import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
import json
import os

# Configuration
DATASET_DIR = r"D:\teju\AI_Food Freshness Monitoring Platform\datasets\Freshness44"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 5 # Full 5-pass training for maximum accuracy

print("Loading dataset...")
# Load dataset
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)
class_names = train_ds.class_names # Extract before taking subset
num_classes = len(class_names)
train_ds = train_ds.take(100) # Medium hack: 100 batches (~3200 images) to finish in 6 mins before crash

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)
val_ds = val_ds.take(20)


print(f"Found {num_classes} classes.")

# Save class names for the inference engine
with open("class_names.json", "w") as f:
    json.dump(class_names, f)

print("Building model...")
# Data augmentation
data_augmentation = tf.keras.Sequential([
  layers.RandomFlip("horizontal_and_vertical"),
  layers.RandomRotation(0.2),
])

# Create the base model from the pre-trained model MobileNet V2
preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

inputs = tf.keras.Input(shape=(224, 224, 3))
x = data_augmentation(inputs)
x = preprocess_input(x)

base_model = MobileNetV2(input_shape=(224, 224, 3),
                         include_top=False,
                         weights='imagenet')
base_model.trainable = False # Freeze base model

x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.2)(x)
outputs = layers.Dense(num_classes, activation='softmax')(x)
model = tf.keras.Model(inputs, outputs)

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              loss=tf.keras.losses.SparseCategoricalCrossentropy(),
              metrics=['accuracy'])

print("Starting training...")
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS
)

print("Saving model...")
model.save("fresh_detect_model.keras")
print("Training complete! Model saved as fresh_detect_model.keras")
