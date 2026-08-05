import os
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def main():
    # ---------------------------------------------------------
    # 1. Dataset Loading & Preprocessing
    # ---------------------------------------------------------
    print("Loading dataset...")
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    dataset_path = base_dir / "dataset" / "processed" / "mendeley_final.csv"
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {dataset_path}")

    df = pd.read_csv(dataset_path)
    
    # Check structure
    # Columns: fruit,temp,humid_(%),light_(fux),co2_(pmm),class
    print(f"Dataset Shape: {df.shape}")
    
    # Drop rows with missing values just in case
    df = df.dropna()

    # Features: Environmental variables only
    X = df[['temp', 'humid_(%)', 'light_(fux)', 'co2_(pmm)']]
    y = df['class']

    # Label encode target ('Good', 'Bad' usually)
    print("Encoding target labels...")
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split Dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Scale Features
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---------------------------------------------------------
    # 2. Model Comparison
    # ---------------------------------------------------------
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42),
        "SVM": SVC(probability=True, random_state=42),
        "KNN": KNeighborsClassifier()
    }

    print("\nStarting Model Comparison...")
    best_model_name = ""
    best_score = 0
    results = {}

    for name, model in models.items():
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        mean_cv_score = cv_scores.mean()
        
        # Train & Predict on test set
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        results[name] = {
            "CV_Accuracy": mean_cv_score,
            "Test_Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1_Score": f1,
            "Model": model
        }
        
        print(f"[{name}] CV Acc: {mean_cv_score:.4f} | Test Acc: {acc:.4f} | F1: {f1:.4f}")
        
        if acc > best_score:
            best_score = acc
            best_model_name = name

    print(f"\n=> Best Model Selected: {best_model_name} (Test Acc: {best_score:.4f})")

    # ---------------------------------------------------------
    # 3. Hyperparameter Tuning (Random Forest Example)
    # ---------------------------------------------------------
    print("\nStarting Hyperparameter Tuning...")
    final_model = None
    if best_model_name == "Random Forest":
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        }
        grid = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=3, n_jobs=-1, scoring='accuracy')
        grid.fit(X_train_scaled, y_train)
        print(f"Best params: {grid.best_params_}")
        final_model = grid.best_estimator_
    elif best_model_name == "SVM":
        param_grid = {'C': [0.1, 1, 10], 'kernel': ['linear', 'rbf']}
        grid = GridSearchCV(SVC(probability=True, random_state=42), param_grid, cv=3, n_jobs=-1, scoring='accuracy')
        grid.fit(X_train_scaled, y_train)
        print(f"Best params: {grid.best_params_}")
        final_model = grid.best_estimator_
    else:
        # Fallback to base if neither RF or SVM
        final_model = models[best_model_name]
        final_model.fit(X_train_scaled, y_train)

    # ---------------------------------------------------------
    # 4. Final Training & Artifact Export
    # ---------------------------------------------------------
    # Retrain on full dataset for maximum performance
    print("Retraining final optimized model on FULL dataset...")
    X_full_scaled = scaler.fit_transform(X)
    final_model.fit(X_full_scaled, y_encoded)
    
    # Evaluate final
    full_pred = final_model.predict(X_full_scaled)
    print("Final Model Confusion Matrix:")
    print(confusion_matrix(y_encoded, full_pred))
    
    # Save Artifacts
    models_dir = base_dir / "weights"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "freshness_model.pkl"
    scaler_path = models_dir / "scaler.pkl"
    encoder_path = models_dir / "class_encoder.pkl"
    
    joblib.dump(final_model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(label_encoder, encoder_path)
    
    print("\n✅ Artifacts Exported Successfully!")
    print(f"- Model: {model_path}")
    print(f"- Scaler: {scaler_path}")
    print(f"- Encoder: {encoder_path}")

if __name__ == "__main__":
    main()
