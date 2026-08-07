import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import json
import os

print("Starting Food Freshness Model Training...")

# Dataset paths
base_dir = r"d:\teju\AI_Food Freshness Monitoring Platform\datasets\Food Freshness Dataset"

# Image properties
IMG_SIZE = (224, 224) # Standard for Freshness
BATCH_SIZE = 32

# Data Augmentation & Loading (Split 80/20)
datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    validation_split=0.2 # 20% for validation
)

train_generator = datagen.flow_from_directory(
    base_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary', # Fresh vs Rotten
    subset='training'
)

val_generator = datagen.flow_from_directory(
    base_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation'
)

# Save class names mapping
class_names = list(train_generator.class_indices.keys())
with open('freshness_classes.json', 'w') as f:
    json.dump(class_names, f)
print(f"Found classes: {class_names}")

# Build Model (Transfer Learning with MobileNetV2)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False # Freeze base layers

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.2)(x)
predictions = Dense(1, activation='sigmoid')(x) # Binary classification

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Callbacks
callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=2, restore_best_weights=True),
    ModelCheckpoint('food_freshness_model.keras', save_best_only=True, monitor='val_accuracy')
]

# Train
history = model.fit(
    train_generator,
    epochs=5,
    validation_data=val_generator,
    callbacks=callbacks
)

print("Training Complete! Model saved as 'food_freshness_model.keras'")
