import os
import threading
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, List, Dict, Any


class ColorPicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Image BGR Extractor')

        self.video_frame = tk.Label(self.root)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10)
        self.video_frame.bind("<Button-1>", self.get_bgr_from_video)

        self.threshold_frame = tk.Label(self.root)
        self.threshold_frame.grid(row=0, column=1, padx=10, pady=10)

        self.value_label = tk.Label(self.root, text='')
        self.value_label.grid(row=1, column=0)
        self.instruction_label = tk.Label(self.root, text='Click on 5 points for white')
        self.instruction_label.grid(row=2, column=0, columnspan=2)

        self.btn_take_image = tk.Button(self.root, text="Take Image", command=self.take_image)
        self.btn_take_image.grid(row=3, column=0)

        self.btn_load_image = tk.Button(self.root, text="Load Image", command=self.load_image)
        self.btn_load_image.grid(row=4, column=0)

        self.btn_next_category = tk.Button(self.root, text="Next Category", command=self.next_category)
        self.btn_next_category.grid(row=5, column=0)

        self.btn_done = tk.Button(self.root, text="Done", command=self.save_bounds_to_file)
        self.btn_done.grid(row=6, column=0)

        self.btn_undo = tk.Button(self.root, text="Undo Last Click", command=self.undo_click)
        self.btn_undo.grid(row=7, column=0)

        self.btn_live_video = tk.Button(self.root, text="Live Video", command=self.start_live_video)
        self.btn_live_video.grid(row=8, column=0)

        self.slider = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL, label="Fluctuation")
        self.slider.set(20)
        self.slider.grid(row=3, column=1)

        self.states: List[str] = ["white", "orange", "border", "green", "red"]
        self.stateIndex: int = 0
        self.click_counts: Dict[str, int] = {state: 0 for state in self.states}
        self.variances: Dict[str, int] = {state: 20 for state in self.states}

        self.bgr_values: Dict[str, List[Tuple[int, int, int]]] = {state: [] for state in self.states}

        self.img = None
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
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        cv2.imwrite("image.jpg", frame)
        cap.release()
        self.img = Image.open("image.jpg")
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.video_frame.configure(image=self.photo)
        self.video_frame.image = self.photo
        self.video_frame.bind("<Button-1>", self.get_bgr_from_image)

    def load_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.img = Image.open(filepath)
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.video_frame.configure(image=self.photo)
        self.video_frame.image = self.photo
        self.video_frame.bind("<Button-1>", self.get_bgr_from_image)

    def next_category(self):
        current_state = self.states[self.stateIndex]
        self.variances[current_state] = int(self.slider.get())

        self.stateIndex += 1
        if self.stateIndex == len(self.states):
            self.stateIndex = 0

        self.update_instruction()
        next_state = self.states[self.stateIndex]
        self.slider.set(self.variances[next_state])

    def get_bgr_from_image(self, event):
        if self.img is None:
            return

        x, y = event.x, event.y
        color = self.img.getpixel((x, y))
        if len(color) == 4:
            r, g, b, _ = color
        else:
            r, g, b = color

        self.add_bgr_value(b, g, r)

    def get_bgr_from_video(self, event):
        if self.frame is None:
            return

        x, y = event.x, event.y
        scale_x = self.frame.shape[1] / self.video_frame.winfo_width()
        scale_y = self.frame.shape[0] / self.video_frame.winfo_height()
        x = int(x * scale_x)
        y = int(y * scale_y)
        b, g, r = self.frame[y, x]

        self.add_bgr_value(b, g, r)

    def add_bgr_value(self, b, g, r):
        stateIndex = self.stateIndex
        self.bgr_values[self.states[stateIndex]].append((b, g, r))
        self.click_counts[self.states[stateIndex]] += 1

        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.value_label.config(text=f'BGR: ({b}, {g}, {r}) Hex: {color_hex}', bg=color_hex)

        if self.click_counts[self.states[stateIndex]] == 5:
            self.next_category()

    def undo_click(self):
        stateIndex = self.stateIndex
        if self.click_counts[self.states[self.stateIndex]] > 0:
            self.bgr_values[self.states[self.stateIndex]].pop()
            self.click_counts[self.states[self.stateIndex]] -= 1

    def get_average_bgr(self, bgr_array: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        b_avg = sum([bgr[0] for bgr in bgr_array]) // len(bgr_array)
        g_avg = sum([bgr[1] for bgr in bgr_array]) // len(bgr_array)
        r_avg = sum([bgr[2] for bgr in bgr_array]) // len(bgr_array)
        return (b_avg, g_avg, r_avg)

    def bgr_to_hsv(self, bgr_value: Tuple[int, int, int]) -> Tuple[int, int, int]:
        bgr_array = np.uint8([[list(bgr_value)]])
        hsv_value = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)[0][0]
        return (int(hsv_value[0]), int(hsv_value[1]), int(hsv_value[2]))

    def bounds_dict(self) -> Dict[str, np.ndarray]:
        bounds = {}
        for color, bgr_list in self.bgr_values.items():
            if len(bgr_list) == 5:
                average_bgr = self.get_average_bgr(bgr_list)
                average_hsv = self.bgr_to_hsv(average_bgr)
                h,s,v = average_hsv
                bounds[color] = [h,s,v, self.variances[color]]
        return bounds

    def save_bounds_to_file(self):
        
        overall_dir = os.path.dirname(os.path.dirname(__file__))
        video_analysis_dir = os.path.join(overall_dir, 'video_analysis')
        file_path = os.path.join(video_analysis_dir, 'bounds.txt')

        os.makedirs(video_analysis_dir, exist_ok=True)

        try:
            with open(file_path, 'w') as file:
                for color, bgr_list in self.bgr_values.items():
                    if len(bgr_list) == 0:
                        file.write(f"{color};{0},{0},{0},{0}\n")
                        continue
                    average_bgr = self.get_average_bgr(bgr_list)
                    average_hsv = self.bgr_to_hsv(average_bgr)
                    percentage = self.variances[color]
                    h, s, v = average_hsv
                    file.write(f"{color};{int(h)},{int(s)},{int(v)},{percentage}\n")
                print(f'Bounds saved to {file_path}')
        except IOError as e:
            print(f'Error writing to file: {e}')

    def apply_threshold(self, image: np.ndarray, bounds_dict_entry: np.ndarray) -> np.ndarray:
        
        h,s,v,variance = bounds_dict_entry

        lower = np.array([h - variance, s - variance, v - variance])
        upper = np.array([h + variance, s + variance, v + variance])
        
        #print(variance)
        
        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(image_hsv, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=2)
        return mask

    def start_live_video(self):
        if not self.running:
            self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
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

            if 0 < len(self.bgr_values[self.states[self.stateIndex]]) < 6:
                average_bgr = self.get_average_bgr(self.bgr_values[self.states[self.stateIndex]])
                average_hsv = self.bgr_to_hsv(average_bgr)
                #print(self.variances)
                #print(self.states[self.stateIndex])
                bounds_with_variance = np.array([average_hsv[0], average_hsv[1], average_hsv[2], self.slider.get()])
                thresh = self.apply_threshold(frame, bounds_with_variance)
            else:
                thresh = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = cv2.resize(frame, (500, 500))
            frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
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
