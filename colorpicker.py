import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, List, Dict


class ColorPicker:
    def __init__(self):
        root = tk.Tk()
        root.title('Image RGB Extractor')
        self.root = root
        self.canvas = tk.Canvas(root, width=1000, height=600)
        self.canvas.pack()
        self.value_label = tk.Label(root, text='')
        self.value_label.pack()
        self.instruction_label = tk.Label(root, text='Click on a white ball')
        self.instruction_label.pack()

        self.btn_load = tk.Button(root, text="Take Image", command=self.take_image)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Load Image", command=self.load_image)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Next Category", command=self.next_category)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Done", command=self.save_bounds_to_file)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Load Standards", command=self.load_standards)
        self.btn_load.pack()
        self.states: List[str] = ["white", "orange", "border", "green", "red"]
        self.stateIndex: int = 0
        self.load_standard: bool = False
        self.canvas.bind("<Button-1>", self.get_rgb)
        self.canvas.bind("<Button-3>", self.undo_click)

        self.rgb_values: Dict[str, Tuple[int, int, int]] = {state: None for state in self.states}

        self.click_count = 0
        self.img = None

        self.setup_window()

    def load_standards(self):
        self.load_standard = True

    def take_image(self):
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        cv2.imwrite("image.jpg", frame)
        cap.release()
        self.img = Image.open("image.jpg")
        self.img.thumbnail((1024, 1500))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def next_category(self):
        self.stateIndex += 1
        if self.stateIndex == 5:
            self.stateIndex = 0
        self.update_instruction()
        print(f"State index: {self.stateIndex}")

    def update_instruction(self):
        instructions = [
            'Click on a white ball',
            'Click on an orange ball',
            'Click on a border wall',
            'Click on a green circle',
            'Click on a red circle'
        ]
        self.instruction_label.config(text=instructions[self.stateIndex])

    def load_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.img = Image.open(filepath)
        self.img.thumbnail((1024, 1500))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def get_rgb(self, event):
        stateIndex = self.stateIndex
        x, y = event.x, event.y
        size = 10
        line_width = 3

        if self.img is None:
            return

        self.canvas.create_line(x - size, y - size, x + size, y + size, fill='red', width=line_width)
        self.canvas.create_line(x + size, y - size, x - size, y + size, fill='red', width=line_width)

        color = self.img.getpixel((event.x, event.y))
        if len(color) == 4:
            r, g, b, _ = color
        else:
            r, g, b = color

        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.value_label.config(text=f'RGB: ({r}, {g}, {b}) Hex: {color_hex}', bg=color_hex)

        self.rgb_values[self.states[stateIndex]] = (r, g, b)
        self.next_category()

    def undo_click(self):
        stateIndex = self.stateIndex
        self.rgb_values[self.states[stateIndex]] = None

    def get_bounds_bgr(self, rgb_value: Tuple[int, int, int], percentage: float) -> Tuple[np.array, np.array]:
        r, g, b = rgb_value

        fluctuation = percentage / 100.0
        r_min, r_max = r * (1 - fluctuation), r * (1 + fluctuation)
        g_min, g_max = g * (1 - fluctuation), g * (1 + fluctuation)
        b_min, b_max = b * (1 - fluctuation), b * (1 + fluctuation)

        r_min, r_max = round(max(0, min(255, r_min))), round(max(0, min(255, r_max)))
        g_min, g_max = round(max(0, min(255, g_min))), round(max(0, min(255, g_max)))
        b_min, b_max = round(max(0, min(255, b_min))), round(max(0, min(255, b_max)))

        lower = np.array([b_min, g_min, r_min])
        upper = np.array([b_max, g_max, r_max])

        return lower, upper

    def bounds_dict(self, percentage: float) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        bounds = {}
        for color, rgb_value in self.rgb_values.items():
            if rgb_value:
                lower, upper = self.get_bounds_bgr(rgb_value, percentage)
                bounds[color] = (lower, upper)
        return bounds

    def save_bounds_to_file(self):
        percentage = 20
        bounds = self.bounds_dict(percentage)

        overall_dir = os.path.dirname(os.path.dirname(__file__))
        video_analysis_dir = os.path.join(overall_dir, 'video_analysis')
        file_path = os.path.join(video_analysis_dir, 'bounds.txt')

        os.makedirs(video_analysis_dir, exist_ok=True)

        # Write to the text file
        try:
            with open(file_path, 'w') as file:
                for color, (lower, upper) in bounds.items():
                    r, g, b = (lower[2] + upper[2]) // 2, (lower[1] + upper[1]) // 2, (lower[0] + upper[0]) // 2
                    file.write(f"{color};{r},{g},{b},{percentage}%\n")
            print(f'Bounds saved to {file_path}')
        except IOError as e:
            print(f'Error writing to file: {e}')

    def setup_window(self):
        undo_button = tk.Button(self.root, text="Undo last click", command=self.undo_click)
        undo_button.pack()
        self.root.mainloop()


if __name__ == '__main__':
    colorpicker = ColorPicker()
    print("Done")
