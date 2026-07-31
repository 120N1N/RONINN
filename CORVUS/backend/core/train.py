import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from backend.db.database import SessionLocal
from backend.db import models

class RandomForestTrainer:
    @staticmethod
    def train(dataset_id: int, params: dict, user_id: str) -> int:
        """
        Loads preprocessed datasets by ID, trains the RandomForest Classifier, evaluates it,
        saves the model object (.pkl), and logs training metrics in the database.
        """
        db = SessionLocal()
        try:
            dataset = db.query(models.PreprocessedDataset).filter(models.PreprocessedDataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Preprocessed dataset ID {dataset_id} not found in database.")
                
            train_path = dataset.file_path
            test_path = train_path.replace("_train.csv", "_test.csv")
            
            if not os.path.exists(train_path) or not os.path.exists(test_path):
                raise FileNotFoundError("Preprocessed dataset CSV files are missing from disk.")
                
            train_df = pd.read_csv(train_path)
            test_df = pd.read_csv(test_path)
            
            # Split features and labels
            X_train = train_df.drop(columns=['label'])
            y_train = train_df['label']
            X_test = test_df.drop(columns=['label'])
            y_test = test_df['label']
            
            # Unpack Hyperparameters
            n_estimators = int(params.get("n_estimators", 100))
            max_depth = params.get("max_depth")
            if max_depth is not None and str(max_depth).strip().lower() not in ["none", ""]:
                max_depth = int(max_depth)
            else:
                max_depth = None
                
            # Initialize & Fit Random Forest
            # Apply class_weight='balanced' to handle class imbalance natively
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                class_weight='balanced',
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Run Evaluation
            metrics = RandomForestTrainer.evaluate(model, X_test, y_test, X_train.columns.tolist())
            
            # Save Trained Model
            os.makedirs("models", exist_ok=True)
            model_filename = f"models/rf_ds{dataset_id}_est{n_estimators}.pkl"
            joblib.dump(model, model_filename)
            
            # Save Trained Model metadata in Database
            trained_model = models.TrainedModel(
                user_id=user_id,
                dataset_id=dataset_id,
                name=f"RF Classifier (DS #{dataset_id}, Trees: {n_estimators})",
                params={
                    "n_estimators": n_estimators,
                    "max_depth": max_depth
                },
                metrics=metrics,
                model_path=model_filename,
                is_active=False
            )
            db.add(trained_model)
            db.commit()
            db.refresh(trained_model)
            model_id = trained_model.id
            
        finally:
            db.close()
            
        return model_id

    @staticmethod
    def evaluate(model, X_test, y_test, feature_names: list) -> dict:
        """
        Calculates and maps performance metrics: Accuracy, Precision, Recall, F1, FPR,
        Confusion Matrix, and Feature Importance percentages.
        Also calculates Error Analysis stats.
        """
        y_pred = model.predict(X_test)
        
        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, zero_division=0))
        recall = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        
        # Calculate Confusion Matrix
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
        tn = fp = fn = tp = 0
        if cm.shape == (2, 2):
            tn, fp, fn, tp = map(int, cm.ravel())
                
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        
        # Extract Feature Importance breakdown
        importances = model.feature_importances_
        feature_importance_dict = {}
        for name, imp in zip(feature_names, importances):
            feature_importance_dict[name] = float(imp)
            
        # Scientific Error Analysis
        misclassified_count = fp + fn
        total_test_samples = len(y_test)
        misclassification_rate = float(misclassified_count / total_test_samples) if total_test_samples > 0 else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "fpr": fpr,
            "confusion_matrix": {
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "tp": tp
            },
            "feature_importance": feature_importance_dict,
            "error_analysis": {
                "false_positives": fp,
                "false_negatives": fn,
                "misclassified_count": misclassified_count,
                "misclassification_rate": misclassification_rate
            }
        }
