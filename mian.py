import cv2
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from tkinter import ttk
import threading
import webbrowser


def generate_name_video(name_file_path, font_path, output_path, fps, frame_size, interval,
                        text_size, text_color, bg_type, bg_value, progress_var):
    try:
        with open(name_file_path, 'r', encoding='utf-8') as f:
            names = f.read().splitlines()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

        font = ImageFont.truetype(font_path, text_size)

        frames_per_name = int(interval * fps)
        total_frames = len(names) * frames_per_name
        current_frame = 0

        for name in names:
            if bg_type == '纯色':
                img = Image.new('RGB', frame_size, color=bg_value)
            elif bg_type == '图片':
                try:
                    bg_img = Image.open(bg_value).resize(frame_size)
                    img = bg_img.copy()
                except Exception:
                    img = Image.new('RGB', frame_size, color=(0, 0, 0))
            elif bg_type == '视频':
                cap = cv2.VideoCapture(bg_value)
                ret, bg_frame = cap.read()
                if ret:
                    bg_frame = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(bg_frame)
                else:
                    img = Image.new('RGB', frame_size, color=(0, 0, 0))
                cap.release()

            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (frame_size[0] - text_width) // 2
            text_y = (frame_size[1] - text_height) // 2

            draw.text((text_x, text_y), name, font=font, fill=text_color)

            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            for _ in range(frames_per_name):
                out.write(img_cv)
                current_frame += 1
                progress = (current_frame / total_frames) * 100
                progress_var.set(progress)
                root.update_idletasks()

        out.release()
        messagebox.showinfo("成功", "视频生成成功！")
    except Exception as e:
        messagebox.showerror("错误", f"视频生成失败：{str(e)}")
    finally:
        generate_button.config(state=tk.NORMAL)
        progress_bar.stop()


def select_font_file():
    font_path = filedialog.askopenfilename(filetypes=[("Font files", "*.ttf;*.otf")])
    if font_path:
        font_entry.delete(0, tk.END)
        font_entry.insert(0, font_path)


def select_name_file():
    name_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if name_path:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, name_path)


def select_output_path():
    output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
    if output_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, output_path)


def select_bg_file():
    bg_type = bg_type_var.get()
    if bg_type == '图片':
        bg_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    elif bg_type == '视频':
        bg_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
    else:
        return
    if bg_path:
        bg_entry.delete(0, tk.END)
        bg_entry.insert(0, bg_path)


def choose_text_color():
    color = colorchooser.askcolor()[1]
    if color:
        text_color_entry.delete(0, tk.END)
        text_color_entry.insert(0, color)


def toggle_advanced_options():
    if advanced_frame.winfo_ismapped():
        advanced_frame.grid_forget()
        advanced_button.config(text="展开高级选项")
    else:
        advanced_frame.grid(row=7, column=0, columnspan=3, pady=10)
        advanced_button.config(text="折叠高级选项")


def generate_video():
    font_path = font_entry.get()
    name_file_path = name_entry.get()
    output_path = output_entry.get()
    fps_str = fps_entry.get()
    resolution_str = resolution_entry.get()
    interval_str = interval_entry.get()
    text_size_str = text_size_entry.get()
    text_color = text_color_entry.get()
    bg_type = bg_type_var.get()
    bg_value = bg_entry.get()

    if not all([font_path, name_file_path, output_path, fps_str, resolution_str, interval_str,
                text_size_str, text_color]):
        messagebox.showerror("输入错误", "请确保所有输入框都有内容！")
        return

    try:
        fps = int(fps_str)
        width, height = map(int, resolution_str.split(','))
        interval = float(interval_str)
        text_size = int(text_size_str)
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的数字！")
        return

    if not os.path.exists(font_path) or not os.path.exists(name_file_path):
        messagebox.showerror("文件不存在", "字体文件或姓名文件不存在，请检查路径！")
        return

    if bg_type in ['图片', '视频'] and not os.path.exists(bg_value):
        messagebox.showerror("文件不存在", f"{bg_type}文件不存在，请检查路径！")
        return

    generate_button.config(state=tk.DISABLED)
    progress_var.set(0)
    progress_bar.start()
    thread = threading.Thread(target=generate_name_video, args=(
        name_file_path, font_path, output_path, fps, (width, height), interval,
        text_size, text_color, bg_type, bg_value, progress_var))
    thread.start()


