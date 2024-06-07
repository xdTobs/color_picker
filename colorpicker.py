import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, List, Dict


class ColorPicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Image RGB Extractor')

        self.canvas = tk.Canvas(self.root, width=1000, height=600)
        self.canvas.pack()

        self.value_label = tk.Label(self.root, text='')
        self.value_label.pack()

        self.instruction_label = tk.Label(self.root, text='Click on 5 points for white')
        self.instruction_label.pack()

        self.btn_load = tk.Button(self.root, text="Take Image", command=self.take_image)
        self.btn_load.pack()

        self.btn_load = tk.Button(self.root, text="Load Image", command=self.load_image)
        self.btn_load.pack()

        self.btn_load = tk.Button(self.root, text="Next Category", command=self.next_category)
        self.btn_load.pack()

        self.btn_load = tk.Button(self.root, text="Done", command=self.save_bounds_to_file)
        self.btn_load.pack()

        self.btn_undo = tk.Button(self.root, text="Undo Last Click", command=self.undo_click)
        self.btn_undo.pack()

        self.states: List[str] = ["white", "orange", "border", "green", "red"]
        self.stateIndex: int = 0
        self.click_counts: Dict[str, int] = {state: 0 for state in self.states}
        self.fluctuation: Dict[str, int] = {state: 20 for state in self.states}
        self.canvas.bind("<Button-1>", self.get_rgb)

        self.rgb_values: Dict[str, List[Tuple[int, int, int]]] = {state: [] for state in self.states}

        self.img = None

        self.setup_window()

        self.sliders: Dict[str, tk.Scale] = {}
        for state in self.states:
            self.sliders[state] = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                           label=f"{state} fluctuation %")
            self.sliders[state].set(20)
            self.sliders[state].pack()

        self.video_feed = tk.Label(self.root)
        self.video_feed.pack()

        self.update_video_feed()

    def update_instruction(self):
        instructions = [
            'Click on 5 points for white',
            'Click on 5 points for orange',
            'Click on 5 points for border',
            'Click on 5 points for green',
            'Click on 5 points for red'
        ]
        self.instruction_label.config(text=instructions[self.stateIndex])

    def take_image(self):
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        cv2.imwrite("image.jpg", frame)
        cap.release()
        self.img = Image.open("image.jpg")
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def load_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.img = Image.open(filepath)
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def next_category(self):
        if self.click_counts[self.states[self.stateIndex]] < 5:
            print(f"Please click on 5 points for {self.states[self.stateIndex]}")
            return

        self.stateIndex += 1
        if self.stateIndex == len(self.states):
            self.stateIndex = 0
        self.update_instruction()
        print(f"State index: {self.stateIndex}")

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

        self.rgb_values[self.states[stateIndex]].append((r, g, b))
        self.click_counts[self.states[stateIndex]] += 1

        if self.click_counts[self.states[stateIndex]] == 5:
            self.next_category()

    def undo_click(self):
        stateIndex = self.stateIndex
        if self.click_counts[self.states[stateIndex]] > 0:
            self.rgb_values[self.states[stateIndex]].pop()
            self.click_counts[self.states[stateIndex]] -= 1

    def get_average_rgb(self, rgb_array: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        r_avg = sum([rgb[0] for rgb in rgb_array]) // len(rgb_array)
        g_avg = sum([rgb[1] for rgb in rgb_array]) // len(rgb_array)
        b_avg = sum([rgb[2] for rgb in rgb_array]) // len(rgb_array)
        return (r_avg, g_avg, b_avg)

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

    def bounds_dict(self) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        bounds = {}
        for color, rgb_list in self.rgb_values.items():
            if len(rgb_list) == 5:
                average_rgb = self.get_average_rgb(rgb_list)
                percentage = self.sliders[color].get()
                lower, upper = self.get_bounds_bgr(average_rgb, percentage)
                bounds[color] = (lower, upper)
        return bounds

    def save_bounds_to_file(self):
        bounds = self.bounds_dict()

        overall_dir = os.path.dirname(os.path.dirname(__file__))
        video_analysis_dir = os.path.join(overall_dir, 'video_analysis')
        file_path = os.path.join(video_analysis_dir, 'bounds.txt')

        os.makedirs(video_analysis_dir, exist_ok=True)

        try:
            with open(file_path, 'w') as file:
                for color, (lower, upper) in bounds.items():
                    r, g, b = (lower[2] + upper[2]) // 2, (lower[1] + upper[1]) // 2, (lower[0] + upper[0]) // 2
                    percentage = self.sliders[color].get()
                    file.write(f"{color};{r},{g},{b},{percentage}\n")
            print(f'Bounds saved to {file_path}')
        except IOError as e:
            print(f'Error writing to file: {e}')

    def update_video_feed(self):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(frame_gray, 127, 255, cv2.THRESH_BINARY)
            frame_pil = Image.fromarray(thresh)
            frame_pil.thumbnail((500, 500))
            frame_tk = ImageTk.PhotoImage(frame_pil)
            self.video_feed.configure(image=frame_tk)
            self.video_feed.image = frame_tk

        self.root.after(30, self.update_video_feed)

    def setup_window(self):
        self.root.mainloop()


if __name__ == '__main__':
    colorpicker = ColorPicker()
    print("Done")
