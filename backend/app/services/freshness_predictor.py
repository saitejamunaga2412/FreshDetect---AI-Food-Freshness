import os
import logging
import joblib

logger = logging.getLogger(__name__)

class FreshnessPredictor:
    """
    Predicts freshness based on environmental factors using an ML model.
    """
    def __init__(self):
        # Paths to artifacts
        base_dir = os.path.dirname(__file__)
        self.model_path = os.path.abspath(os.path.join(base_dir, "..", "..", "weights", "freshness_model.pkl"))
        self.scaler_path = os.path.abspath(os.path.join(base_dir, "..", "..", "weights", "scaler.pkl"))
        self.encoder_path = os.path.abspath(os.path.join(base_dir, "..", "..", "weights", "fruit_encoder.pkl"))
        
        self.model = None
        self.scaler = None
        self.encoder = None
        
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
            if os.path.exists(self.encoder_path):
                self.encoder = joblib.load(self.encoder_path)
            logger.info("Freshness ML Model and Scaler loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Freshness Predictor models: {e}")

    def predict(self, fruit: str, temp: float, humid: float) -> dict:
        """
        Predict freshness using fruit and environmental variables.
        """
        if self.model is None or self.scaler is None or self.encoder is None:
            logger.warning("ML Model artifacts not fully loaded. Returning degraded prediction.")
            return {"prediction": "Unknown", "probability": 0.0}

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Transform fruit
                # Handle unknown fruits gracefully
                try:
                    fruit_encoded = self.encoder.transform([fruit])[0]
                except ValueError:
                    logger.warning(f"Unseen fruit '{fruit}' encountered. Defaulting to 0.")
                    fruit_encoded = 0

                # 1. Prepare Feature Array: fruit, temp, humid_(%)
                features_env = [[temp, humid]]
                features_env_scaled = self.scaler.transform(features_env)
                
                features = [[fruit_encoded, features_env_scaled[0][0], features_env_scaled[0][1]]]
                
                # 3. Predict Class Index
                pred_idx = self.model.predict(features)[0]
                
                # 4. Predict Probability (Confidence)
                prob_array = self.model.predict_proba(features)[0]
                
                # We explicitly mapped Good=1, Bad=0.
                probability = prob_array[1]
                
                # 5. Inverse Transform Label
                prediction = "Good" if pred_idx == 1 else "Bad"

            return {
                "prediction": prediction,
                "probability": float(probability)
            }
        except Exception as e:
            logger.error(f"Error predicting freshness: {e}")
            return {
                "prediction": "Unknown",
                "probability": 0.0
            }
