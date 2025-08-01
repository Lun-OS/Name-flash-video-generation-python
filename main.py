import cv2
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from tkinter import ttk
import threading
import random
import webbrowser
import ctypes
from ctypes import wintypes
import sys

# 确保中文显示正常
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，避免tkinter冲突

# 检测系统是否为Windows 10/11
is_windows = sys.platform.startswith('win32')

# Win11毛玻璃效果相关设置
if is_windows:
    try:
        # 加载Windows API用于毛玻璃效果
        user32 = ctypes.WinDLL('user32')
        dwmapi = ctypes.WinDLL('dwmapi')
        
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWA_MICA_EFFECT = 1029
        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        DWMSBT_MAINWINDOW = 2  # Mica效果
        
        # 设置窗口圆角
        def set_window_corner(hwnd, preference):
            return dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(preference)),
                ctypes.sizeof(ctypes.c_int)
            )
        
        # 设置窗口毛玻璃效果
        def enable_mica_effect(hwnd):
            return dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_MICA_EFFECT,
                ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)),
                ctypes.sizeof(ctypes.c_int)
            )
        
        # 获取系统主题（亮/暗）
        def is_dark_mode():
            try:
                key = ctypes.c_void_p()
                ctypes.WinDLL("advapi32").RegOpenKeyExW(
                    ctypes.c_void_p(0x80000002),  # HKEY_CURRENT_USER
                    "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                    0,
                    0x20019,  # KEY_READ | KEY_WOW64_32KEY
                    ctypes.byref(key)
                )
                
                value = ctypes.c_int()
                size = ctypes.c_uint(4)
                ctypes.WinDLL("advapi32").RegQueryValueExW(
                    key,
                    "AppsUseLightTheme",
                    None,
                    None,
                    ctypes.byref(value),
                    ctypes.byref(size)
                )
                ctypes.WinDLL("advapi32").RegCloseKey(key)
                return value.value == 0  # 0表示暗模式，1表示亮模式
            except:
                return False
    except:
        # 异常处理
        def set_window_corner(hwnd, preference):
            pass
        
        def enable_mica_effect(hwnd):
            pass
        
        def is_dark_mode():
            return False
else:
    # 非Windows系统
    def set_window_corner(hwnd, preference):
        pass
    
    def enable_mica_effect(hwnd):
        pass
    
    def is_dark_mode():
        return False


def generate_name_video(name_file_path, font_path, output_path, fps, frame_size, interval,
                        text_size, text_color, bg_type, bg_value, progress_var, root):
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
                    bg_img = Image.open(bg_value)
                    # 确保图片按比例调整大小并填充整个帧
                    bg_img = bg_img.resize(frame_size, Image.LANCZOS)
                    img = bg_img.copy()
                except Exception as e:
                    print(f"加载图片失败: {e}")
                    img = Image.new('RGB', frame_size, color=(0, 0, 0))
            elif bg_type == '视频（循环播放）':
                cap = cv2.VideoCapture(bg_value)
                # 获取视频总帧数
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if frame_count > 0:
                    # 为当前名字随机选择一个起始帧
                    start_frame = random.randint(0, frame_count - 1)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                    ret, bg_frame = cap.read()
                    if not ret:
                        # 如果读取失败，尝试读取第一帧
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, bg_frame = cap.read()
                    if ret:
                        bg_frame = cv2.resize(bg_frame, frame_size)
                        bg_frame = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(bg_frame)
                    else:
                        img = Image.new('RGB', frame_size, color=(0, 0, 0))
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
    elif bg_type == '视频（存在bug，有能力的解决）':
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


def choose_bg_color():
    # 确保只有在纯色背景模式下才打开颜色选择器
    if bg_type_var.get() == '纯色':
        color = colorchooser.askcolor()[1]
        if color:
            bg_entry.delete(0, tk.END)
            bg_entry.insert(0, color)


