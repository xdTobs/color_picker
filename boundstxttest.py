import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from typing import Tuple, List, Dict
from PIL import Image, ImageTk

def read_bounds_file(file_path: str) -> Dict[str, Tuple[int, int, int, int]]:
    bounds = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split(';')
            if len(parts) != 2:
                continue
            color, values = parts
            h, s, v, threshold = map(int, values.split(','))
            bounds[color] = (h, s, v, threshold)
    return bounds

def create_color_image(hsv_value: Tuple[int, int, int], size: Tuple[int, int]) -> np.ndarray:
    h, s, v = hsv_value
    hsv_image = np.full((size[1], size[0], 3), (h, s, v), dtype=np.uint8)
    bgr_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    return bgr_image

def display_color_images(bounds: Dict[str, Tuple[int, int, int, int]]):
    root = tk.Tk()
    root.title("HSV Color Display")

    for color, (h, s, v, threshold) in bounds.items():
        bgr_image = create_color_image((h, s, v), (100, 100))
        bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(image=Image.fromarray(bgr_image))

        label = tk.Label(root, text=f"{color}: HSV({h}, {s}, {v}), Threshold: {threshold}")
        label.pack()
        img_label = tk.Label(root, image=img)
        img_label.image = img
        img_label.pack()

    root.mainloop()

if __name__ == "__main__":
    file_path = filedialog.askopenfilename(title="Select bounds.txt file", filetypes=[("Text files", "*.txt")])
    if file_path:
        bounds = read_bounds_file(file_path)
        display_color_images(bounds)
