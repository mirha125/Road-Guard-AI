import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import cv2
from collections import deque
from pathlib import Path
import asyncio

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AccidentDetectionService:
    def __init__(self):
        self.model = None
        self.sequence_length = 16  # Updated to match model requirement
        self.image_height = 224    # Updated to match model requirement
        self.image_width = 224     # Updated to match model requirement
        self.active_detections: Dict[str, bool] = {}
        self.frame_buffers: Dict[str, deque] = {}
        
    def build_cnn_lstm_model(self):
        """
        Reconstruct the model architecture exactly as defined in training.
        """
        input_shape = (self.image_height, self.image_width, 3)
        
        # Data Augmentation Layer (Must be included to match topology, though unused in inference)
        data_augmentation = tf.keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.1),
            layers.RandomBrightness(0.1),
            layers.RandomContrast(0.1),
        ])

        # CNN Base (ResNet50)
        # We use weights=None because we will load our own trained weights immediately after.
        # This avoids the SSL error when trying to download ImageNet weights.
        cnn_base = tf.keras.applications.ResNet50(
            include_top=False, weights=None, pooling='avg', input_shape=input_shape
        )
        # Note: Trainable state doesn't affect inference, but matching structure does.
        cnn_base.trainable = True 

        model = models.Sequential([
            layers.Input(shape=(self.sequence_length,) + input_shape),
            layers.TimeDistributed(data_augmentation),
            layers.TimeDistributed(cnn_base),
            layers.LSTM(256, return_sequences=False),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(2, activation='softmax')
        ])

        # We don't need to compile for inference, and it avoids optimizer mismatch warnings
        # model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def load_model(self):
        """Load the pre-trained accident detection model weights"""
        if self.model is None:
            try:
                model_path = Path(__file__).parent.parent / "aiModel" / "accident_detector_cnn_lstm.keras"
                logger.info(f"Building model architecture...")
                self.model = self.build_cnn_lstm_model()
                
                logger.info(f"Loading weights from {model_path}")
                # Load weights into the built model
                self.model.load_weights(str(model_path))
                
                logger.info("Model weights loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
    
    def preprocess_frame(self, frame):
        """Preprocess a single frame for the model"""
        # Resize frame to the required size
        resized_frame = cv2.resize(frame, (self.image_height, self.image_width))
        # Return raw BGR frame (0-255) as trained
        return resized_frame.astype(np.float32)
    
    
    def predict_accident(self, frames_buffer: deque) -> tuple[bool, float]:
        """
        Predict if an accident occurred in the frame sequence
        Returns: (is_accident, confidence)
        """
        if len(frames_buffer) < self.sequence_length:
            return False, 0.0
        
        try:
            # Get the last sequence_length frames
            frames = list(frames_buffer)[-self.sequence_length:]
            
            # Stack frames into a sequence
            sequence = np.array(frames)
            
            # Add batch dimension
            sequence = np.expand_dims(sequence, axis=0)
            
            # Make prediction
            prediction = self.model.predict(sequence, verbose=0)
            
            # Get confidence score for Accident class (index 1)
            # Index 0 is Normal, Index 1 is Accident
            confidence = float(prediction[0][1])
            
            # Threshold for accident detection
            is_accident = confidence > 0.5
            
            logger.info(f"Prediction: {confidence:.4f}, Accident: {is_accident}")
            
            return is_accident, confidence
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return False, 0.0
    
    async def start_detection(self, camera_id: str, camera_url: str) -> bool:
        """Start accident detection for a camera"""
        if camera_id in self.active_detections and self.active_detections[camera_id]:
            logger.warning(f"Detection already active for camera {camera_id}")
            return False
        
        # Ensure model is loaded
        if self.model is None:
            self.load_model()
        
        # Initialize frame buffer for this camera
        self.frame_buffers[camera_id] = deque(maxlen=self.sequence_length)
        self.active_detections[camera_id] = True
        
        logger.info(f"Started detection for camera {camera_id}")
        return True
    
    def stop_detection(self, camera_id: str) -> bool:
        """Stop accident detection for a camera"""
        if camera_id in self.active_detections:
            self.active_detections[camera_id] = False
            if camera_id in self.frame_buffers:
                del self.frame_buffers[camera_id]
            logger.info(f"Stopped detection for camera {camera_id}")
            return True
        return False
    
    def is_detection_active(self, camera_id: str) -> bool:
        """Check if detection is active for a camera"""
        return self.active_detections.get(camera_id, False)
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> tuple[bool, float]:
        """
        Process a single frame and return if accident is detected
        Returns: (is_accident, confidence)
        """
        if not self.is_detection_active(camera_id):
            return False, 0.0
        
        # Preprocess the frame
        processed_frame = self.preprocess_frame(frame)
        
        # Add to buffer
        if camera_id not in self.frame_buffers:
            self.frame_buffers[camera_id] = deque(maxlen=self.sequence_length)
        
        self.frame_buffers[camera_id].append(processed_frame)
        
        # Only predict when we have enough frames
        if len(self.frame_buffers[camera_id]) >= self.sequence_length:
            return self.predict_accident(self.frame_buffers[camera_id])
        
        return False, 0.0

# Global instance
accident_detection_service = AccidentDetectionService()