def open_github():
    webbrowser.open("https://github.com")


root = tk.Tk()
root.title("名字闪烁视频生成器")

tk.Label(root, text="字体文件位置:").grid(row=0, column=0, padx=10, pady=5)
font_entry = tk.Entry(root, width=50)
font_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="选择字体文件", command=select_font_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="姓名文件（txt）位置:").grid(row=1, column=0, padx=10, pady=5)
name_entry = tk.Entry(root, width=50)
name_entry.grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="选择姓名文件", command=select_name_file).grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="FPS:").grid(row=2, column=0, padx=10, pady=5)
fps_entry = tk.Entry(root, width=10)
fps_entry.insert(0, "30")
fps_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="像素 (宽,高):").grid(row=3, column=0, padx=10, pady=5)
resolution_entry = tk.Entry(root, width=20)
resolution_entry.insert(0, "192,108")
resolution_entry.grid(row=3, column=1, padx=10, pady=5)

tk.Label(root, text="名字停留时间 (秒):").grid(row=4, column=0, padx=10, pady=5)
interval_entry = tk.Entry(root, width=10)
interval_entry.insert(0, "0.2")
interval_entry.grid(row=4, column=1, padx=10, pady=5)

tk.Label(root, text="视频输出路径:").grid(row=5, column=0, padx=10, pady=5)
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=5, column=1, padx=10, pady=5)
tk.Button(root, text="选择输出路径", command=select_output_path).grid(row=5, column=2, padx=10, pady=5)

advanced_button = tk.Button(root, text="展开高级选项", command=toggle_advanced_options)
advanced_button.grid(row=6, column=1, padx=10, pady=10)

advanced_frame = tk.Frame(root)

tk.Label(advanced_frame, text="文字大小:").grid(row=0, column=0, padx=10, pady=5)
text_size_entry = tk.Entry(advanced_frame, width=10)
text_size_entry.insert(0, "70")
text_size_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(advanced_frame, text="文字颜色:").grid(row=1, column=0, padx=10, pady=5)
text_color_entry = tk.Entry(advanced_frame, width=10)
text_color_entry.insert(0, "#ffffff")
text_color_entry.grid(row=1, column=1, padx=10, pady=5)
tk.Button(advanced_frame, text="选择颜色", command=choose_text_color).grid(row=1, column=2, padx=10, pady=5)

tk.Label(advanced_frame, text="背景类型:").grid(row=2, column=0, padx=10, pady=5)
bg_type_var = tk.StringVar()
bg_type_var.set("纯色")
bg_type_menu = ttk.Combobox(advanced_frame, textvariable=bg_type_var, values=["纯色", "图片", "视频（存在bug，有能力的解决）"])
bg_type_menu.grid(row=2, column=1, padx=10, pady=5)

tk.Label(advanced_frame, text="背景值:").grid(row=3, column=0, padx=10, pady=5)
bg_entry = tk.Entry(advanced_frame, width=50)
bg_entry.insert(0, "#000000")
bg_entry.grid(row=3, column=1, padx=10, pady=5)
tk.Button(advanced_frame, text="选择文件", command=select_bg_file).grid(row=3, column=2, padx=10, pady=5)

generate_button = tk.Button(root, text="生成视频", command=generate_video)
generate_button.grid(row=8, column=1, padx=10, pady=20)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# 添加右下角版权信息
copyright_label = tk.Label(root, text="By:Lun.", fg="red")
copyright_label.grid(row=10, column=2, sticky="se", padx=10, pady=10)

# 添加左下角GitHub链接
github_link = tk.Label(root, text="GitHub", fg="blue", cursor="hand2")
github_link.grid(row=10, column=0, sticky="sw", padx=10, pady=10)
github_link.bind("<Button-1>", lambda e: open_github())

root.mainloop()
    