import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

# Fixed rectangle size
rect_width = 360
rect_height = 240

def get_interactive_coordinates(image_path):
    # Remove the offscreen setting to allow display
    if "QT_QPA_PLATFORM" in os.environ:
        del os.environ["QT_QPA_PLATFORM"]
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from '{image_path}'.")
        return None
    
    # Resize if needed
    if image.shape[1] != 1920 or image.shape[0] != 1080:
        image = cv2.resize(image, (1920, 1080))
    
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rect_start = None
    rect_end = None
    drawing = False

    def on_click(event):
        nonlocal rect_start, drawing
        if event.button == 1:  # Left mouse button
            rect_start = (int(event.xdata - rect_width//2), int(event.ydata - rect_height//2))
            drawing = True
            update_display()

    def on_move(event):
        nonlocal rect_start, drawing
        if drawing and event.inaxes and rect_start:
            update_display()

    def on_release(event):
        nonlocal drawing
        drawing = False

    def update_display():
        img_copy = img_rgb.copy()
        if rect_start:
            # Ensure coordinates are within image bounds
            x = max(0, min(rect_start[0], img_rgb.shape[1] - rect_width))
            y = max(0, min(rect_start[1], img_rgb.shape[0] - rect_height))
            
            cv2.rectangle(img_copy, 
                          (x, y), 
                          (x + rect_width, y + rect_height),
                          (255, 0, 0), 2)
        plt.gca().images[0].set_array(img_copy)
        plt.draw()

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.imshow(img_rgb)
    ax.axis('off')
    
    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('motion_notify_event', on_move)
    fig.canvas.mpl_connect('button_release_event', on_release)
    
    plt.show()
    
    # After window is closed, return the coordinates
    if rect_start:
        # Final bounds check
        x = max(0, min(rect_start[0], img_rgb.shape[1] - rect_width))
        y = max(0, min(rect_start[1], img_rgb.shape[0] - rect_height))
        return {'x': x, 'y': y}
    return None