import os
import threading
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

        self.canvas = tk.Canvas(self.root, width=1000, height=400)
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

        self.btn_live_video = tk.Button(self.root, text="Live Video", command=self.start_live_video)
        self.btn_live_video.pack()

        self.states: List[str] = ["white", "orange", "border", "green", "red"]
        self.stateIndex: int = 0
        self.click_counts: Dict[str, int] = {state: 0 for state in self.states}
        self.fluctuation = 20
        self.canvas.bind("<Button-1>", self.get_rgb_from_image)

        self.rgb_values: Dict[str, List[Tuple[int, int, int]]] = {state: [] for state in self.states}

        self.img = None

        self.video_frame = tk.Label(self.root)
        self.video_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.video_frame.bind("<Button-1>", self.get_rgb_from_video)

        self.threshold_frame = tk.Label(self.root)
        self.threshold_frame.pack(side=tk.LEFT, padx=10, pady=10)


        self.slider = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL, label="Fluctuation %")
        self.slider.set(20)
        self.slider.pack()

        self.cap = None
        self.frame = None
        self.running = False

        self.setup_window()

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
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
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

    def get_rgb_from_image(self, event):
        if self.img is None:
            return

        x, y = event.x, event.y
        color = self.img.getpixel((x, y))
        if len(color) == 4:
            r, g, b, _ = color
        else:
            r, g, b = color

        self.add_rgb_value(r, g, b)

    def get_rgb_from_video(self, event):
        if self.frame is None:
            return

        x, y = event.x, event.y
        scale_x = self.frame.shape[1] / self.video_frame.winfo_width()
        scale_y = self.frame.shape[0] / self.video_frame.winfo_height()
        x = int(x * scale_x)
        y = int(y * scale_y)
        b, g, r = self.frame[y, x]

        self.add_rgb_value(r, g, b)

    def add_rgb_value(self, r, g, b):
        stateIndex = self.stateIndex
        self.rgb_values[self.states[stateIndex]].append((r, g, b))
        self.click_counts[self.states[stateIndex]] += 1

        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.value_label.config(text=f'RGB: ({r}, {g}, {b}) Hex: {color_hex}', bg=color_hex)

        if self.click_counts[self.states[stateIndex]] == 5:
            self.next_category()

    def undo_click(self):
        stateIndex = self.stateIndex
        if self.click_counts[self.states[self.stateIndex]] > 0:
            self.rgb_values[self.states[self.stateIndex]].pop()
            self.click_counts[self.states[self.stateIndex]] -= 1

    def get_average_rgb(self, rgb_array: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        r_avg = sum([rgb[0] for rgb in rgb_array]) // len(rgb_array)
        g_avg = sum([rgb[1] for rgb in rgb_array]) // len(rgb_array)
        b_avg = sum([rgb[2] for rgb in rgb_array]) // len(rgb_array)
        return (r_avg, g_avg, b_avg)

    def get_bounds_bgr(self, rgb_value: Tuple[int, int, int], percentage: int) -> np.ndarray:
        r, g, b = rgb_value
        bounds_with_variance = np.array([b, g, r, percentage])
        return bounds_with_variance

    def bounds_dict(self) -> Dict[str, np.ndarray]:
        bounds = {}
        for color, rgb_list in self.rgb_values.items():
            if len(rgb_list) == 5:
                average_rgb = self.get_average_rgb(rgb_list)
                bounds[color] = self.get_bounds_bgr(average_rgb, self.slider.get())
        return bounds

    def save_bounds_to_file(self):
        bounds = self.bounds_dict()

        overall_dir = os.path.dirname(os.path.dirname(__file__))
        video_analysis_dir = os.path.join(overall_dir, 'video_analysis')
        file_path = os.path.join(video_analysis_dir, 'bounds.txt')

        os.makedirs(video_analysis_dir, exist_ok=True)

        try:
            with open(file_path, 'w') as file:
                for color, bounds_array in bounds.items():
                    lower, upper = bounds_array[:3], bounds_array[3:]
                    r, g, b = (lower[2] + upper[2]) // 2, (lower[1] + upper[1]) // 2, (lower[0] + upper[0]) // 2
                    percentage = self.slider.get()
                    file.write(f"{color};{r},{g},{b},{percentage}%\n")
            print(f'Bounds saved to {file_path}')
        except IOError as e:
            print(f'Error writing to file: {e}')

    def apply_threshold(self, image: np.ndarray, bounds_dict_entry: np.ndarray) -> np.ndarray:
        bounds = bounds_dict_entry[:3]
        variance = bounds_dict_entry[3]
        print(f"Bounds: {bounds}, variance: {variance}")
        lower = np.clip(bounds - variance, 0, 255)
        upper = np.clip(bounds + variance, 0, 255)
        print(lower, upper)

        mask = cv2.inRange(image, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=2)
        return mask

    def start_live_video(self):
        if not self.running:
            self.video_frame.pack()
            self.threshold_frame.pack()
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.running = True
            threading.Thread(target=self.update_video_feed, daemon=True).start()

    def update_video_feed(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            self.frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if 0 < len(self.rgb_values[self.states[self.stateIndex]]) < 6:
                average_rgb = self.get_average_rgb(self.rgb_values[self.states[self.stateIndex]])
                print(f"testitest{average_rgb}")
                print(f"Slider value: {self.slider.get()}")
                bounds_with_variance = self.get_bounds_bgr(average_rgb, self.slider.get())
                thresh = self.apply_threshold(frame_rgb, bounds_with_variance)
            else:
                thresh = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame_rgb = cv2.resize(frame_rgb, (500, 500))
            frame_pil = Image.fromarray(frame_rgb)
            frame_tk = ImageTk.PhotoImage(frame_pil)
            self.video_frame.configure(image=frame_tk)
            self.video_frame.image = frame_tk

            thresh = cv2.resize(thresh, (500, 500))
            thresh_pil = Image.fromarray(thresh)
            thresh_tk = ImageTk.PhotoImage(thresh_pil)
            self.threshold_frame.configure(image=thresh_tk)
            self.threshold_frame.image = thresh_tk

            self.root.update_idletasks()

    def setup_window(self):
        self.root.mainloop()


if __name__ == '__main__':
    colorpicker = ColorPicker()
    print("Done")
