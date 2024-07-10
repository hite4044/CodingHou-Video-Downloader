import tkinter as tk
from tkinter import ttk
from os import mkdir, path
from threading import Lock, Thread
from tkinter.filedialog import askdirectory

from core import download


class LabelEntry(ttk.Frame):
    def __init__(self, parent, text):
        super().__init__(parent)
        ttk.Label(self, text=text).pack(side=tk.LEFT)
        self.entry = ttk.Entry(self, width=50)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def set(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def get(self):
        return self.entry.get()


class ProgressBar(tk.Canvas):
    def __init__(self, master: tk.Misc, text: str = "0%"):
        super(ProgressBar, self).__init__(master, height=26)

        class Color:
            def __init__(self):
                self.success = "#06B025"
                self.fg = "#000000"
                self.border = "#BCBCBC"

        self.color = Color()
        self.bind("<Configure>", self.redraw)
        self.percentage = 0
        self.text = text
        self.redraw_lock = Lock()
        self.now_elements = []
        self.last_elements = []

        self.text_id = 0
        self.redraw()

    def redraw(self, *_):
        with self.redraw_lock:
            self.now_elements.clear()
            width = self.winfo_width()
            bar_x = int((width - 4) * self.percentage)
            if bar_x == 1:
                self.now_elements.append(self.create_line(1, 1, 1, 26, fill=self.color.success))
            elif bar_x > 1:
                self.now_elements.append(self.create_rectangle(1, 1, bar_x, 26 - 2, fill=self.color.success,
                                                               outline=self.color.success))

            self.now_elements.append(self.create_rectangle(2, 2, width - 2, 26 - 2, outline=self.color.border))
            self.text_id = self.create_text(width // 2, 13, text=self.text, fill=self.color.fg)
            self.now_elements.append(self.text_id)

            if self.last_elements:
                self.delete(*self.last_elements)
            self.last_elements = self.now_elements.copy()

    def set_percentage(self, percentage: float):
        self.percentage = percentage
        self.text = str(round(percentage * 100, 2)) + "%"
        self.redraw()


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("编程侯老师网站视频下载器")
        tk.Label(self, text="仅供学习使用, 严禁用于非法用途!", fg="red", font=("微软雅黑", 24)).pack(anchor=tk.NW)
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        self.inp = LabelEntry(self, "课程ID: ")
        self.out = LabelEntry(self, "输出目录: ")
        self.out_chs = ttk.Button(self.out, text="选择目录", command=self.choose_dir)
        self.inp.pack(pady=10, anchor=tk.NW)
        self.out.pack(pady=10, anchor=tk.NW)
        self.out_chs.pack(side=tk.LEFT)
        self.start_b = ttk.Button(self, text="开始下载", command=self.start_download, width=20)
        self.start_b.pack(pady=10)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.pack(fill=tk.X)

    def choose_dir(self):
        dir_ = askdirectory(parent=self)
        if dir_:
            self.out.set(dir_)

    def update_progress_bar(self, vaule):
        self.progress_bar.set_percentage(vaule)

    def start_download(self):
        self.start_b.configure(state=tk.DISABLED)
        inp = self.inp.get()
        out = self.out.get()
        if not path.isdir(out):
            mkdir(out)
        Thread(target=download, args=(int(inp), out, self.update_progress_bar), daemon=True).start()


if __name__ == "__main__":
    GUI().mainloop()