def toggle_advanced_options():
    if advanced_frame.winfo_ismapped():
        advanced_frame.grid_forget()
        advanced_button.config(text="展开高级选项")
    else:
        advanced_frame.grid(row=7, column=0, columnspan=3, pady=10, sticky="nsew")
        advanced_button.config(text="折叠高级选项")


def generate_video():
    font_path = font_entry.get()
    name_file_path = name_entry.get()
    output_path = output_entry.get()
    fps_str = fps_entry.get()
    width_str = width_entry.get()
    height_str = height_entry.get()
    interval_str = interval_entry.get()
    text_size_str = text_size_entry.get()
    text_color = text_color_entry.get()
    bg_type = bg_type_var.get()
    bg_value = bg_entry.get()

    if not all([font_path, name_file_path, output_path, fps_str, width_str, height_str, interval_str,
                text_size_str, text_color]):
        messagebox.showerror("输入错误", "请确保所有输入框都有内容！")
        return

    try:
        fps = int(fps_str)
        width = int(width_str)
        height = int(height_str)
        interval = float(interval_str)
        text_size = int(text_size_str)
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的数字！")
        return

    if not os.path.exists(font_path) or not os.path.exists(name_file_path):
        messagebox.showerror("文件不存在", "字体文件或姓名文件不存在，请检查路径！")
        return

    if bg_type in ['图片', '视频（存在bug，有能力的解决）'] and not os.path.exists(bg_value):
        messagebox.showerror("文件不存在", f"{bg_type}文件不存在，请检查路径！")
        return

    generate_button.config(state=tk.DISABLED)
    progress_var.set(0)
    progress_bar.start()
    thread = threading.Thread(target=generate_name_video, args=(
        name_file_path, font_path, output_path, fps, (width, height), interval,
        text_size, text_color, bg_type, bg_value, progress_var, root))
    thread.start()


def open_github():
    webbrowser.open("https://github.com/Lun-OS/Name-flash-video-generation-python")


# 切换主题模式
def switch_theme(is_dark):
    if is_dark:
        apply_dark_theme()
    else:
        apply_light_theme()
    update_theme_icon()


# 应用浅色主题
def apply_light_theme():
    global current_theme
    current_theme = "light"
    
    # 更新颜色配置
    win11_colors = {
        'bg': '#f8f9fa',
        'accent': '#3a7bd5',  # Win11蓝
        'light_accent': '#e8f0fe',
        'text': '#202124',
        'text_light': '#5f6368',
        'border': '#dadce0',
        'hover': '#e9ecef',
        'entry_bg': 'white'
    }
    
    update_theme(win11_colors)


# 应用深色主题
def apply_dark_theme():
    global current_theme
    current_theme = "dark"
    
    # 更新颜色配置
    win11_colors = {
        'bg': '#1e1e1e',
        'accent': '#5d89d6',  # 深色模式下的蓝色
        'light_accent': '#2d3b66',
        'text': '#f0f0f0',
        'text_light': '#b0b0b0',
        'border': '#383838',
        'hover': '#333333',
        'entry_bg': '#2d2d2d'
    }
    
    update_theme(win11_colors)


# 更新主题样式
def update_theme(colors):
    # 更新框架背景
    main_frame.configure(style='Win11.TFrame')
    advanced_frame.configure(style='Win11.TFrame')
    
    # 更新样式配置
    style.configure('Win11.TFrame', 
                    background=colors['bg'])
    
    style.configure('Win11.TLabel',
                    background=colors['bg'],
                    foreground=colors['text'])
    
    style.configure('Win11.TEntry',
                    fieldbackground=colors['entry_bg'],
                    foreground=colors['text'],
                    bordercolor=colors['border'])
    
    style.map('Win11.TEntry',
              bordercolor=[('focus', colors['accent'])])
    
    style.configure('Win11.TButton',
                    background=colors['light_accent'],
                    foreground=colors['accent'])
    
    style.map('Win11.TButton',
              background=[('active', colors['accent']), ('hover', colors['hover'])],
              foreground=[('active', 'white'), ('hover', colors['accent'])])
    
    style.configure('Win11.Horizontal.TProgressbar',
                    background=colors['accent'],
                    troughcolor=colors['light_accent'])
    
    # 更新标题颜色
    title_label.configure(foreground=colors['accent'])
    copyright_label.configure(foreground=colors['text_light'])
    github_link.configure(foreground=colors['accent'])


