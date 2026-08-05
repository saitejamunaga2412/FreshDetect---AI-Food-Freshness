import os
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

def main():
    print("Loading dataset...")
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    dataset_path = base_dir / "dataset" / "processed" / "mendeley_final.csv"
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {dataset_path}")

    df = pd.read_csv(dataset_path)
    print(f"Dataset Shape: {df.shape}")
    df = df.dropna()

    # We only use production features: fruit, temp, humid
    # The dataset columns: fruit,temp,humid_(%),light_(fux),co2_(pmm),class
    X = df[['fruit', 'temp', 'humid_(%)']]
    y = df['class']

    # Explicitly map Good=1, Bad=0
    print("Mapping target labels explicitly (Good=1, Bad=0)...")
    y_encoded = y.map({'Good': 1, 'Bad': 0})
    if y_encoded.isnull().any():
        print("Warning: some classes were not Good or Bad. Dropping them.")
        valid_idx = y_encoded.notnull()
        X = X[valid_idx]
        y_encoded = y_encoded[valid_idx]

    y_encoded = y_encoded.astype(int)

    # Encode 'fruit' feature
    print("Encoding 'fruit' feature...")
    fruit_encoder = LabelEncoder()
    X_encoded = X.copy()
    X_encoded['fruit'] = fruit_encoder.fit_transform(X['fruit'])

    # Split Dataset
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y_encoded, test_size=0.2, random_state=42)

    # Scale Features (temp, humid only)
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    
    scale_cols = ['temp', 'humid_(%)']
    X_train_scaled[scale_cols] = scaler.fit_transform(X_train[scale_cols])
    X_test_scaled[scale_cols] = scaler.transform(X_test[scale_cols])

    # Model Comparison
    models = {
        "Random Forest": RandomForestClassifier(random_state=42)
    }
    if XGBClassifier is not None:
        models["XGBoost"] = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    else:
        print("XGBoost not installed. Skipping.")

    print("\nStarting Model Comparison...")
    best_model_name = ""
    best_score = 0
    best_model = None
    
    for name, model in models.items():
        # Train & Predict
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_prob)
        
        print(f"[{name}] Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | ROC-AUC: {roc_auc:.4f}")
        
        if acc > best_score:
            best_score = acc
            best_model_name = name
            best_model = model

    print(f"\n=> Best Model Selected: {best_model_name} (Test Acc: {best_score:.4f})")
    
    print("\nFinal Model Confusion Matrix:")
    y_pred_best = best_model.predict(X_test_scaled)
    print(confusion_matrix(y_test, y_pred_best))

    # Retrain on full dataset
    print("Retraining best model on FULL dataset...")
    X_full_scaled = X_encoded.copy()
    X_full_scaled[scale_cols] = scaler.fit_transform(X_encoded[scale_cols])
    best_model.fit(X_full_scaled, y_encoded)

    # Save Artifacts
    models_dir = base_dir / "weights"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "freshness_model.pkl"
    scaler_path = models_dir / "scaler.pkl"
    encoder_path = models_dir / "fruit_encoder.pkl"
    
    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(fruit_encoder, encoder_path)
    
    print("\n✅ Artifacts Exported Successfully!")
    print(f"- Model: {model_path}")
    print(f"- Scaler: {scaler_path}")
    print(f"- Fruit Encoder: {encoder_path}")

if __name__ == "__main__":
    main()
