import os
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import filedialog, Frame, Label, Button, Scale, HORIZONTAL, VERTICAL, LEFT, RIGHT, BOTTOM, TOP, Checkbutton, IntVar, simpledialog
from matplotlib import gridspec

# Helper function to load a DICOM series
def load_dicom_series(folder_path):
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(folder_path)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    image_array = sitk.GetArrayFromImage(image)  # Convert to numpy array (z, y, x)
    return image_array

# Helper function to load a NIfTI file
def load_nifti_file(file_path):
    image = sitk.ReadImage(file_path)
    image_array = sitk.GetArrayFromImage(image)  # Convert to numpy array (z, y, x)
    return image_array

# Main Application Class for MPR Viewer
class MPRViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced MPR Viewer - ITK-Snap Style")

        # Load Buttons to Select DICOM Series or NIfTI File
        self.load_button = Button(root, text="Load DICOM Series", command=self.load_dicom_series)
        self.load_button.pack(side="top", padx=5, pady=5)

        self.load_nifti_button = Button(root, text="Load NIfTI File", command=self.load_nifti_file)
        self.load_nifti_button.pack(side="top", padx=5, pady=5)

        # Frame for Viewers
        self.viewer_frame = Frame(root)
        self.viewer_frame.pack(fill="both", expand=True)

        # Create Matplotlib figure for displaying three views with GridSpec
        self.fig, (self.axial_ax, self.coronal_ax, self.sagittal_ax) = plt.subplots(1, 3, figsize=(12, 5))
        self.fig.subplots_adjust(wspace=0.05)

        # Embedding Matplotlib figure into Tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viewer_frame)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # Controls for brightness, contrast, and other features in a more compact layout
        self.control_frame = Frame(root)
        self.control_frame.pack(side="bottom", fill="x")

        # Sub-frame for Play Cine buttons and brightness/contrast sliders
        self.bc_frame = Frame(self.control_frame)
        self.bc_frame.pack(side="left", padx=10, pady=5)

        # Axial Controls
        Label(self.bc_frame, text="Axial View").grid(row=0, column=0, columnspan=2)
        self.brightness_slider_axial = Scale(self.bc_frame, from_=-100, to=100, orient=HORIZONTAL, label="Brightness", command=self.update_brightness_axial)
        self.brightness_slider_axial.grid(row=1, column=0)
        self.contrast_slider_axial = Scale(self.bc_frame, from_=0.5, to=2.0, resolution=0.1, orient=HORIZONTAL, label="Contrast", command=self.update_contrast_axial)
        self.contrast_slider_axial.grid(row=1, column=1)
        
        

        # Coronal Controls
        Label(self.bc_frame, text="Coronal View").grid(row=0, column=2, columnspan=2)
        self.brightness_slider_coronal = Scale(self.bc_frame, from_=-100, to=100, orient=HORIZONTAL, label="Brightness", command=self.update_brightness_coronal)
        self.brightness_slider_coronal.grid(row=1, column=2)
        self.contrast_slider_coronal = Scale(self.bc_frame, from_=0.5, to=2.0, resolution=0.1, orient=HORIZONTAL, label="Contrast", command=self.update_contrast_coronal)
        self.contrast_slider_coronal.grid(row=1, column=3)

        # Sagittal Controls
        Label(self.bc_frame, text="Sagittal View").grid(row=0, column=4, columnspan=2)
        self.brightness_slider_sagittal = Scale(self.bc_frame, from_=-100, to=100, orient=HORIZONTAL, label="Brightness", command=self.update_brightness_sagittal)
        self.brightness_slider_sagittal.grid(row=1, column=4)
        self.contrast_slider_sagittal = Scale(self.bc_frame, from_=0.5, to=2.0, resolution=0.1, orient=HORIZONTAL, label="Contrast", command=self.update_contrast_sagittal)
        self.contrast_slider_sagittal.grid(row=1, column=5)

        # Other controls in a separate sub-frame for organization
        self.other_controls_frame = Frame(self.control_frame)
        self.other_controls_frame.pack(side=LEFT, padx=10, pady=5)

        self.play_button = Button(self.other_controls_frame, text="Play All Cine", command=self.toggle_cine_all)
        self.play_button.grid(row=0, column=0, padx=5, pady=5)

        self.cursor_button = Button(self.other_controls_frame, text="Cursor Inspector", command=self.activate_cursor_inspector)
        self.cursor_button.grid(row=0, column=1, padx=5, pady=5)

        self.save_button = Button(self.other_controls_frame, text="Save Slice", command=self.save_slice)
        self.save_button.grid(row=0, column=2, padx=5, pady=5)

        # Layout inspector checkboxes
        self.axial_var = IntVar(value=1)
        self.coronal_var = IntVar(value=1)
        self.sagittal_var = IntVar(value=1)

        self.axial_checkbox = Checkbutton(self.other_controls_frame, text="Show Axial", variable=self.axial_var, command=self.update_views)
        self.axial_checkbox.grid(row=1, column=0)

        self.coronal_checkbox = Checkbutton(self.other_controls_frame, text="Show Coronal", variable=self.coronal_var, command=self.update_views)
        self.coronal_checkbox.grid(row=1, column=1)

        self.sagittal_checkbox = Checkbutton(self.other_controls_frame, text="Show Sagittal", variable=self.sagittal_var, command=self.update_views)
        self.sagittal_checkbox.grid(row=1, column=2)

        # Slice sliders for each view
        self.slice_sliders_frame = Frame(self.control_frame)
        self.slice_sliders_frame.pack(side=LEFT, padx=10, pady=5)

        self.axial_slider = Scale(self.slice_sliders_frame, from_=0, to=0, orient=HORIZONTAL, label="Axial Slice", command=self.update_axial_slider)
        self.axial_slider.pack(side=LEFT, fill="x", padx=5)

        self.coronal_slider = Scale(self.slice_sliders_frame, from_=0, to=0, orient=HORIZONTAL, label="Coronal Slice", command=self.update_coronal_slider)
        self.coronal_slider.pack(side=LEFT, fill="x", padx=5)

        self.sagittal_slider = Scale(self.slice_sliders_frame, from_=0, to=0, orient=HORIZONTAL, label="Sagittal Slice", command=self.update_sagittal_slider)
        self.sagittal_slider.pack(side=LEFT, fill="x", padx=5)

        # Initialize default values for brightness and contrast
        self.brightness_axial = 0
        self.brightness_coronal = 0
        self.brightness_sagittal = 0
        self.contrast_axial = 1.0
        self.contrast_coronal = 1.0
        self.contrast_sagittal = 1.0

        # Modify the cine animation attributes
        self.cine_running = False
        self.cine_animation = None
        self.max_frames = 0

        # Connect matplotlib mouse events
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_click)
        self.fig.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)

    def load_dicom_series(self):
        folder_path = filedialog.askdirectory(title="Select a DICOM Series Folder")
        if folder_path:
            try:
                self.image_3d = load_dicom_series(folder_path)
                self.initialize_view()
            except Exception as e:
                print(f"Error loading DICOM series: {e}")

    def load_nifti_file(self):
        file_path = filedialog.askopenfilename(title="Select a NIfTI File", filetypes=[("NIfTI files", "*.nii *.nii.gz")])
        if file_path:
            try:
                self.image_3d = load_nifti_file(file_path)
                self.initialize_view()
            except Exception as e:
                print(f"Error loading NIfTI file: {e}")

    def initialize_view(self):
        self.z, self.y, self.x = self.image_3d.shape
        self.axial_idx = self.z // 2
        self.coronal_idx = self.y // 2
        self.sagittal_idx = self.x // 2

        # Update slider ranges
        self.axial_slider.config(to=self.z - 1)
        self.coronal_slider.config(to=self.y - 1)
        self.sagittal_slider.config(to=self.x - 1)

        self.update_views()

    def apply_brightness_contrast(self, image, brightness=0, contrast=1.0):
        image = np.clip((image * contrast) + brightness, 0, 255)
        return image.astype(np.uint8)

    def update_views(self):
        self.axial_ax.clear()
        self.coronal_ax.clear()
        self.sagittal_ax.clear()

        # Axial View
        if self.axial_var.get():
            axial_slice = self.apply_brightness_contrast(self.image_3d[self.axial_idx, :, :], self.brightness_axial, self.contrast_axial)
            self.axial_ax.imshow(np.flipud(axial_slice), cmap='gray', aspect='auto')
            self.axial_ax.set_title(f'Axial - Slice {self.axial_idx}')

        # Coronal View
        if self.coronal_var.get():
            coronal_slice = self.apply_brightness_contrast(self.image_3d[:, self.coronal_idx, :], self.brightness_coronal, self.contrast_coronal)
            self.coronal_ax.imshow(np.flipud(coronal_slice), cmap='gray', aspect='auto')
            self.coronal_ax.set_title(f'Coronal - Slice {self.coronal_idx}')

        # Sagittal View
        if self.sagittal_var.get():
            sagittal_slice = self.apply_brightness_contrast(self.image_3d[:, :, self.sagittal_idx], self.brightness_sagittal, self.contrast_sagittal)
            self.sagittal_ax.imshow(np.flipud(sagittal_slice), cmap='gray', aspect='auto')
            self.sagittal_ax.set_title(f'Sagittal - Slice {self.sagittal_idx}')

        self.canvas.draw_idle()

    def update_brightness_axial(self, value):
        self.brightness_axial = int(value)
        self.update_views()

    def update_brightness_coronal(self, value):
        self.brightness_coronal = int(value)
        self.update_views()

    def update_brightness_sagittal(self, value):
        self.brightness_sagittal = int(value)
        self.update_views()

    def update_contrast_axial(self, value):
        self.contrast_axial = float(value)
        self.update_views()

    def update_contrast_coronal(self, value):
        self.contrast_coronal = float(value)
        self.update_views()

    def update_contrast_sagittal(self, value):
        self.contrast_sagittal = float(value)
        self.update_views()

    def update_axial_slider(self, value):
        self.axial_idx = int(value)
        self.update_views()

    def update_coronal_slider(self, value):
        self.coronal_idx = int(value)
        self.update_views()

    def update_sagittal_slider(self, value):
        self.sagittal_idx = int(value)
        self.update_views()

    def toggle_cine_all(self):
        if not self.cine_running:
            self.cine_running = True
            self.play_button.config(text="Pause All Cine")
            self.max_frames = max(self.z, self.y, self.x)
            
            # Calculate the starting frame based on current positions
            start_frame = max(self.axial_idx, self.coronal_idx, self.sagittal_idx)
            
            # Create a new animation starting from the current position
            self.cine_animation = FuncAnimation(
                self.fig, 
                self.animate_cine, 
                frames=self.frame_generator(start_frame, self.max_frames), 
                interval=100, 
                repeat=True
            )
        else:
            self.cine_running = False
            self.play_button.config(text="Play All Cine")
            if self.cine_animation:
                self.cine_animation.event_source.stop()

    def frame_generator(self, start, end):
        current = start
        while True:
            yield current
            current = (current + 1) % end

    def draw_dotted_lines(self, ax, x, y):
        """Draws dotted lines on the specified axis."""
        ax.axhline(y, color='red', linestyle='--', linewidth=1)  # Horizontal line
        ax.axvline(x, color='green', linestyle='--', linewidth=1)  # Vertical line

    def animate_cine(self, frame):
        # Update axial view
        if frame < self.z:
            self.axial_idx = frame
            self.axial_slider.set(frame)
        
        # Update coronal view
        if frame < self.y:
            self.coronal_idx = frame
            self.coronal_slider.set(frame)
        
        # Update sagittal view
        if frame < self.x:
            self.sagittal_idx = frame
            self.sagittal_slider.set(frame)
        
        self.update_views()

     # Activating cursor inspector mode
    def activate_cursor_inspector(self):
        self.cursor_active = True

     # Save slice as image
    def save_slice(self):
        # Ask user which view they want to save
        view_choice = simpledialog.askstring("Save Slice", "Which view would you like to save? (axial, coronal, sagittal)")
        
        if view_choice not in ["axial", "coronal", "sagittal"]:
            print("Invalid view selected")
            return
        
        # Get the appropriate slice based on user selection
        if view_choice == "axial":
            slice_to_save = self.image_3d[self.axial_idx, :, :]
            title = f"Axial_Slice_{self.axial_idx}"
        elif view_choice == "coronal":
            slice_to_save = self.image_3d[:, self.coronal_idx, :]
            title = f"Coronal_Slice_{self.coronal_idx}"
        elif view_choice == "sagittal":
            slice_to_save = self.image_3d[:, :, self.sagittal_idx]
            title = f"Sagittal_Slice_{self.sagittal_idx}"

        # Open file dialog to specify where to save the image
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
        
        if file_path:
            # Save the selected slice as an image
            plt.imsave(file_path, slice_to_save, cmap='gray')
            print(f"Saved {view_choice} slice at {file_path}")


   # Handle mouse click for cursor inspector
    def on_mouse_click(self, event):
        if self.cursor_active:
            # Check if the click occurred in the axial, coronal, or sagittal view
            if event.inaxes == self.axial_ax:
                self.sagittal_idx = int(event.xdata)
                self.coronal_idx = int(event.ydata)
            elif event.inaxes == self.coronal_ax:
                self.sagittal_idx = int(event.xdata)
                self.axial_idx = int(event.ydata)
            elif event.inaxes == self.sagittal_ax:
                self.coronal_idx = int(event.xdata)
                self.axial_idx = int(event.ydata)
            self.update_views()
            # Draw dotted lines at the clicked position
            self.draw_dotted_lines(self.axial_ax, self.sagittal_idx, self.coronal_idx)
            self.draw_dotted_lines(self.coronal_ax, self.sagittal_idx, self.axial_idx)
            self.draw_dotted_lines(self.sagittal_ax, self.coronal_idx, self.axial_idx)

    def on_mouse_scroll(self, event):
        """Zoom in or out based on mouse scroll event."""
        zoom_step = 0.1
        for ax in [self.axial_ax, self.coronal_ax, self.sagittal_ax]:
            if event.inaxes == ax:  # Only zoom the axis where the mouse is located
                xdata, ydata = event.xdata, event.ydata  # Current mouse position in data coordinates

                # Get current axis limits
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()

                # Calculate range of the current view
                x_range = (xlim[1] - xlim[0])
                y_range = (ylim[1] - ylim[0])

                # Zoom in
                if event.button == 'up':
                    scale_factor = 1 - zoom_step
                # Zoom out
                elif event.button == 'down':
                    scale_factor = 1 + zoom_step

                # Adjust x and y limits based on the mouse position and zoom factor
                ax.set_xlim([xdata - (xdata - xlim[0]) * scale_factor,
                             xdata + (xlim[1] - xdata) * scale_factor])
                ax.set_ylim([ydata - (ydata - ylim[0]) * scale_factor,
                             ydata + (ylim[1] - ydata) * scale_factor])

        self.canvas.draw_idle()


# Create Tkinter application
root = tk.Tk()
app = MPRViewerApp(root)
root.mainloop()