# 创建主窗口
root = tk.Tk()
root.title("名字闪烁视频生成器")
root.geometry("850x650")
root.minsize(800, 600)

# 设置Win11风格
if is_windows:
    try:
        # 对于Windows 11，启用毛玻璃效果和圆角
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        enable_mica_effect(hwnd)
        set_window_corner(hwnd, 2)  # 2 = 圆角
    except:
        pass

# 创建自定义样式
style = ttk.Style()
style.theme_use('clam')

# 创建主框架
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# 添加标题
title_label = ttk.Label(main_frame, text="名字闪烁视频生成器", 
                       font=('Segoe UI', 16, 'bold'),
                       style='Win11.TLabel')
title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

# 字体文件选择
ttk.Label(main_frame, text="字体文件位置（ttf）:", style='Win11.TLabel').grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
font_entry = ttk.Entry(main_frame, width=50, style='Win11.TEntry')
font_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)
font_button = ttk.Button(main_frame, text="浏览...", command=select_font_file, style='Win11.TButton')
font_button.grid(row=1, column=2, padx=10, pady=10)

# 姓名文件选择
ttk.Label(main_frame, text="姓名文件位置（txt）:", style='Win11.TLabel').grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
name_entry = ttk.Entry(main_frame, width=50, style='Win11.TEntry')
name_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.EW)
name_button = ttk.Button(main_frame, text="浏览...", command=select_name_file, style='Win11.TButton')
name_button.grid(row=2, column=2, padx=10, pady=10)

# FPS 输入
ttk.Label(main_frame, text="帧率（FPS）:", style='Win11.TLabel').grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
fps_entry = ttk.Entry(main_frame, width=10, style='Win11.TEntry')
fps_entry.insert(0, "30")
fps_entry.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

# 分辨率输入
# 宽度
width_frame = ttk.Frame(main_frame, style='Win11.TFrame')
width_frame.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)

ttk.Label(width_frame, text="分辨率  宽度:", style='Win11.TLabel').pack(side=tk.LEFT)
width_entry = ttk.Entry(width_frame, width=10, style='Win11.TEntry')
width_entry.insert(0, "192")
width_entry.pack(side=tk.LEFT, padx=(5, 0))
ttk.Label(width_frame, text="像素", style='Win11.TLabel').pack(side=tk.LEFT, padx=(5, 10))

# 高度
height_frame = ttk.Frame(main_frame, style='Win11.TFrame')
height_frame.grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)

ttk.Label(height_frame, text="高度:", style='Win11.TLabel').pack(side=tk.LEFT)
height_entry = ttk.Entry(height_frame, width=10, style='Win11.TEntry')
height_entry.insert(0, "108")
height_entry.pack(side=tk.LEFT, padx=(5, 0))
ttk.Label(height_frame, text="像素", style='Win11.TLabel').pack(side=tk.LEFT, padx=(5, 0))

# 名字停留时间输入
ttk.Label(main_frame, text="名字停留时间 (秒):", style='Win11.TLabel').grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
interval_entry = ttk.Entry(main_frame, width=10, style='Win11.TEntry')
interval_entry.insert(0, "0.2")
interval_entry.grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)

# 输出路径选择
ttk.Label(main_frame, text="视频输出路径:", style='Win11.TLabel').grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)
output_entry = ttk.Entry(main_frame, width=50, style='Win11.TEntry')
output_entry.grid(row=6, column=1, padx=10, pady=10, sticky=tk.EW)
output_button = ttk.Button(main_frame, text="浏览...", command=select_output_path, style='Win11.TButton')
output_button.grid(row=6, column=2, padx=10, pady=10)

