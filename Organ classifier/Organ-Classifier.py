import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf
from pathlib import Path
import os

class MedicalImageClassifier:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Image Classifier")
        self.root.geometry("800x600")
        
        # Initialize model
        self.model = tf.keras.models.load_model("C:/Users/ahmed/OneDrive/Desktop/task2/newnew.h5")
        self.preds = ["brain", "breast", "knee", "lung"]
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Upload button
        self.upload_btn = ttk.Button(
            main_frame, 
            text="Upload Image",
            command=self.upload_image
        )
        self.upload_btn.grid(row=0, column=0, pady=10)
        
        # Frame for image display
        self.image_frame = ttk.Frame(main_frame, borderwidth=2, relief="solid")
        self.image_frame.grid(row=1, column=0, padx=10, pady=10)
        
        # Label for image display
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.grid(row=0, column=0, padx=10, pady=10)
        
        # Result frame
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=2, column=0, pady=10)
        
        # Result label
        self.result_var = tk.StringVar()
        self.result_var.set("Upload an image to get prediction")
        self.result_label = ttk.Label(
            result_frame,
            textvariable=self.result_var,
            font=("Arial", 12)
        )
        self.result_label.grid(row=0, column=0)

    def preprocess_image(self, image):
        """Preprocess the image for model input"""
        # Resize to (256, 256)
        image = image.resize((256, 256))
        
        # Convert to Grayscale
        image = image.convert("L")
        
        # Convert to numpy array and add batch dimension
        image_array = np.array(image)
        image_array = np.expand_dims(image_array, axis=(0, -1))  # Adding batch and channel dimensions
        
        return image_array
    def upload_image(self):
        """Handle image upload and prediction"""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")
            ]
        )
        
        if file_path:
            # Load and display image
            image = Image.open(file_path)
            
            # Resize image for display while maintaining aspect ratio
            display_size = (300, 300)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for display
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep a reference
            
            # Preprocess image and make prediction
            preprocessed_image = self.preprocess_image(Image.open(file_path))
            prediction = self.model.predict(preprocessed_image)
            
            # Get predicted class
            predicted_class = self.preds[np.argmax(prediction)]
            confidence = np.max(prediction) * 100
            
            # Update result label
            self.result_var.set(
                f"Prediction: {predicted_class}\nConfidence: {confidence:.2f}%"
            )

def main():
    root = tk.Tk()
    app = MedicalImageClassifier(root)
    root.mainloop()

if __name__ == "__main__":
    main()