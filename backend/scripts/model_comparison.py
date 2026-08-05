import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Scikit-Learn Imports
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

# Optional Model Imports
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

def compare_models():
    """
    Evaluates multiple machine learning models using the predefined train/test split.
    Calculates key classification metrics, generates confusion matrices, and ranks 
    the models based on their F1-Score and ROC-AUC.
    """
    # 1 & 2. File paths
    train_path = 'dataset/SplitDataset/train.csv'
    test_path = 'dataset/SplitDataset/test.csv'
    config_path = 'models/preprocessing_config.json'
    
    results_dir = 'results/'
    cm_dir = os.path.join(results_dir, 'confusion_matrices')
    
    csv_report_path = os.path.join(results_dir, 'model_comparison.csv')
    txt_report_path = os.path.join(results_dir, 'model_comparison_report.txt')
    plot_path = os.path.join(results_dir, 'model_comparison.png')
    
    try:
        # Step 1: Load train and test data
        if not os.path.exists(train_path) or not os.path.exists(test_path):
            raise FileNotFoundError("Train or test dataset is missing in 'dataset/SplitDataset/'.")
            
        print("Loading datasets...")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # Step 2: Read preprocessing configuration
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file missing at {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        feature_cols = config.get('feature_columns')
        target_col = config.get('target_column')
        
        if not feature_cols or not target_col:
            raise ValueError("Feature columns or target column missing in preprocessing config.")
            
        # Isolate features (X) and target (y)
        X_train, y_train = train_df[feature_cols], train_df[target_col]
        X_test, y_test = test_df[feature_cols], test_df[target_col]
        
        # Ensure output directories exist
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(cm_dir, exist_ok=True)
        
        # Step 3: Define models (No hyperparameter tuning, using defaults/random_state)
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Random Forest': RandomForestClassifier(random_state=42),
            'SVM': SVC(probability=True, random_state=42),
            'KNN': KNeighborsClassifier()
        }
        
        # Add optional models if installed
        if HAS_XGB:
            models['XGBoost'] = XGBClassifier(eval_metric='logloss', random_state=42)
        if HAS_LGBM:
            models['LightGBM'] = LGBMClassifier(random_state=42)
        if HAS_CATBOOST:
            models['CatBoost'] = CatBoostClassifier(verbose=0, random_state=42)
            
        print(f"\nModels to evaluate: {list(models.keys())}\n")
        
        results = []
        
        # Determine classification type (Binary vs Multiclass)
        num_classes = y_train.nunique()
        is_binary = (num_classes == 2)
        avg_method = 'binary' if is_binary else 'weighted'
        
        # Step 4: Evaluate each model
        for name, model in models.items():
            print(f"Training and evaluating {name}...")
            
            # --- Training Time ---
            start_train = time.time()
            model.fit(X_train, y_train)
            train_time = time.time() - start_train
            
            # --- Prediction Time ---
            start_pred = time.time()
            y_pred = model.predict(X_test)
            pred_time = time.time() - start_pred
            
            # Extract Probabilities for ROC-AUC
            y_prob = None
            if hasattr(model, "predict_proba"):
                try:
                    probs = model.predict_proba(X_test)
                    if is_binary:
                        y_prob = probs[:, 1]
                    else:
                        y_prob = probs
                except Exception:
                    pass
            
            # --- Calculate Metrics ---
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average=avg_method, zero_division=0)
            rec = recall_score(y_test, y_pred, average=avg_method, zero_division=0)
            f1 = f1_score(y_test, y_pred, average=avg_method, zero_division=0)
            
            roc_auc = np.nan
            if y_prob is not None:
                if is_binary:
                    roc_auc = roc_auc_score(y_test, y_prob)
                else:
                    roc_auc = roc_auc_score(y_test, y_prob, multi_class='ovr')
            
            # Append results to list
            results.append({
                'Model': name,
                'Accuracy': acc,
                'Precision': prec,
                'Recall': rec,
                'F1-Score': f1,
                'ROC-AUC': roc_auc,
                'Training_Time(s)': train_time,
                'Prediction_Time(s)': pred_time
            })
            
            # Step 6: Save one confusion matrix image per model
            cm = confusion_matrix(y_test, y_pred)
            plt.figure(figsize=(6, 5))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title(f'Confusion Matrix: {name}')
            plt.ylabel('Actual Label')
            plt.xlabel('Predicted Label')
            plt.tight_layout()
            plt.savefig(os.path.join(cm_dir, f"{name.replace(' ', '_')}_cm.png"))
            plt.close()
            
        # Create DataFrame from results
        results_df = pd.DataFrame(results)
        
        # Step 8: Rank the models
        # Hierarchy: 1) F1-Score, 2) ROC-AUC, 3) Accuracy (Tiebreaker)
        results_df = results_df.sort_values(
            by=['F1-Score', 'ROC-AUC', 'Accuracy'], 
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        # Step 5: Save results CSV
        results_df.to_csv(csv_report_path, index=False)
        
        # Extract Best Model details
        best_model_name = results_df.loc[0, 'Model']
        best_f1 = results_df.loc[0, 'F1-Score']
        
        # Generate Text Report
        report_lines = []
        report_lines.append("="*60)
        report_lines.append("=== Model Comparison Report ===")
        report_lines.append("="*60 + "\n")
        report_lines.append("Ranking Criteria: 1) F1-Score, 2) ROC-AUC, 3) Accuracy (Tiebreaker)\n")
        
        report_lines.append("--- Detailed Results ---")
        report_lines.append(results_df.to_string(index=False))
        
        report_lines.append("\n" + "="*60)
        report_lines.append(f"BEST MODEL: {best_model_name} (F1-Score: {best_f1:.4f})")
        report_lines.append("="*60 + "\n")
        
        with open(txt_report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
            
        # Step 7: Generate a comparison bar chart
        plt.figure(figsize=(12, 6))
        # Reshape data for seaborn barplot
        plot_df = results_df.melt(id_vars='Model', value_vars=['Accuracy', 'F1-Score', 'ROC-AUC'], 
                                  var_name='Metric', value_name='Score')
        
        sns.barplot(data=plot_df, x='Model', y='Score', hue='Metric', palette='viridis')
        plt.title('Model Performance Comparison')
        plt.ylim(0, 1.1)
        plt.xticks(rotation=45)
        plt.legend(loc='lower right')
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()
        
        # Step 9: Print the best model and outputs
        print("\n" + "="*50)
        print("Model Comparison Complete!")
        print("="*50)
        print(f"🥇 BEST MODEL: {best_model_name}")
        print(f"   F1-Score: {best_f1:.4f}")
        print("="*50)
        print(f"Results CSV: {os.path.abspath(csv_report_path)}")
        print(f"Report TXT: {os.path.abspath(txt_report_path)}")
        print(f"Comparison Chart: {os.path.abspath(plot_path)}")
        print(f"Confusion Matrices saved in: {os.path.abspath(cm_dir)}\\")
        
    # Step 11: Proper Exception Handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
    except KeyError as e:
        print(f"\n[ERROR - Column Missing] {e}")
    except ValueError as e:
        print(f"\n[ERROR - Value Error] {e}")
    except ImportError as e:
        print(f"\n[ERROR - Missing Package] Please run 'pip install scikit-learn matplotlib seaborn'. Error: {e}")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An error occurred: {e}")

if __name__ == "__main__":
    compare_models()