# 高级选项按钮
advanced_button = ttk.Button(main_frame, text="展开高级选项", command=toggle_advanced_options, style='Win11.TButton')
advanced_button.grid(row=7, column=0, columnspan=3, pady=10)

# 高级选项框架
advanced_frame = ttk.Frame(main_frame, style='Win11.TFrame')

# 文字大小
ttk.Label(advanced_frame, text="文字大小:", style='Win11.TLabel').grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
text_size_entry = ttk.Entry(advanced_frame, width=10, style='Win11.TEntry')
text_size_entry.insert(0, "70")
text_size_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

# 文字颜色
ttk.Label(advanced_frame, text="文字颜色:", style='Win11.TLabel').grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
text_color_entry = ttk.Entry(advanced_frame, width=10, style='Win11.TEntry')
text_color_entry.insert(0, "#ffffff")
text_color_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
color_button = ttk.Button(advanced_frame, text="选择颜色", command=choose_text_color, style='Win11.TButton')
color_button.grid(row=1, column=2, padx=10, pady=5)

# 背景类型
ttk.Label(advanced_frame, text="背景类型:", style='Win11.TLabel').grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
bg_type_var = tk.StringVar()
bg_type_var.set("纯色")
bg_type_menu = ttk.Combobox(advanced_frame, textvariable=bg_type_var, 
                           values=["纯色", "图片", "视频（暂不支持）"],
                           state="readonly", style='Win11.TCombobox')
bg_type_menu.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

# 背景值
ttk.Label(advanced_frame, text="背景值:", style='Win11.TLabel').grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
bg_entry = ttk.Entry(advanced_frame, width=50, style='Win11.TEntry')
bg_entry.insert(0, "#000000")
bg_entry.grid(row=3, column=1, padx=10, pady=5, sticky=tk.EW)

# 为纯色背景添加颜色选择按钮
color_frame = ttk.Frame(advanced_frame)
color_frame.grid(row=3, column=2, padx=10, pady=5)

bg_button = ttk.Button(color_frame, text="选择文件", command=select_bg_file, style='Win11.TButton')
bg_button.pack(side=tk.LEFT, padx=(0, 5))

choose_bg_color_button = ttk.Button(color_frame, text="选择颜色", command=choose_bg_color, style='Win11.TButton')
choose_bg_color_button.pack(side=tk.LEFT)

# 生成按钮
generate_button = ttk.Button(main_frame, text="生成视频", command=generate_video, style='Win11.TButton')
generate_button.grid(row=8, column=0, columnspan=3, pady=20)

# 进度条
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100, style='Win11.Horizontal.TProgressbar')
progress_bar.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky=tk.EW)

# 添加右下角版权信息
copyright_label = ttk.Label(main_frame, text="By:Lun.", style='Win11.TLabel')
copyright_label.grid(row=10, column=2, sticky="se", padx=10, pady=10)

# 添加左下角GitHub链接
github_link = ttk.Label(main_frame, text="GitHub", cursor="hand2", style='Win11.TLabel')
github_link.grid(row=10, column=0, sticky="sw", padx=10, pady=10)
github_link.bind("<Button-1>", lambda e: open_github())

# 配置列权重，使界面可以自适应调整
main_frame.columnconfigure(1, weight=1)
advanced_frame.columnconfigure(1, weight=1)

# 设置行权重
for i in range(11):
    main_frame.rowconfigure(i, weight=1)

for i in range(4):
    advanced_frame.rowconfigure(i, weight=1)

# 添加主题切换按钮（使用昼夜图标）
theme_button = ttk.Button(main_frame, text="🌙", command=lambda: switch_theme(current_theme == "light"), style='Win11.TButton')
theme_button.grid(row=0, column=2, padx=10, pady=10, sticky="ne")

def update_theme_icon():
    if current_theme == "light":
        theme_button.config(text="🌙")
    else:
        theme_button.config(text="☀️")

# 初始化主题 - 强制使用白色主题
current_theme = None
apply_light_theme()
update_theme_icon()

# 运行主循环
root.mainloop()
