import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QComboBox, QSpinBox, 
                           QDoubleSpinBox, QGraphicsView, QGraphicsScene, QRubberBand,
                           QGroupBox, QMessageBox, QShortcut, QStatusBar, QSlider,QStylePainter)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QImage, QPainter, QPixmap, QKeySequence, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class ROISelector(QGraphicsView):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.roi_start = None
        self.roi_end = None
        self.rubberBand = None
        self.rois = []
        # Add zoom support
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            # Zoom in/out with mouse wheel
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and len(self.rois) < 3:
            # Convert mouse coordinates to view coordinates
            self.roi_start = event.pos()
            if not self.rubberBand:
                self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.roi_start, self.roi_start))
            self.rubberBand.show()
        elif event.button() == Qt.RightButton:
            self.rois = []  # Clear ROIs on right click
            self.viewport().update()
            
    def mouseMoveEvent(self, event):
        if self.rubberBand:
            # Update rubber band geometry
            self.rubberBand.setGeometry(QRect(self.roi_start, event.pos()).normalized())
            
    def mouseReleaseEvent(self, event):
        if self.rubberBand and self.roi_start:
            self.roi_end = event.pos()
            # Create ROI in view coordinates
            roi = QRect(self.roi_start, self.roi_end).normalized()
            # Only add if ROI has non-zero size
            if roi.width() > 0 and roi.height() > 0:
                self.rois.append(roi)
            self.rubberBand.hide()
            self.rubberBand = None
            self.viewport().update()

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Advanced Image Quality Viewer')
        self.setGeometry(100, 100, 1400, 900)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create image viewers with labels
        viewers_layout = QHBoxLayout()
        
        # Input viewer group
        input_group = QGroupBox("Input Image")
        input_layout = QVBoxLayout()
        self.input_view = ROISelector("Input View")
        input_layout.addWidget(self.input_view)
        input_group.setLayout(input_layout)
        
        # Output1 viewer group
        output1_group = QGroupBox("Output 1")
        output1_layout = QVBoxLayout()
        self.output1_view = ROISelector("Output 1 View")
        output1_layout.addWidget(self.output1_view)
        output1_group.setLayout(output1_layout)
        
        # Output2 viewer group
        output2_group = QGroupBox("Output 2")
        output2_layout = QVBoxLayout()
        self.output2_view = ROISelector("Output 2 View")
        output2_layout.addWidget(self.output2_view)
        output2_group.setLayout(output2_layout)
        
        viewers_layout.addWidget(input_group)
        viewers_layout.addWidget(output1_group)
        viewers_layout.addWidget(output2_group)
        
        layout.addLayout(viewers_layout)
        
        # Controls in tabs
        controls_layout = QHBoxLayout()
        
        # File controls group
        file_group = QGroupBox("File Operations")
        file_controls = QVBoxLayout()
        self.load_btn = QPushButton('Load Image (Ctrl+O)')
        self.load_btn.setToolTip('Open a grayscale image file')
        self.load_btn.clicked.connect(self.load_image)
        self.save_btn = QPushButton('Save Current Image (Ctrl+S)')
        self.save_btn.setToolTip('Save the currently selected image')
        self.save_btn.clicked.connect(self.save_image)
        file_controls.addWidget(self.load_btn)
        file_controls.addWidget(self.save_btn)
        file_group.setLayout(file_controls)
        
        # Zoom controls group
        zoom_group = QGroupBox("Zoom Controls")
        zoom_controls = QVBoxLayout()
        self.zoom_factor = QSlider(Qt.Horizontal)
        self.zoom_factor.setRange(10, 500)
        self.zoom_factor.setValue(100)
        self.zoom_factor.setTickPosition(QSlider.TicksBelow)
        self.zoom_factor.setTickInterval(50)
        self.zoom_label = QLabel('Zoom: 100%')
        self.zoom_factor.valueChanged.connect(
            lambda v: self.zoom_label.setText(f'Zoom: {v}%'))
        
        self.interpolation_method = QComboBox()
        self.interpolation_method.addItems(['Nearest Neighbor', 'Linear', 'Bilinear', 'Cubic'])
        self.interpolation_method.setToolTip('Select interpolation method for zoom')
        
        zoom_controls.addWidget(self.zoom_label)
        zoom_controls.addWidget(self.zoom_factor)
        zoom_controls.addWidget(QLabel('Interpolation:'))
        zoom_controls.addWidget(self.interpolation_method)
        zoom_group.setLayout(zoom_controls)
        
        # Enhancement controls group
        enhance_group = QGroupBox("Image Enhancement")
        enhance_controls = QVBoxLayout()
        
        # Brightness/Contrast sliders
        self.brightness = QSlider(Qt.Horizontal)
        self.brightness.setRange(-100, 100)
        self.brightness.setValue(0)
        self.brightness.setTickPosition(QSlider.TicksBelow)
        self.brightness_label = QLabel('Brightness: 0')
        self.brightness.valueChanged.connect(
            lambda v: self.brightness_label.setText(f'Brightness: {v}'))
        
        self.contrast = QSlider(Qt.Horizontal)
        self.contrast.setRange(10, 300)
        self.contrast.setValue(100)
        self.contrast.setTickPosition(QSlider.TicksBelow)
        self.contrast_label = QLabel('Contrast: 100%')
        self.contrast.valueChanged.connect(
            lambda v: self.contrast_label.setText(f'Contrast: {v}%'))
        
        enhance_controls.addWidget(self.brightness_label)
        enhance_controls.addWidget(self.brightness)
        enhance_controls.addWidget(self.contrast_label)
        enhance_controls.addWidget(self.contrast)
        enhance_group.setLayout(enhance_controls)
        
        # Filters group
        filters_group = QGroupBox("Filters")
        filter_controls = QVBoxLayout()
        
        self.noise_type = QComboBox()
        self.noise_type.addItems(['None', 'Gaussian', 'Salt & Pepper', 'Speckle'])
        self.noise_type.setToolTip('Add noise to the image')
        
        self.denoise_type = QComboBox()
        self.denoise_type.addItems(['None', 'Median Filter', 'Gaussian Filter', 'Non-local Means'])
        self.denoise_type.setToolTip('Apply denoising filter')
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(['None', 'Lowpass', 'Highpass'])
        self.filter_type.setToolTip('Apply frequency domain filters')
        
        filter_controls.addWidget(QLabel('Add Noise:'))
        filter_controls.addWidget(self.noise_type)
        filter_controls.addWidget(QLabel('Denoise:'))
        filter_controls.addWidget(self.denoise_type)
        filter_controls.addWidget(QLabel('Filters:'))
        filter_controls.addWidget(self.filter_type)
        filters_group.setLayout(filter_controls)
        
        # Contrast enhancement group
        contrast_group = QGroupBox("Contrast Enhancement")
        contrast_controls = QVBoxLayout()
        self.contrast_method = QComboBox()
        self.contrast_method.addItems(['None', 'Histogram Equalization', 'CLAHE', 'Custom Stretching'])
        self.contrast_method.setToolTip('Apply contrast enhancement')
        
        contrast_controls.addWidget(QLabel('Enhancement Method:'))
        contrast_controls.addWidget(self.contrast_method)
        contrast_group.setLayout(contrast_controls)
        
        # Add all control groups
        controls_layout.addWidget(file_group)
        controls_layout.addWidget(zoom_group)
        controls_layout.addWidget(enhance_group)
        controls_layout.addWidget(filters_group)
        controls_layout.addWidget(contrast_group)
        
        # Action buttons with tooltips
        self.apply_btn = QPushButton('Apply to Output 1 (F5)')
        self.apply_btn.setToolTip('Apply current settings to Output 1')
        self.apply_btn2 = QPushButton('Apply to Output 2 (F6)')
        self.apply_btn2.setToolTip('Apply current settings to Output 2')
        self.measure_snr_btn = QPushButton('Measure SNR/CNR (F7)')
        self.measure_snr_btn.setToolTip('Select two ROIs to measure SNR/CNR')
        self.show_histogram_btn = QPushButton('Show Histogram (F8)')
        self.show_histogram_btn.setToolTip('Display image histogram')
        self.reset_btn = QPushButton('Reset All (F9)')
        self.reset_btn.setToolTip('Reset all settings to default')
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.apply_btn2)
        buttons_layout.addWidget(self.measure_snr_btn)
        buttons_layout.addWidget(self.show_histogram_btn)
        buttons_layout.addWidget(self.reset_btn)
        
        # Connect buttons
        self.apply_btn.clicked.connect(lambda: self.apply_processing(1))
        self.apply_btn2.clicked.connect(lambda: self.apply_processing(2))
        self.measure_snr_btn.clicked.connect(self.measure_snr_cnr)
        self.show_histogram_btn.clicked.connect(self.show_histogram)
        self.reset_btn.clicked.connect(self.reset_settings)
        
        # Keyboard shortcuts
        QShortcut(QKeySequence('Ctrl+O'), self, self.load_image)
        QShortcut(QKeySequence('Ctrl+S'), self, self.save_image)
        QShortcut(QKeySequence('F5'), self, lambda: self.apply_processing(1))
        QShortcut(QKeySequence('F6'), self, lambda: self.apply_processing(2))
        QShortcut(QKeySequence('F7'), self, self.measure_snr_cnr)
        QShortcut(QKeySequence('F8'), self, self.show_histogram)
        QShortcut(QKeySequence('F9'), self, self.reset_settings)
        
        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add all layouts to main layout
        layout.addLayout(controls_layout)
        layout.addLayout(buttons_layout)
        
        # Initialize image variables
        self.input_image = None
        self.output1_image = None
        self.output2_image = None
        
        # Show initial help message
        self.show_help()
        
    def show_help(self):
        help_text = """
        Welcome to Advanced Image Quality Viewer!
        
        Quick Tips:
        - Use Ctrl+Mouse Wheel to zoom in/out on any image
        - Right-click to clear ROI selections
        - Use keyboard shortcuts (shown in button labels)
        - Hover over controls for tooltips
        
        Getting Started:
        1. Load an image using 'Load Image' or Ctrl+O
        2. Adjust enhancement settings as needed
        3. Apply to Output 1 or 2 using F5/F6
        4. Use F7 to measure SNR/CNR
        5. Use F8 to view histograms
        """
        QMessageBox.information(self, "Help", help_text)
        
    def reset_settings(self):
        self.zoom_factor.setValue(100)
        self.brightness.setValue(0)
        self.contrast.setValue(100)
        self.noise_type.setCurrentIndex(0)
        self.denoise_type.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(0)
        self.contrast_method.setCurrentIndex(0)
        self.statusBar.showMessage('All settings reset to default', 3000)
        
    def save_image(self):
        if not any([self.input_image is not None, 
                   self.output1_image is not None, 
                   self.output2_image is not None]):
            self.statusBar.showMessage('No image to save!', 3000)
            return
            
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "", 
                                                 "Image Files (*.png *.jpg *.bmp *.tif)")
        if file_name:
            # Determine which image to save based on focus
            if self.output2_view.hasFocus():
                cv2.imwrite(file_name, self.output2_image)
            elif self.output1_view.hasFocus():
                cv2.imwrite(file_name, self.output1_image)
            else:
                cv2.imwrite(file_name, self.input_image)
            self.statusBar.showMessage(f'Image saved to {file_name}', 3000)
        
    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", 
                                                "Image Files (*.png *.jpg *.bmp *.tif)")
        if file_name:
            self.input_image = cv2.imread(file_name)  # Removed cv2.IMREAD_GRAYSCALE
            self.display_image(self.input_image, self.input_view)
            self.statusBar.showMessage(f'Loaded image: {file_name}', 3000)
    
            
    def display_image(self, image, view):
        if image is not None:
            height, width = image.shape[:2]  # Changed to handle both color and grayscale
            if len(image.shape) == 3:  # Color image
                bytes_per_line = 3 * width
                # Convert BGR to RGB for Qt
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:  # Grayscale image
                bytes_per_line = width
                q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                
            scene = QGraphicsScene()
            scene.addPixmap(QPixmap.fromImage(q_image))
            view.setScene(scene)
            view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
                
    def apply_processing(self, output_num):
        if self.input_image is None:
            self.statusBar.showMessage('No image loaded!', 3000)
            return
            
        # Check if trying to process output 2 without output 1
        if output_num == 2 and self.output1_image is None:
            self.statusBar.showMessage('Please process Output 1 first!', 3000)
            return
                
        # Get source image based on output number
        source_image = self.input_image if output_num == 1 else self.output1_image
        
        try:
            # Apply selected processing
            processed_image = None
            
            # Zoom processing
            if self.zoom_factor.value() != 100:
                zoom_value = self.zoom_factor.value() / 100.0
                new_size = (int(source_image.shape[1] * zoom_value),
                        int(source_image.shape[0] * zoom_value))
                
                interpolation_methods = {
                    'Nearest Neighbor': cv2.INTER_NEAREST,
                    'Linear': cv2.INTER_LINEAR,
                    'Bilinear': cv2.INTER_LINEAR,
                    'Cubic': cv2.INTER_CUBIC
                }
                
                method = interpolation_methods[self.interpolation_method.currentText()]
                processed_image = cv2.resize(source_image, new_size, interpolation=method)
                
            # Initialize processed image if not yet done
            if processed_image is None:
                processed_image = source_image.copy()

            # Split image into channels if it's color
            is_color = len(processed_image.shape) == 3
            if is_color:
                b, g, r = cv2.split(processed_image)
            else:
                processed_image = processed_image.copy()
                
            # Noise processing
            if self.noise_type.currentText() != 'None':
                if self.noise_type.currentText() == 'Gaussian':
                    if is_color:
                        for channel in [b, g, r]:
                            noise = np.random.normal(0, 25, channel.shape).astype(np.uint8)
                            channel[:] = cv2.add(channel, noise)
                    else:
                        noise = np.random.normal(0, 25, processed_image.shape).astype(np.uint8)
                        processed_image = cv2.add(processed_image, noise)
                        
                elif self.noise_type.currentText() == 'Salt & Pepper':
                    prob = 0.05
                    if is_color:
                        for channel in [b, g, r]:
                            noise = np.random.random(channel.shape)
                            channel[noise < prob/2] = 0
                            channel[noise > 1 - prob/2] = 255
                    else:
                        noise = np.random.random(processed_image.shape)
                        processed_image[noise < prob/2] = 0
                        processed_image[noise > 1 - prob/2] = 255
                        
                elif self.noise_type.currentText() == 'Speckle':
                    if is_color:
                        for channel in [b, g, r]:
                            noise = np.random.normal(0, 25, channel.shape).astype(np.uint8)
                            channel[:] = channel + channel * noise/255
                    else:
                        noise = np.random.normal(0, 25, processed_image.shape).astype(np.uint8)
                        processed_image = processed_image + processed_image * noise/255
                    
            # Denoising
            if self.denoise_type.currentText() != 'None':
                if self.denoise_type.currentText() == 'Median Filter':
                    if is_color:
                        b = cv2.medianBlur(b, 5)
                        g = cv2.medianBlur(g, 5)
                        r = cv2.medianBlur(r, 5)
                    else:
                        processed_image = cv2.medianBlur(processed_image, 5)
                        
                elif self.denoise_type.currentText() == 'Gaussian Filter':
                    if is_color:
                        b = cv2.GaussianBlur(b, (5,5), 0)
                        g = cv2.GaussianBlur(g, (5,5), 0)
                        r = cv2.GaussianBlur(r, (5,5), 0)
                    else:
                        processed_image = cv2.GaussianBlur(processed_image, (5,5), 0)
                        
                elif self.denoise_type.currentText() == 'Non-local Means':
                    if is_color:
                        processed_image = cv2.fastNlMeansDenoisingColored(processed_image)
                    else:
                        processed_image = cv2.fastNlMeansDenoising(processed_image)
                    
            # Filters
            if self.filter_type.currentText() != 'None':
                if self.filter_type.currentText() == 'Lowpass':
                    kernel = np.ones((5,5), np.float32)/25
                    if is_color:
                        b = cv2.filter2D(b, -1, kernel)
                        g = cv2.filter2D(g, -1, kernel)
                        r = cv2.filter2D(r, -1, kernel)
                    else:
                        processed_image = cv2.filter2D(processed_image, -1, kernel)
                        
                elif self.filter_type.currentText() == 'Highpass':
                    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                    if is_color:
                        b = cv2.filter2D(b, -1, kernel)
                        g = cv2.filter2D(g, -1, kernel)
                        r = cv2.filter2D(r, -1, kernel)
                    else:
                        processed_image = cv2.filter2D(processed_image, -1, kernel)
                    
            # Contrast adjustment
            if self.contrast_method.currentText() != 'None':
                if self.contrast_method.currentText() == 'Histogram Equalization':
                    if is_color:
                        # Convert to LAB color space
                        lab = cv2.cvtColor(processed_image, cv2.COLOR_BGR2LAB)
                        l, a, b = cv2.split(lab)
                        # Apply histogram equalization to L channel
                        l = cv2.equalizeHist(l)
                        # Merge channels and convert back to BGR
                        lab = cv2.merge((l, a, b))
                        processed_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                    else:
                        processed_image = cv2.equalizeHist(processed_image)
                        
                elif self.contrast_method.currentText() == 'CLAHE':
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    if is_color:
                        lab = cv2.cvtColor(processed_image, cv2.COLOR_BGR2LAB)
                        l, a, b = cv2.split(lab)
                        l = clahe.apply(l)
                        lab = cv2.merge((l, a, b))
                        processed_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                    else:
                        processed_image = clahe.apply(processed_image)
                        
            # Merge channels back if color image
            if is_color and self.noise_type.currentText() != 'None' or self.denoise_type.currentText() != 'None' or self.filter_type.currentText() != 'None':
                processed_image = cv2.merge([b, g, r])
                    
            # Apply brightness and contrast
            alpha = self.contrast.value() / 100.0
            beta = self.brightness.value()
            processed_image = cv2.convertScaleAbs(processed_image, alpha=alpha, beta=beta)
                
            # Ensure image is in valid range
            processed_image = np.clip(processed_image, 0, 255).astype(np.uint8)
                
            # Update appropriate output view
            if output_num == 1:
                self.output1_image = processed_image.copy()
                self.display_image(self.output1_image, self.output1_view)
            else:
                self.output2_image = processed_image.copy()
                self.display_image(self.output2_image, self.output2_view)
                
            self.statusBar.showMessage(f'Processing applied to Output {output_num}', 3000)
            
        except Exception as e:
            self.statusBar.showMessage(f'Error processing image: {str(e)}', 3000)
            print(f"Error details: {str(e)}")  # For debugging
    def measure_snr_cnr(self):
        # Determine which view is currently focused
        if self.output2_view.hasFocus():
            current_view = self.output2_view
            current_image = self.output2_image
            view_name = "Output 2"
        elif self.output1_view.hasFocus():
            current_view = self.output1_view
            current_image = self.output1_image
            view_name = "Output 1"
        else:
            current_view = self.input_view
            current_image = self.input_image
            view_name = "Input"

        if current_image is None:
            self.statusBar.showMessage('No image in selected view!', 3000)
            return

        # Clear previous ROIs
        current_view.rois = []
        
        self.statusBar.showMessage(f'Select three ROIs in {view_name}', 3000)
        
        # Wait for user to select two ROIs
        while len(current_view.rois) < 3:
            QApplication.processEvents()
            
        try:
            # Calculate SNR/CNR from ROIs
            roi1 = current_view.rois[0]
            roi2 = current_view.rois[1]
            roi3 = current_view.rois[2]
            # Convert view coordinates to scene coordinates
            scene_rect = current_view.scene().sceneRect()
            
            # Calculate scaling factors
            scale_x = current_image.shape[1] / scene_rect.width()
            scale_y = current_image.shape[0] / scene_rect.height()
            
            # Convert ROI coordinates to scene coordinates
            roi1_scene = current_view.mapToScene(roi1).boundingRect()
            roi2_scene = current_view.mapToScene(roi2).boundingRect()
            roi3_scene = current_view.mapToScene(roi3).boundingRect()
            # Convert scene coordinates to image coordinates
            roi1_x = int(roi1_scene.x() * scale_x)
            roi1_y = int(roi1_scene.y() * scale_y)
            roi1_width = int(roi1_scene.width() * scale_x)
            roi1_height = int(roi1_scene.height() * scale_y)
            
            roi2_x = int(roi2_scene.x() * scale_x)
            roi2_y = int(roi2_scene.y() * scale_y)
            roi2_width = int(roi2_scene.width() * scale_x)
            roi2_height = int(roi2_scene.height() * scale_y)
            
            roi3_x = int(roi3_scene.x() * scale_x)
            roi3_y = int(roi3_scene.y() * scale_y)
            roi3_width = int(roi3_scene.width() * scale_x)
            roi3_height = int(roi3_scene.height() * scale_y)
            
            # Ensure coordinates are within image bounds
            roi1_x = max(0, min(roi1_x, current_image.shape[1] - 1))
            roi1_y = max(0, min(roi1_y, current_image.shape[0] - 1))
            roi2_x = max(0, min(roi2_x, current_image.shape[1] - 1))
            roi2_y = max(0, min(roi2_y, current_image.shape[0] - 1))
            roi3_x = max(0, min(roi3_x, current_image.shape[1] - 1))
            roi3_y = max(0, min(roi3_y, current_image.shape[0] - 1))
            
            
            roi1_width = min(roi1_width, current_image.shape[1] - roi1_x)
            roi1_height = min(roi1_height, current_image.shape[0] - roi1_y)
            roi2_width = min(roi2_width, current_image.shape[1] - roi2_x)
            roi2_height = min(roi2_height, current_image.shape[0] - roi2_y)
            roi3_width = min(roi3_width, current_image.shape[1] - roi2_x)
            roi3_height = min(roi3_height, current_image.shape[0] - roi2_y)
            
            # Extract ROI data
            roi1_data = current_image[roi1_y:roi1_y+roi1_height, roi1_x:roi1_x+roi1_width]
            roi2_data = current_image[roi2_y:roi2_y+roi2_height, roi2_x:roi2_x+roi2_width]
            roi3_data = current_image[roi3_y:roi3_y+roi3_height, roi3_x:roi3_x+roi3_width]

            # Handle color images by converting to grayscale if needed
            if len(current_image.shape) == 3:
                roi1_data = cv2.cvtColor(roi1_data, cv2.COLOR_BGR2GRAY)
                roi2_data = cv2.cvtColor(roi2_data, cv2.COLOR_BGR2GRAY)
                roi3_data = cv2.cvtColor(roi3_data, cv2.COLOR_BGR2GRAY)
                
            # Calculate metrics
            signal_mean = np.mean(roi1_data)
            noise_mean = np.mean(roi2_data)
            noise_std = np.std(roi3_data)
            
            snr = signal_mean / noise_std if noise_std != 0 else 0
            cnr = abs(signal_mean - noise_mean) / noise_std if noise_std != 0 else 0
            
            # Show results
            msg = f'{view_name} Measurements:\nSNR: {snr:.2f}\nCNR: {cnr:.2f}'
            QMessageBox.information(self, 'Measurements', msg)
            
        except Exception as e:
            self.statusBar.showMessage(f'Error calculating measurements: {str(e)}', 3000)
            print(f"Error details: {str(e)}")  # For debugging)
    def show_histogram(self):
        try:
            # Get the currently focused view
            if self.output2_view.hasFocus():
                image = self.output2_image
                current_view = self.output2_view
                title = "Output 2 Histogram"
            elif self.output1_view.hasFocus():
                image = self.output1_image
                current_view = self.output1_view
                title = "Output 1 Histogram"
            else:
                image = self.input_image
                current_view = self.input_view
                title = "Input Image Histogram"

            if image is None:
                self.statusBar.showMessage('No image selected!', 3000)
                return

            # Check for ROIs
            rois = current_view.rois
            if not rois:
                # If no ROIs, show histogram for entire image
                if len(image.shape) == 3:  # Color image
                    plt.figure(figsize=(10, 8))
                    colors = ('b', 'g', 'r')
                    for i, color in enumerate(colors):
                        hist = cv2.calcHist([image], [i], None, [256], [0, 256])
                        plt.plot(hist, color=color)
                    plt.title(f'{title} - Full Image')
                    plt.xlabel('Pixel Value')
                    plt.ylabel('Count')
                    plt.legend(['Blue', 'Green', 'Red'])
                else:  # Grayscale image
                    plt.figure(figsize=(10, 8))
                    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
                    plt.plot(hist)
                    plt.title(f'{title} - Full Image')
                    plt.xlabel('Pixel Value')
                    plt.ylabel('Count')
                
                plt.grid(True)
                plt.show()
                return

            # Process ROIs
            scene = current_view.scene()
            view_rect = current_view.viewport().rect()
            scale_x = image.shape[1] / scene.width()
            scale_y = image.shape[0] / scene.height()

            fig = plt.figure(figsize=(15, 5 * len(rois)))
            fig.suptitle(f'{title} - ROI Analysis', fontsize=16)

            for idx, roi in enumerate(rois):
                # Convert ROI to scene coordinates
                roi_scene = current_view.mapToScene(roi).boundingRect()
                
                # Calculate image coordinates
                x = int(max(0, min(roi_scene.x() * scale_x, image.shape[1]-1)))
                y = int(max(0, min(roi_scene.y() * scale_y, image.shape[0]-1)))
                w = int(min(roi_scene.width() * scale_x, image.shape[1]-x))
                h = int(min(roi_scene.height() * scale_y, image.shape[0]-y))

                # Extract ROI from image
                roi_img = image[y:y+h, x:x+w]

                if len(image.shape) == 3:  # Color image
                    plt.subplot(len(rois), 2, 2*idx + 1)
                    plt.imshow(cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB))
                    plt.title(f'ROI {idx+1}')
                    plt.axis('off')

                    plt.subplot(len(rois), 2, 2*idx + 2)
                    colors = ('b', 'g', 'r')
                    for i, color in enumerate(colors):
                        hist = cv2.calcHist([roi_img], [i], None, [256], [0, 256])
                        plt.plot(hist, color=color)
                    plt.title(f'ROI {idx+1} Histogram')
                    plt.xlabel('Pixel Value')
                    plt.ylabel('Count')
                    plt.legend(['Blue', 'Green', 'Red'])
                    plt.grid(True)
                else:  # Grayscale image
                    plt.subplot(len(rois), 2, 2*idx + 1)
                    plt.imshow(roi_img, cmap='gray')
                    plt.title(f'ROI {idx+1}')
                    plt.axis('off')

                    plt.subplot(len(rois), 2, 2*idx + 2)
                    hist = cv2.calcHist([roi_img], [0], None, [256], [0, 256])
                    plt.plot(hist)
                    plt.title(f'ROI {idx+1} Histogram')
                    plt.xlabel('Pixel Value')
                    plt.ylabel('Count')
                    plt.grid(True)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            self.statusBar.showMessage(f'Error showing histogram: {str(e)}', 3000)
            print(f"Error details: {str(e)}")  # For debugging
if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())