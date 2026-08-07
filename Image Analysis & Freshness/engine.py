import cv2
import numpy as np
import os
import json
import tensorflow as tf

# Load the trained ML model and class names
MODEL_PATH = os.path.join(os.path.dirname(__file__), "fresh_detect_model.keras")
CLASS_NAMES_PATH = os.path.join(os.path.dirname(__file__), "class_names.json")

print("Loading Keras model...")
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(CLASS_NAMES_PATH, "r") as f:
        class_names = json.load(f)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    class_names = []

def assess_freshness(image_bytes: bytes):
    """
    Analyzes an image using the trained Keras Deep Learning model.
    """
    if model is None:
        return {
            "score": 0,
            "status": "ERROR",
            "confidence": 0.0,
            "details": {"error": "ML Model not loaded."}
        }

    try:
        # Decode image bytes
        img = tf.io.decode_image(image_bytes, channels=3)
        img = tf.image.resize(img, [224, 224])
        img_array = tf.expand_dims(img, 0) # Create a batch

        # Get prediction
        predictions = model.predict(img_array)
        score_probs = tf.nn.softmax(predictions[0]) # Assuming softmax is in the model, but actually it is already softmaxed
        
        # In train.py, the model output is already softmaxed: outputs = layers.Dense(..., activation='softmax')(x)
        # So predictions[0] is already probabilities
        predicted_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_idx]) * 100
        predicted_class = class_names[predicted_idx]
        
        # Extract food name assuming format like "Apple_Rotten" or "Banana_Fresh"
        food_name = predicted_class.split('_')[0]
        # Format it nicely (e.g. replace dashes)
        food_name = food_name.replace('-', ' ').title()
        
        # Determine status and freshness score based on class name
        if "_Rotten" in predicted_class or "_spoiled" in predicted_class.lower() or "Spoiled" in predicted_class:
            status = "SPOILED"
            # Since the fast model might have low confidence, ensure score is appropriately low
            score = min(25, max(5, int(100 - confidence)))
        else:
            status = "FRESH"
            # Ensure fresh score is appropriately high, even if fast-model confidence is low
            score = max(85, min(98, int(confidence + 70)))
            
        # The AI confidence is what the model actually output
        return {
            "foodName": food_name,
            "score": score,
            "status": status,
            "confidence": round(confidence, 1),
            "details": {
                "predicted_class": predicted_class,
                "model_type": "Deep Learning (MobileNetV2)"
            }
        }

    except Exception as e:
        print(f"Prediction error: {e}")
        return {
            "score": 0,
            "status": "ERROR",
            "confidence": 0.0,
            "details": {"error": str(e)}
        }
