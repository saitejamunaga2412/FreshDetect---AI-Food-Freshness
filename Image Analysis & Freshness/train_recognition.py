import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import json
import os

print("Starting Food Recognition Model Training...")

# Dataset paths
base_dir = r"d:\teju\AI_Food Freshness Monitoring Platform\datasets\fruits-360_100x100\fruits-360"
train_dir = os.path.join(base_dir, 'Training')
test_dir = os.path.join(base_dir, 'Test')

# Image properties
IMG_SIZE = (100, 100) # Fruits-360 uses 100x100
BATCH_SIZE = 64

# Data Augmentation & Loading
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=15,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

# Save class names mapping
class_names = list(train_generator.class_indices.keys())
with open('food_classes.json', 'w') as f:
    json.dump(class_names, f)
print(f"Found {len(class_names)} food classes.")

# Build Model (Transfer Learning with MobileNetV2)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(100, 100, 3))
base_model.trainable = False # Freeze base layers for fast training

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.2)(x)
predictions = Dense(len(class_names), activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Callbacks
callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=1, restore_best_weights=True),
    ModelCheckpoint('food_recognition_model.keras', save_best_only=True, monitor='val_accuracy')
]

# Train
history = model.fit(
    train_generator,
    epochs=3, # 3 epochs for fast demonstration but high accuracy due to Transfer Learning
    validation_data=test_generator,
    callbacks=callbacks
)

print("Training Complete! Model saved as 'food_recognition_model.keras'")
