import cv2
import numpy as np
import os

# Fixed rectangle size
rect_width = 360
rect_height = 240

def detect_face(image_path):
    """Detects face using Haar Cascade classifier"""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from '{image_path}'.")
        return None
    
    # Resize if needed
    if image.shape[1] != 1920 or image.shape[0] != 1080:
        image = cv2.resize(image, (1920, 1080))
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        # Get the largest face
        x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        # Return center coordinates (normalized 0-1)
        return {
            'x': (x + w/2) / 1920,
            'y': (y + h/2) / 1080
        }
    return None

def deteccionCara(image_path):
    if image_path is None or not os.path.exists(image_path):
        print(f"Error: Invalid image path '{image_path}'.")
        return None
    
    # First try automatic face detection
    coords = detect_face(image_path)
    if coords:
        print(f"Auto-detected face at {coords}")
        return coords
    
    # Fallback to center coordinates
    print("No face detected, using center coordinates")
    return {'x': 0.5, 'y': 0.5}