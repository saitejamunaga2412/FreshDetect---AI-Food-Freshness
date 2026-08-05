import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split, WeightedRandomSampler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, roc_curve, auc
import time
import copy
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import random

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def plot_metrics(history, save_dir):
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_acc'], label='Train Acc')
    plt.plot(history['val_acc'], label='Val Acc')
    plt.title('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Loss')
    plt.legend()
    plt.savefig(os.path.join(save_dir, 'accuracy_loss.png'))
    plt.close()

def plot_confusion_matrix(cm, classes, save_dir):
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True')
    plt.xlabel('Predicted')
    plt.savefig(os.path.join(save_dir, 'confusion_matrix.png'))
    plt.close()

def plot_roc_curve(y_true, y_prob, save_dir):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    plt.savefig(os.path.join(save_dir, 'roc_curve.png'))
    plt.close()

def export_onnx(model, save_path, device):
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    torch.onnx.export(model, dummy_input, save_path, export_params=True, 
                      opset_version=11, do_constant_folding=True, 
                      input_names=['input'], output_names=['output'], 
                      dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
    print(f"ONNX model exported to {save_path}")

def train_model(resume=False):
    print("Starting Production Training Pipeline...")
    set_seed(42)
    
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.abspath(os.path.join(base_dir, "../../../dataset/Freshness44"))
    models_dir = os.path.abspath(os.path.join(base_dir, "../models/freshness"))
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Dataset & Preprocessing
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    full_dataset = datasets.ImageFolder(data_dir, transform=train_transform)
    class_names = full_dataset.classes
    print(f"Original classes found: {len(class_names)}")
    
    total_samples = len(full_dataset)
    print(f"Total original images: {total_samples}")
    
    # Proper 70/15/15 Split
    train_size = int(0.7 * total_samples)
    val_size = int(0.15 * total_samples)
    test_size = total_samples - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = random_split(full_dataset, [train_size, val_size, test_size])
    
    val_dataset.dataset = copy.copy(full_dataset)
    val_dataset.dataset.transform = test_transform
    test_dataset.dataset = copy.copy(full_dataset)
    test_dataset.dataset.transform = test_transform
    
    # Map multiple folder classes to 'Fresh' and 'Rotten' for weighted loss
    target_mapping = {}
    fresh_count = 0
    rotten_count = 0
    for i, c in enumerate(class_names):
        if "fresh" in c.lower():
            target_mapping[i] = 0
            fresh_count += full_dataset.targets.count(i)
        elif "rotten" in c.lower():
            target_mapping[i] = 1
            rotten_count += full_dataset.targets.count(i)
            
    # Calculate class weights for weighted cross entropy
    total = fresh_count + rotten_count
    weight_fresh = total / (2 * fresh_count) if fresh_count > 0 else 1.0
    weight_rotten = total / (2 * rotten_count) if rotten_count > 0 else 1.0
    class_weights = torch.FloatTensor([weight_fresh, weight_rotten])
    
    # Custom transform to map targets
    def target_transform(target):
        return target_mapping.get(target, 0)
    full_dataset.target_transform = target_transform
    
    # Determine batch size and workers
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    batch_size = 64 if torch.cuda.is_available() else 32
    num_workers = 4 if torch.cuda.is_available() else 0
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    
    # 2. Model Initialization
    print(f"Initializing MobileNetV3-Large... (Device: {device})")
    model = models.mobilenet_v3_large(pretrained=True)
    
    for param in model.parameters():
        param.requires_grad = False
    
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, 2)
    model = model.to(device)
    class_weights = class_weights.to(device)
    
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3)
    scaler = GradScaler(enabled=torch.cuda.is_available())
    
    num_epochs = 30
    best_val_acc = 0.0
    patience = 8
    patience_counter = 0
    start_epoch = 0
    history = {'train_acc': [], 'val_acc': [], 'train_loss': [], 'val_loss': []}
    
    # Resume
    last_model_path = os.path.join(models_dir, 'last_model.pth')
    if resume and os.path.exists(last_model_path):
        checkpoint = torch.load(last_model_path)
        model.load_state_dict(checkpoint['model_state'])
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        start_epoch = checkpoint['epoch']
        best_val_acc = checkpoint['best_val_acc']
        history = checkpoint['history']
        print(f"Resumed from epoch {start_epoch}")
    
    # 3. Training Loop
    start_time = time.time()
    for epoch in range(start_epoch, num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        model.train()
        running_loss = 0.0
        corrects = 0
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            
            with autocast(enabled=torch.cuda.is_available()):
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            _, preds = torch.max(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            corrects += torch.sum(preds == labels.data)
            
            if i % 100 == 0:
                print(f"  Batch {i}/{len(train_loader)} Loss: {loss.item():.4f}")
                
        epoch_loss = running_loss / train_size
        epoch_acc = corrects.double() / train_size
        history['train_loss'].append(epoch_loss)
        history['train_acc'].append(epoch_acc.item())
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_corrects = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                with autocast(enabled=torch.cuda.is_available()):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                _, preds = torch.max(outputs, 1)
                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data)
                
        val_epoch_loss = val_loss / val_size
        val_epoch_acc = val_corrects.double() / val_size
        history['val_loss'].append(val_epoch_loss)
        history['val_acc'].append(val_epoch_acc.item())
        
        print(f"  Val Loss: {val_epoch_loss:.4f} | Val Acc: {val_epoch_acc:.4f}")
        scheduler.step(val_epoch_acc)
        
        # Save Last Checkpoint
        torch.save({
            'epoch': epoch + 1,
            'model_state': model.state_dict(),
            'optimizer_state': optimizer.state_dict(),
            'best_val_acc': best_val_acc,
            'history': history
        }, last_model_path)
        
        if val_epoch_acc > best_val_acc:
            best_val_acc = val_epoch_acc
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(models_dir, 'best_model.pth'))
            print("  [Saved Best Model]")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered.")
                break
                
    time_elapsed = time.time() - start_time
    print(f"Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
    
    # 4. Evaluation
    print("Evaluating on Test Set...")
    model.load_state_dict(torch.load(os.path.join(models_dir, 'best_model.pth')))
    model.eval()
    
    all_preds = []
    all_targets = []
    all_probs = []
    
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)[:, 1]
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
    # Metrics
    metrics = {
        "accuracy": accuracy_score(all_targets, all_preds),
        "precision": precision_score(all_targets, all_preds, zero_division=0),
        "recall": recall_score(all_targets, all_preds, zero_division=0),
        "f1": f1_score(all_targets, all_preds, zero_division=0)
    }
    
    try:
        cr = classification_report(all_targets, all_preds, target_names=["Fresh", "Rotten"], output_dict=True)
    except:
        cr = classification_report(all_targets, all_preds, labels=[0, 1], target_names=["Fresh", "Rotten"], output_dict=True)
        
    cm = confusion_matrix(all_targets, all_preds, labels=[0, 1])
    
    # Save artifacts
    with open(os.path.join(models_dir, 'training_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4)
        
    with open(os.path.join(models_dir, 'classification_report.json'), 'w') as f:
        json.dump(cr, f, indent=4)
        
    with open(os.path.join(models_dir, 'class_names.json'), 'w') as f:
        json.dump({"0": "Fresh", "1": "Rotten"}, f, indent=4)
        
    plot_metrics(history, models_dir)
    plot_confusion_matrix(cm, ["Fresh", "Rotten"], models_dir)
    
    try:
        plot_roc_curve(all_targets, all_probs, models_dir)
    except:
        print("Could not generate ROC curve.")
        
    export_onnx(model, os.path.join(models_dir, 'freshness_classifier.onnx'), device)
    
    # Final copy for the backend
    import shutil
    shutil.copy(os.path.join(models_dir, 'best_model.pth'), os.path.join(models_dir, 'freshness_classifier.pth'))
    
    print("\n✅ Production Training Completed & Artifacts Exported Successfully!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()
    train_model(resume=args.resume)
