import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple,List,Dict

class ColorPicker:
    def __init__(self):
        root = tk.Tk()
        # root.state('zoomed')
        root.title('Image RGB Extractor')
        self.root = root
        self.canvas = tk.Canvas(root, width=1000, height=400)
        self.canvas.pack()
        self.value_label = tk.Label(root, text='')
        self.value_label.pack()
        self.instruction_label = tk.Label(root, text='Click on at least 3 white balls')
        self.instruction_label.pack()
        
        self.btn_load = tk.Button(root, text="Take Image", command=self.take_image)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Load Image", command=self.load_image)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Next Category", command=self.next_category)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Done", command=self.bounds_dict)
        self.btn_load.pack()
        self.btn_load = tk.Button(root, text="Load Standards", command=self.load_standards)
        self.btn_load.pack()
        self.states : List[str] = ["white", "orange", "border", "green", "red"]
        self.stateIndex : int = 0
        self.load_standard : bool = False
        self.canvas.bind("<Button-1>", self.get_rgb)
        self.canvas.bind("<Button-3>", self.undo_click)
        
        self.rgb_values : Dict[str, List[Tuple[int,int,int]]] = {}
        for state in self.states:
            self.rgb_values[state] = []
        
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
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        bgr_img = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2BGR)
        #cv2.imshow('BGR Image', bgr_img)

    def next_category(self):
        self.stateIndex += 1
        if self.stateIndex == 5:
            self.stateIndex = 0
        if self.stateIndex == 0:
            self.instruction_label.config(text = 'Click on at least 3 white balls')
        if self.stateIndex == 1:
            self.instruction_label.config(text = 'Click on at least 3 orange balls')
        if self.stateIndex == 2:
            self.instruction_label.config(text = 'Click on at least 3 border walls')
        if self.stateIndex == 3:
            self.instruction_label.config(text = 'Click on at least 3 green balls')
        if self.stateIndex == 4:
            self.instruction_label.config(text = 'Click on at least 3 red balls')
        print(f"State index: {self.stateIndex}")
        
    def load_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.img = Image.open(filepath)
        self.img.thumbnail((1024, 1024))
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        bgr_img = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2BGR)
        #cv2.imshow('BGR Image', bgr_img)
    
    def get_rgb(self, event):
        stateIndex = self.stateIndex
        x, y = event.x, event.y
        size = 10 
        line_width = 3

        if self.img is None:
            return
        
        self.canvas.create_line(x - size, y - size, x + size, y + size, fill='red',width=line_width)
        self.canvas.create_line(x + size, y - size, x - size, y + size, fill='red',width=line_width)
        
        color = self.img.getpixel((event.x, event.y))
        if len(color) == 4:
            r, g, b, _ = color
        else:
            r, g, b = color

        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.value_label.config(text=f'RGB: ({r}, {g}, {b}) Hex: {color_hex}', bg=color_hex)
        
        colorArray = self.rgb_values[self.states[stateIndex]]
        colorArray.append((r, g, b))

        

    def undo_click(self):
        stateIndex = self.stateIndex
        rgb_array = self.rgb_values[self.states[stateIndex]] 
        if len(rgb_array) == 0:
            return
        rgb_array.pop()


    def get_rgb_values(self) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int]]]:
        return self.white_balls_array, self.orange_balls_array
    

    def get_bounds_bgr(self,rgb_array: List[Tuple[int, int, int]], color: str) -> Tuple[np.array, np.array]:

        standard_colors = {
        'white': (np.array([146, 171, 191]), np.array([255, 255, 255])),
        'orange': (np.array([148, 192, 202]), np.array([255, 255, 255])),
        'green': (np.array([143, 174, 152]), np.array([224, 255, 233])),
        'red': (np.array([0, 0, 189]), np.array([4, 2, 255])),
        'border': (np.array([0, 14, 168]), np.array([30, 62, 255]))
        }

        if len(rgb_array) < 3:
            return standard_colors[color]

        r_values, g_values, b_values = zip(*rgb_array)

        r_min, r_max = min(r_values), max(r_values)
        g_min, g_max = min(g_values), max(g_values)
        b_min, b_max = min(b_values), max(b_values)

        r_min, r_max = r_min * 0.80, r_max * 1.20
        g_min, g_max = g_min * 0.80, g_max * 1.20
        b_min, b_max = b_min * 0.80, b_max * 1.20

        r_min, r_max = round(max(0, min(255, r_min))), round(max(0, min(255, r_max)))
        g_min, g_max = round(max(0, min(255, g_min))), round(max(0, min(255, g_max)))
        b_min, b_max = round(max(0, min(255, b_min))), round(max(0, min(255, b_max)))

        lower = np.array([b_min, g_min, r_min ])
        upper = np.array([b_max, g_max, r_max ])

        return lower, upper

    def bounds_dict(self) -> Dict[str, np.ndarray]:
        if self.load_standard == True:
            colors = {
                'white_lower': np.array([146, 171, 191]),
                'orange_lower': np.array([148, 192, 202]),
                'green_lower': np.array([143, 174, 152]),
                'red_lower': np.array([0, 0, 189]),
                'border_lower': np.array([0, 14, 168]),
                'white_upper': np.array([255, 255, 255]),
                'orange_upper': np.array([255, 255, 255]),
                'green_upper': np.array([224, 255, 233]),
                'red_upper': np.array([4, 2, 255]),
                'border_upper': np.array([30, 62, 255])
            }
            return colors
        self.white_lower, self.white_upper = self.get_bounds_bgr(self.rgb_values["white"], "white")
        self.orange_lower, self.orange_upper = self.get_bounds_bgr(self.rgb_values["orange"], "orange")
        self.green_bot_lower, self.green_bot_upper = self.get_bounds_bgr(self.rgb_values["green"], "green")
        self.red_bot_lower, self.red_bot_upper = self.get_bounds_bgr(self.rgb_values["red"], "red")
        self.border_lower, self.border_upper = self.get_bounds_bgr(self.rgb_values["border"], "border")
        
        return {
            "white_lower": self.white_lower,
            "white_upper": self.white_upper,
            "orange_lower": self.orange_lower,
            "orange_upper": self.orange_upper,
            "green_lower": self.green_bot_lower,
            "green_upper": self.green_bot_upper,
            "red_lower": self.red_bot_lower,
            "red_upper": self.red_bot_upper,
            "border_lower": self.border_lower,
            "border_upper": self.border_upper
        }

    def setup_window(self):

        undo_button = tk.Button(self.root, text="Undo last click", command=self.undo_click) # Man kan ikke se denne knap
        undo_button.pack()

        self.root.mainloop()
        
if __name__ == '__main__':

    colorpicker = ColorPicker()
    bounds = colorpicker.bounds_dict()
    print(bounds)
    print("Done")
