"""
train_freshness.py

Production-ready training pipeline for the FreshDetect Freshness
Classifier (Fresh vs. Rotten, per fruit/vegetable) built on an
EfficientNet-B0 backbone via `timm`.

This script is fully self-contained: dataset loading, model
definition, training / validation / test loops, metric computation,
early stopping, LR scheduling, checkpointing with resume support and
result visualisation are all included here, as required by the
FreshDetect project.

Additional production features in this version:
    - Weighted CrossEntropyLoss to handle class imbalance
    - Automatic Mixed Precision (AMP) training for GPU speedups
    - Gradient clipping to guard against exploding gradients
    - TensorBoard logging for live monitoring
    - ONNX export of the best model for deployment

Usage:
    python models/train_freshness.py

Author: FreshDetect Team
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image

# torch.cuda.amp.{autocast,GradScaler} are deprecated in favour of the
# device-agnostic torch.amp API (PyTorch >= 2.0). Fall back gracefully
# for older PyTorch installs that don't expose torch.amp yet.
try:
    from torch.amp import GradScaler, autocast

    _NEW_AMP_API = True
except ImportError:  # pragma: no cover - older torch
    from torch.cuda.amp import GradScaler, autocast

    _NEW_AMP_API = False

from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

try:
    from torch.utils.tensorboard import SummaryWriter

    _TENSORBOARD_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    SummaryWriter = None  # type: ignore[assignment,misc]
    _TENSORBOARD_AVAILABLE = False

try:
    import timm
except ImportError as exc:
    raise ImportError(
        "The 'timm' package is required. Install it with `pip install timm`."
    ) from exc

try:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )
except ImportError as exc:
    raise ImportError(
        "The 'scikit-learn' package is required. Install it with "
        "`pip install scikit-learn`."
    ) from exc

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

try:
    from rich.logging import RichHandler

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


# --------------------------------------------------------------------------- #
# AMP helpers (future-proof wrapper around torch.amp / torch.cuda.amp)
# --------------------------------------------------------------------------- #
def amp_autocast(device_type: str, enabled: bool):
    """Return an autocast context manager using the modern torch.amp API
    when available, falling back to torch.cuda.amp on older PyTorch."""
    if _NEW_AMP_API:
        return autocast(device_type=device_type, enabled=enabled)
    return autocast(enabled=enabled)  # legacy torch.cuda.amp.autocast


def make_grad_scaler(device_type: str, enabled: bool) -> GradScaler:
    """Instantiate a GradScaler using the modern torch.amp API when
    available, falling back to torch.cuda.amp on older PyTorch."""
    if _NEW_AMP_API:
        return GradScaler(device_type, enabled=enabled)
    return GradScaler(enabled=enabled)  # legacy torch.cuda.amp.GradScaler


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    """Central configuration for the training pipeline."""

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent
    dataset_dir: Path = field(init=False)
    train_dir: Path = field(init=False)
    valid_dir: Path = field(init=False)
    test_dir: Path = field(init=False)
    weights_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    plots_dir: Path = field(init=False)
    tensorboard_dir: Path = field(init=False)

    # Model
    model_name: str = "efficientnet_b0"
    image_size: int = 224
    pretrained: bool = True

    # Training
    batch_size: int = 32
    num_epochs: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    # min(4, cpu_count) keeps this safe on machines with few cores and
    # avoids the multiprocessing DataLoader worker issues that show up
    # on some Windows setups when num_workers is hardcoded too high.
    # Set to 0 explicitly if you still hit DataLoader worker errors
    # during local development on Windows.
    num_workers: int = field(default_factory=lambda: min(4, os.cpu_count() or 1))
    seed: int = 42

    # Early stopping
    early_stopping_patience: int = 7
    early_stopping_min_delta: float = 1e-4

    # LR scheduler
    lr_scheduler_factor: float = 0.5
    lr_scheduler_patience: int = 3
    lr_scheduler_min_lr: float = 1e-7

    # Class imbalance handling
    use_weighted_loss: bool = True

    # Mixed precision training
    use_amp: bool = True

    # Gradient clipping (set to None to disable)
    grad_clip_norm: Optional[float] = 1.0

    # TensorBoard
    use_tensorboard: bool = True

    # ONNX export
    export_onnx: bool = True
    onnx_export_name: str = "freshness_classifier.onnx"
    onnx_opset_version: int = 17

    # Checkpointing
    checkpoint_name: str = "freshness_classifier.pth"
    last_checkpoint_name: str = "last_checkpoint.pth"
    class_names_file: str = "class_names.json"
    history_file: str = "training_history.json"

    # Resume
    resume: bool = True

    def __post_init__(self) -> None:
        self.dataset_dir = self.project_root / "dataset" / "SplitDataset"
        self.train_dir = self.dataset_dir / "train"
        self.valid_dir = self.dataset_dir / "valid"
        self.test_dir = self.dataset_dir / "test"
        self.weights_dir = self.project_root / "models" / "weights"
        self.logs_dir = self.project_root / "models" / "logs"
        self.plots_dir = self.project_root / "models" / "plots"
        self.tensorboard_dir = self.project_root / "models" / "tensorboard"


CONFIG = Config()


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def setup_logging(logs_dir: Path) -> logging.Logger:
    """Configure rich (if available) + file logging."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"train_{time.strftime('%Y%m%d_%H%M%S')}.log"

    handlers: List[logging.Handler] = []
    if _RICH_AVAILABLE:
        handlers.append(RichHandler(rich_tracebacks=True, show_path=False))
    else:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
        )
        handlers.append(stream_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )
    handlers.append(file_handler)

    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)
    return logging.getLogger("freshness_trainer")


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #
def set_seed(seed: int) -> None:
    """Fix all relevant random seeds for reproducible runs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# --------------------------------------------------------------------------- #
# Dataset
# --------------------------------------------------------------------------- #
class FreshnessDataset(Dataset):
    """
    Custom dataset that walks a two-level directory structure of the
    form::

        root/
            <fruit_or_vegetable>/
                fresh/
                    *.jpg
                rotten/
                    *.jpg

    The fruit/vegetable identity (apple, banana, tomato, ...) is
    intentionally discarded here: that information is already
    produced upstream by the YOLO detector in the FreshDetect
    pipeline (Image -> YOLO -> "Banana" -> this model -> "Fresh").
    This dataset therefore collapses every item folder into a single
    shared binary label space::

        fresh  = 0
        rotten = 1

    regardless of which fruit/vegetable sub-folder the image came
    from, producing a 2-class (not 28-class) classifier.
    """

    VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    VALID_CONDITIONS = ("fresh", "rotten")

    def __init__(
        self,
        root_dir: Path,
        class_to_idx: Optional[Dict[str, int]] = None,
        transform: Optional[transforms.Compose] = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []

        if not self.root_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.root_dir}")

        if class_to_idx is None:
            self.class_to_idx = {"fresh": 0, "rotten": 1}
        else:
            self.class_to_idx = class_to_idx

        self.idx_to_class = {idx: name for name, idx in self.class_to_idx.items()}
        self.classes = [
            name
            for name, _ in sorted(self.class_to_idx.items(), key=lambda kv: kv[1])
        ]

        self._build_samples()

        if len(self.samples) == 0:
            raise RuntimeError(
                f"No valid images were found under '{self.root_dir}'. "
                "Please verify the dataset structure."
            )

    def _build_samples(self) -> None:
        """
        Walk every <fruit_or_vegetable>/<fresh|rotten>/ folder and map
        each image to the shared binary label (fresh=0, rotten=1),
        discarding the fruit/vegetable identity entirely.
        """
        for item_dir in sorted(self.root_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            for condition_dir in sorted(item_dir.iterdir()):
                if not condition_dir.is_dir():
                    continue
                condition = condition_dir.name.lower()
                if condition not in self.VALID_CONDITIONS:
                    continue
                if condition not in self.class_to_idx:
                    continue
                label_idx = self.class_to_idx[condition]
                for file_path in sorted(condition_dir.iterdir()):
                    if file_path.suffix.lower() in self.VALID_EXTENSIONS:
                        self.samples.append((file_path, label_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        file_path, label = self.samples[index]
        try:
            image = Image.open(file_path).convert("RGB")
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Failed to load image '{file_path}': {exc}") from exc

        if self.transform is not None:
            image = self.transform(image)

        return image, label


# --------------------------------------------------------------------------- #
# Class imbalance handling
# --------------------------------------------------------------------------- #
def compute_class_weights(
    dataset: FreshnessDataset,
    num_classes: int,
    device: torch.device,
    logger: Optional[logging.Logger] = None,
) -> torch.Tensor:
    """
    Compute inverse-frequency class weights for CrossEntropyLoss so that
    minority classes (e.g. a fruit with very few 'rotten' samples) are
    not drowned out by majority classes during training.

    weight[c] = total_samples / (num_classes * count[c])

    A class with fewer samples receives a proportionally larger weight,
    which increases its contribution to the loss and gradient.
    """
    counts = Counter(label for _, label in dataset.samples)
    total = sum(counts.values())

    weights: List[float] = []
    for idx in range(num_classes):
        count = counts.get(idx, 0)
        if count == 0:
            weights.append(0.0)
        else:
            weights.append(total / (num_classes * count))

    weights_tensor = torch.tensor(weights, dtype=torch.float32, device=device)

    if logger is not None:
        class_names = dataset.classes
        for idx, name in enumerate(class_names):
            logger.info(
                "Class '%s' (idx=%d): count=%d, weight=%.4f",
                name,
                idx,
                counts.get(idx, 0),
                weights_tensor[idx].item(),
            )

    return weights_tensor


# --------------------------------------------------------------------------- #
# Transforms
# --------------------------------------------------------------------------- #
def build_transforms(image_size: int) -> Tuple[transforms.Compose, transforms.Compose]:
    """Create the training (augmented) and evaluation (deterministic) transforms."""
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    train_transform = transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.1),
            transforms.RandomRotation(degrees=20),
            transforms.ColorJitter(
                brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05
            ),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
            transforms.ToTensor(),
            transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
            transforms.RandomErasing(p=0.2),
        ]
    )

    eval_transform = transforms.Compose(
        [
            transforms.Resize(int(image_size * 1.14)),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
        ]
    )

    return train_transform, eval_transform


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
def build_model(
    model_name: str, num_classes: int, pretrained: bool, device: torch.device
) -> nn.Module:
    """Instantiate an EfficientNet-B0 classifier via timm."""
    model = timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)
    model.to(device)
    return model


# --------------------------------------------------------------------------- #
# Early Stopping
# --------------------------------------------------------------------------- #
class EarlyStopping:
    """Stops training once the monitored validation loss stops improving."""

    def __init__(self, patience: int = 7, min_delta: float = 1e-4) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score: Optional[float] = None
        self.should_stop = False

    def step(self, val_loss: float) -> bool:
        if self.best_score is None or val_loss < self.best_score - self.min_delta:
            self.best_score = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
        return self.should_stop


# --------------------------------------------------------------------------- #
# Train / Validate / Test loops
# --------------------------------------------------------------------------- #
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
    num_epochs: int,
    scaler: Optional[GradScaler] = None,
    grad_clip_norm: Optional[float] = None,
    writer: Optional[SummaryWriter] = None,
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    all_preds: List[int] = []
    all_labels: List[int] = []
    use_amp = scaler is not None

    progress_bar = tqdm(loader, desc=f"Epoch {epoch}/{num_epochs} [Train]", leave=False)
    for step, (images, labels) in enumerate(progress_bar):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        if use_amp:
            with amp_autocast(device.type, enabled=True):
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            if grad_clip_norm is not None:
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip_norm)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            if grad_clip_norm is not None:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip_norm)
            optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.detach().cpu().numpy().tolist())
        all_labels.extend(labels.detach().cpu().numpy().tolist())

        progress_bar.set_postfix(loss=f"{loss.item():.4f}")

        if writer is not None:
            global_step = (epoch - 1) * len(loader) + step
            writer.add_scalar("Batch/train_loss", loss.item(), global_step)

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc


@torch.no_grad()
def validate_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    epoch: int,
    num_epochs: int,
    phase: str = "Val",
    use_amp: bool = False,
) -> Tuple[float, float, List[int], List[int]]:
    model.eval()
    running_loss = 0.0
    all_preds: List[int] = []
    all_labels: List[int] = []

    progress_bar = tqdm(loader, desc=f"Epoch {epoch}/{num_epochs} [{phase}]", leave=False)
    for images, labels in progress_bar:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with amp_autocast(device.type, enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.cpu().numpy().tolist())
        all_labels.extend(labels.cpu().numpy().tolist())

        progress_bar.set_postfix(loss=f"{loss.item():.4f}")

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc, all_labels, all_preds


@torch.no_grad()
def evaluate_test_set(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    class_names: List[str],
    logger: logging.Logger,
    use_amp: bool = False,
) -> Tuple[Dict[str, float], np.ndarray]:
    model.eval()
    running_loss = 0.0
    all_preds: List[int] = []
    all_labels: List[int] = []

    for images, labels in tqdm(loader, desc="Test Evaluation", leave=False):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with amp_autocast(device.type, enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, labels)
        running_loss += loss.item() * images.size(0)

        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.cpu().numpy().tolist())
        all_labels.extend(labels.cpu().numpy().tolist())

    test_loss = running_loss / len(loader.dataset)
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average="weighted", zero_division=0)
    recall = recall_score(all_labels, all_preds, average="weighted", zero_division=0)
    f1 = f1_score(all_labels, all_preds, average="weighted", zero_division=0)
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(len(class_names))))

    logger.info("Test Loss:      %.4f", test_loss)
    logger.info("Test Accuracy:  %.4f", accuracy)
    logger.info("Test Precision: %.4f", precision)
    logger.info("Test Recall:    %.4f", recall)
    logger.info("Test F1 Score:  %.4f", f1)

    metrics = {
        "test_loss": test_loss,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }
    return metrics, cm


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_training_history(history: Dict[str, List[float]], plots_dir: Path) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    epochs_range = range(1, len(history["train_loss"]) + 1)

    plt.figure(figsize=(8, 6))
    plt.plot(epochs_range, history["train_loss"], label="Train Loss")
    plt.plot(epochs_range, history["val_loss"], label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training vs Validation Loss")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "loss.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    plt.plot(epochs_range, history["train_acc"], label="Train Accuracy")
    plt.plot(epochs_range, history["val_acc"], label="Validation Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Training vs Validation Accuracy")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "accuracy.png", dpi=150)
    plt.close()


def plot_confusion_matrix(cm: np.ndarray, class_names: List[str], plots_dir: Path) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    size = max(8, len(class_names) * 0.5)
    plt.figure(figsize=(size, size))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(plots_dir / "confusion_matrix.png", dpi=150)
    plt.close()


# --------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------- #
def save_checkpoint(state: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, path)


def load_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: optim.Optimizer,
    scheduler,
    device: torch.device,
    scaler: Optional[GradScaler] = None,
) -> Tuple[int, float, Dict[str, List[float]]]:
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    if scheduler is not None and "scheduler_state_dict" in checkpoint:
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    if scaler is not None and "scaler_state_dict" in checkpoint and checkpoint["scaler_state_dict"] is not None:
        scaler.load_state_dict(checkpoint["scaler_state_dict"])
    start_epoch = checkpoint.get("epoch", 0) + 1
    best_val_loss = checkpoint.get("best_val_loss", float("inf"))
    history = checkpoint.get(
        "history", {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    )
    return start_epoch, best_val_loss, history


# --------------------------------------------------------------------------- #
# ONNX Export
# --------------------------------------------------------------------------- #
def export_to_onnx(
    model: nn.Module,
    image_size: int,
    device: torch.device,
    export_path: Path,
    opset_version: int,
    logger: logging.Logger,
) -> None:
    """
    Export the trained model to ONNX format for deployment (e.g. via
    ONNX Runtime, TensorRT, or mobile/edge inference engines) so the
    pipeline is not locked into a raw .pth checkpoint.
    """
    try:
        import onnx  # noqa: F401  (torch.onnx.export needs this installed)
    except ImportError:
        logger.warning(
            "ONNX export requested but the 'onnx' package is not installed. "
            "Install it with `pip install onnx` to enable deployment export. "
            "Skipping ONNX export."
        )
        return

    export_path.parent.mkdir(parents=True, exist_ok=True)
    model.eval()
    dummy_input = torch.randn(1, 3, image_size, image_size, device=device)

    torch.onnx.export(
        model,
        dummy_input,
        str(export_path),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )
    logger.info("Exported ONNX model to %s", export_path)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = CONFIG
    cfg.weights_dir.mkdir(parents=True, exist_ok=True)
    cfg.logs_dir.mkdir(parents=True, exist_ok=True)
    cfg.plots_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logging(cfg.logs_dir)
    set_seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    use_amp = cfg.use_amp and device.type == "cuda"
    if cfg.use_amp and device.type != "cuda":
        logger.warning("AMP requested but no CUDA device found; running in FP32.")

    writer: Optional[SummaryWriter] = None
    if cfg.use_tensorboard and not _TENSORBOARD_AVAILABLE:
        logger.warning(
            "TensorBoard logging requested but the 'tensorboard' package is not "
            "installed. Install it with `pip install tensorboard` to enable live "
            "monitoring. Continuing without TensorBoard."
        )
    elif cfg.use_tensorboard:
        run_dir = cfg.tensorboard_dir / time.strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        writer = SummaryWriter(log_dir=str(run_dir))
        logger.info("TensorBoard logging to %s", run_dir)
        logger.info("Launch with: tensorboard --logdir %s", cfg.tensorboard_dir)

    try:
        train_transform, eval_transform = build_transforms(cfg.image_size)

        logger.info("Loading training dataset from %s", cfg.train_dir)
        train_dataset = FreshnessDataset(cfg.train_dir, transform=train_transform)
        class_to_idx = train_dataset.class_to_idx
        class_names = train_dataset.classes
        num_classes = len(class_names)
        logger.info("Discovered %d classes: %s", num_classes, class_names)

        logger.info("Loading validation dataset from %s", cfg.valid_dir)
        valid_dataset = FreshnessDataset(
            cfg.valid_dir, class_to_idx=class_to_idx, transform=eval_transform
        )

        logger.info("Loading test dataset from %s", cfg.test_dir)
        test_dataset = FreshnessDataset(
            cfg.test_dir, class_to_idx=class_to_idx, transform=eval_transform
        )

        pin_memory = device.type == "cuda"

        train_loader = DataLoader(
            train_dataset,
            batch_size=cfg.batch_size,
            shuffle=True,
            num_workers=cfg.num_workers,
            pin_memory=pin_memory,
            drop_last=True,
        )
        valid_loader = DataLoader(
            valid_dataset,
            batch_size=cfg.batch_size,
            shuffle=False,
            num_workers=cfg.num_workers,
            pin_memory=pin_memory,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=cfg.batch_size,
            shuffle=False,
            num_workers=cfg.num_workers,
            pin_memory=pin_memory,
        )

        logger.info(
            "Train samples: %d | Valid samples: %d | Test samples: %d",
            len(train_dataset),
            len(valid_dataset),
            len(test_dataset),
        )

        model = build_model(cfg.model_name, num_classes, cfg.pretrained, device)

        if cfg.use_weighted_loss:
            logger.info("Computing class weights for imbalanced dataset...")
            class_weights = compute_class_weights(
                train_dataset, num_classes, device, logger=logger
            )
            criterion = nn.CrossEntropyLoss(weight=class_weights)
        else:
            class_weights = None
            criterion = nn.CrossEntropyLoss()

        optimizer = optim.AdamW(
            model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=cfg.lr_scheduler_factor,
            patience=cfg.lr_scheduler_patience,
            min_lr=cfg.lr_scheduler_min_lr,
        )

        scaler: Optional[GradScaler] = (
            make_grad_scaler(device.type, enabled=use_amp) if use_amp else None
        )
        if use_amp:
            logger.info("Mixed precision (AMP) training enabled.")
        if cfg.grad_clip_norm is not None:
            logger.info("Gradient clipping enabled (max_norm=%.2f).", cfg.grad_clip_norm)

        start_epoch = 1
        best_val_loss = float("inf")
        history: Dict[str, List[float]] = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
        }

        last_checkpoint_path = cfg.weights_dir / cfg.last_checkpoint_name
        best_checkpoint_path = cfg.weights_dir / cfg.checkpoint_name

        if cfg.resume and last_checkpoint_path.exists():
            logger.info("Resuming training from checkpoint: %s", last_checkpoint_path)
            start_epoch, best_val_loss, history = load_checkpoint(
                last_checkpoint_path, model, optimizer, scheduler, device, scaler=scaler
            )
            logger.info(
                "Resumed at epoch %d (best_val_loss=%.4f)", start_epoch, best_val_loss
            )

        early_stopping = EarlyStopping(
            patience=cfg.early_stopping_patience, min_delta=cfg.early_stopping_min_delta
        )

        class_names_path = cfg.weights_dir / cfg.class_names_file
        with open(class_names_path, "w", encoding="utf-8") as f:
            json.dump({"classes": class_names, "class_to_idx": class_to_idx}, f, indent=2)
        logger.info("Saved class names to %s", class_names_path)

        logger.info("Starting training for up to %d epochs...", cfg.num_epochs)
        for epoch in range(start_epoch, cfg.num_epochs + 1):
            epoch_start = time.time()

            train_loss, train_acc = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
                epoch,
                cfg.num_epochs,
                scaler=scaler,
                grad_clip_norm=cfg.grad_clip_norm,
                writer=writer,
            )
            val_loss, val_acc, _, _ = validate_one_epoch(
                model,
                valid_loader,
                criterion,
                device,
                epoch,
                cfg.num_epochs,
                phase="Val",
                use_amp=use_amp,
            )

            scheduler.step(val_loss)
            current_lr = optimizer.param_groups[0]["lr"]

            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            epoch_time = time.time() - epoch_start
            logger.info(
                "Epoch %d/%d | Train Loss: %.4f Acc: %.4f | Val Loss: %.4f Acc: %.4f | "
                "LR: %.2e | Time: %.1fs",
                epoch,
                cfg.num_epochs,
                train_loss,
                train_acc,
                val_loss,
                val_acc,
                current_lr,
                epoch_time,
            )

            if writer is not None:
                writer.add_scalar("Loss/train", train_loss, epoch)
                writer.add_scalar("Loss/val", val_loss, epoch)
                writer.add_scalar("Accuracy/train", train_acc, epoch)
                writer.add_scalar("Accuracy/val", val_acc, epoch)
                writer.add_scalar("LR", current_lr, epoch)
                writer.add_scalar("Time/epoch_seconds", epoch_time, epoch)

            checkpoint_state = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "scaler_state_dict": scaler.state_dict() if scaler is not None else None,
                "best_val_loss": best_val_loss,
                "history": history,
                "class_names": class_names,
                "class_to_idx": class_to_idx,
                "config": {
                    "model_name": cfg.model_name,
                    "image_size": cfg.image_size,
                    "num_classes": num_classes,
                },
            }
            save_checkpoint(checkpoint_state, last_checkpoint_path)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                checkpoint_state["best_val_loss"] = best_val_loss
                save_checkpoint(checkpoint_state, best_checkpoint_path)
                logger.info(
                    "New best model saved (val_loss=%.4f) -> %s",
                    best_val_loss,
                    best_checkpoint_path,
                )

            with open(cfg.weights_dir / cfg.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            if early_stopping.step(val_loss):
                logger.info(
                    "Early stopping triggered at epoch %d (patience=%d).",
                    epoch,
                    cfg.early_stopping_patience,
                )
                break

        plot_training_history(history, cfg.plots_dir)
        logger.info("Saved training curves to %s", cfg.plots_dir)

        logger.info("Loading best model for final test evaluation...")
        best_checkpoint = torch.load(best_checkpoint_path, map_location=device)
        model.load_state_dict(best_checkpoint["model_state_dict"])

        test_metrics, cm = evaluate_test_set(
            model, test_loader, criterion, device, class_names, logger, use_amp=use_amp
        )
        plot_confusion_matrix(cm, class_names, cfg.plots_dir)

        with open(cfg.weights_dir / "test_metrics.json", "w", encoding="utf-8") as f:
            json.dump(test_metrics, f, indent=2)

        if writer is not None:
            writer.add_scalar("Test/loss", test_metrics["test_loss"], 0)
            writer.add_scalar("Test/accuracy", test_metrics["accuracy"], 0)
            writer.add_scalar("Test/precision", test_metrics["precision"], 0)
            writer.add_scalar("Test/recall", test_metrics["recall"], 0)
            writer.add_scalar("Test/f1_score", test_metrics["f1_score"], 0)

        if cfg.export_onnx:
            onnx_path = cfg.weights_dir / cfg.onnx_export_name
            export_to_onnx(
                model,
                cfg.image_size,
                device,
                onnx_path,
                cfg.onnx_opset_version,
                logger,
            )

        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info("Best Validation Loss: %.4f", best_val_loss)
        logger.info("Test Accuracy:  %.4f", test_metrics["accuracy"])
        logger.info("Test Precision: %.4f", test_metrics["precision"])
        logger.info("Test Recall:    %.4f", test_metrics["recall"])
        logger.info("Test F1 Score:  %.4f", test_metrics["f1_score"])
        logger.info("Best model saved at: %s", best_checkpoint_path)
        if cfg.export_onnx:
            logger.info("ONNX model saved at: %s", cfg.weights_dir / cfg.onnx_export_name)
        logger.info("=" * 60)

    except Exception as exc:  # pragma: no cover - top-level safety net
        logging.getLogger("freshness_trainer").exception("Training failed: %s", exc)
        sys.exit(1)
    finally:
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    main()