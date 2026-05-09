import cv2
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import sys
import random
import ctypes
from ctypes import wintypes
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# 全局系统检测
is_windows = sys.platform.startswith('win32')

# -------------------------- Windows 毛玻璃/主题 API --------------------------
if is_windows:
    try:
        user32 = ctypes.WinDLL('user32')
        dwmapi = ctypes.WinDLL('dwmapi')
        
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWA_MICA_EFFECT = 1029
        DWMSBT_MAINWINDOW = 2

        def set_window_effect(hwnd):
            """Win11 圆角+云母效果"""
            try:
                # 圆角
                dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int)
                )
                # 毛玻璃
                dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_MICA_EFFECT,
                    ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)), ctypes.sizeof(ctypes.c_int)
                )
            except:
                pass

        def is_dark_mode():
            return False
    except:
        def set_window_effect(hwnd): pass
else:
    def set_window_effect(hwnd): pass

# -------------------------- 视频生成线程（防界面卡顿） --------------------------
class VideoGeneratorThread(QThread):
    # 自定义信号：进度值(0-100)、完成状态、错误信息
    progress_update = pyqtSignal(int)  # 修改：指定为int类型
    task_finished = pyqtSignal(bool, str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            # 解包参数
            name_file, font_path, output_path, fps, frame_size, interval, \
            text_size, text_color, bg_type, bg_value = self.params

            # 读取姓名列表
            with open(name_file, 'r', encoding='utf-8') as f:
                names = [n.strip() for n in f.readlines() if n.strip()]

            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
            font = ImageFont.truetype(font_path, text_size)

            # 计算帧数
            frames_per_name = int(interval * fps)
            total_frames = len(names) * frames_per_name
            current_frame = 0

            for name in names:
                # 生成背景
                if bg_type == '纯色':
                    img = Image.new('RGB', frame_size, color=bg_value)
                elif bg_type == '图片':
                    try:
                        bg_img = Image.open(bg_value).resize(frame_size, Image.LANCZOS)
                        img = bg_img.copy()
                    except:
                        img = Image.new('RGB', frame_size, color=(0,0,0))
                elif bg_type == '视频（暂不支持）':
                    img = Image.new('RGB', frame_size, color=(0,0,0))
                else:
                    img = Image.new('RGB', frame_size, color=(0,0,0))

                # 绘制居中文字
                draw = ImageDraw.Draw(img)
                bbox = draw.textbbox((0,0), name, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                x = (frame_size[0] - text_w) // 2
                y = (frame_size[1] - text_h) // 2
                draw.text((x, y), name, font=font, fill=text_color)

                # 转OpenCV格式并写入帧
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                for _ in range(frames_per_name):
                    out.write(img_cv)
                    current_frame += 1
                    progress = int((current_frame / total_frames) * 100)  # 修改：强制转整数
                    self.progress_update.emit(progress)

            out.release()
            self.task_finished.emit(True, "视频生成成功！")

        except Exception as e:
            self.task_finished.emit(False, f"生成失败：{str(e)}")

# -------------------------- 主窗口 --------------------------
class NameVideoGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"  # 默认浅色主题
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        # 窗口基础设置
        self.setWindowTitle("名字闪烁视频生成器")
        self.setMinimumSize(850, 650)
        self.resize(850, 650)

        # Win11 毛玻璃效果
        if is_windows:
            set_window_effect(int(self.winId()))

        # 中心部件 + 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # ============== 标题行 ==============
        title_label = QLabel("名字闪烁视频生成器")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label, 0, 0, 1, 2)

        # 主题切换按钮
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self.switch_theme)
        main_layout.addWidget(self.theme_btn, 0, 2, Qt.AlignRight)

        # ============== 基础配置项 ==============
        # 1. 字体文件
        main_layout.addWidget(QLabel("字体文件（ttf/otf）："), 1, 0)
        self.font_entry = QLineEdit()
        self.font_btn = QPushButton("浏览")
        self.font_btn.clicked.connect(self.select_font)
        main_layout.addWidget(self.font_entry, 1, 1)
        main_layout.addWidget(self.font_btn, 1, 2)

        # 2. 姓名文件
        main_layout.addWidget(QLabel("姓名文件（txt）："), 2, 0)
        self.name_entry = QLineEdit()
        self.name_btn = QPushButton("浏览")
        self.name_btn.clicked.connect(self.select_name_file)
        main_layout.addWidget(self.name_entry, 2, 1)
        main_layout.addWidget(self.name_btn, 2, 2)

        # 3. 帧率 FPS
        main_layout.addWidget(QLabel("帧率（FPS）："), 3, 0)
        self.fps_entry = QLineEdit("30")
        main_layout.addWidget(self.fps_entry, 3, 1)

        # 4. 分辨率
        main_layout.addWidget(QLabel("分辨率："), 4, 0)
        res_layout = QHBoxLayout()
        self.width_entry = QLineEdit("1920")
        self.height_entry = QLineEdit("1080")
        res_layout.addWidget(self.width_entry)
        res_layout.addWidget(QLabel("×"))
        res_layout.addWidget(self.height_entry)
        res_layout.addWidget(QLabel("像素"))
        main_layout.addLayout(res_layout, 4, 1)

        # 5. 名字停留时间
        main_layout.addWidget(QLabel("停留时间（秒）："), 5, 0)
        self.interval_entry = QLineEdit("0.2")
        main_layout.addWidget(self.interval_entry, 5, 1)

        # 6. 输出路径
        main_layout.addWidget(QLabel("输出路径："), 6, 0)
        self.output_entry = QLineEdit()
        self.output_btn = QPushButton("浏览")
        self.output_btn.clicked.connect(self.select_output)
        main_layout.addWidget(self.output_entry, 6, 1)
        main_layout.addWidget(self.output_btn, 6, 2)

        # ============== 高级选项折叠面板 ==============
        self.advanced_btn = QPushButton("展开高级选项")
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        main_layout.addWidget(self.advanced_btn, 7, 0, 1, 3)

        # 高级选项容器
        self.advanced_frame = QFrame()
        self.advanced_frame.setVisible(False)
        adv_layout = QGridLayout(self.advanced_frame)
        adv_layout.setSpacing(8)

        # 文字大小
        adv_layout.addWidget(QLabel("文字大小："), 0, 0)
        self.text_size_entry = QLineEdit("70")
        adv_layout.addWidget(self.text_size_entry, 0, 1)

        # 文字颜色
        adv_layout.addWidget(QLabel("文字颜色："), 1, 0)
        self.text_color_entry = QLineEdit("#ffffff")
        self.text_color_btn = QPushButton("选择颜色")
        self.text_color_btn.clicked.connect(self.choose_text_color)
        adv_layout.addWidget(self.text_color_entry, 1, 1)
        adv_layout.addWidget(self.text_color_btn, 1, 2)

        # 背景类型
        adv_layout.addWidget(QLabel("背景类型："), 2, 0)
        self.bg_type = QComboBox()
        self.bg_type.addItems(["纯色", "图片", "视频（暂不支持）"])
        self.bg_type.currentTextChanged.connect(self.on_bg_type_change)
        adv_layout.addWidget(self.bg_type, 2, 1)

        # 背景值
        adv_layout.addWidget(QLabel("背景值："), 3, 0)
        self.bg_entry = QLineEdit("#000000")
        self.bg_file_btn = QPushButton("选择文件")
        self.bg_file_btn.clicked.connect(self.select_bg_file)
        self.bg_color_btn = QPushButton("选择颜色")
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        adv_layout.addWidget(self.bg_entry, 3, 1)
        
        bg_btn_layout = QHBoxLayout()
        bg_btn_layout.addWidget(self.bg_file_btn)
        bg_btn_layout.addWidget(self.bg_color_btn)
        adv_layout.addLayout(bg_btn_layout, 3, 2)

        main_layout.addWidget(self.advanced_frame, 8, 0, 1, 3)

        # ============== 生成按钮 + 进度条 ==============
        self.generate_btn = QPushButton("生成视频")
        self.generate_btn.clicked.connect(self.start_generate)
        self.generate_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        main_layout.addWidget(self.generate_btn, 9, 0, 1, 3)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar, 10, 0, 1, 3)

        # ============== 底部版权/链接 ==============
        main_layout.addWidget(QLabel("By:Lun."), 11, 2, Qt.AlignRight)
        github_link = QLabel('<a href="https://github.com/Lun-OS/Name-flash-video-generation-python">GitHub</a>')
        github_link.setOpenExternalLinks(True)
        main_layout.addWidget(github_link, 11, 0, Qt.AlignLeft)

        # 自适应布局
        for col in range(3):
            main_layout.setColumnStretch(col, 1)

    # -------------------------- 文件选择 --------------------------
    def select_font(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择字体文件", "", "字体文件 (*.ttf *.otf)")
        if path: 
            self.font_entry.setText(path)

    def select_name_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择姓名文件", "", "文本文件 (*.txt)")
        if path: 
            self.name_entry.setText(path)

    def select_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存视频", "", "MP4视频 (*.mp4)")
        if path:
            if not path.endswith(".mp4"):
                path += ".mp4"
            self.output_entry.setText(path)

    def select_bg_file(self):
        bg_t = self.bg_type.currentText()
        if bg_t == "图片":
            path, _ = QFileDialog.getOpenFileName(self, "选择背景图片", "", "图片 (*.png *.jpg *.jpeg)")
        elif bg_t == "视频（暂不支持）":
            path, _ = QFileDialog.getOpenFileName(self, "选择背景视频", "", "视频 (*.mp4 *.avi)")
        else:
            return
        if path: 
            self.bg_entry.setText(path)

    # -------------------------- 颜色选择 --------------------------
    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color_entry.text()))
        if color.isValid():
            self.text_color_entry.setText(color.name())

    def choose_bg_color(self):
        if self.bg_type.currentText() == "纯色":
            color = QColorDialog.getColor(QColor(self.bg_entry.text()))
            if color.isValid():
                self.bg_entry.setText(color.name())

    # -------------------------- 高级选项折叠 --------------------------
    def toggle_advanced(self):
        visible = not self.advanced_frame.isVisible()
        self.advanced_frame.setVisible(visible)
        self.advanced_btn.setText("折叠高级选项" if visible else "展开高级选项")

    def on_bg_type_change(self):
        """背景类型切换时重置输入框"""
        t = self.bg_type.currentText()
        if t == "纯色":
            self.bg_entry.setText("#000000")
        else:
            self.bg_entry.clear()

    # -------------------------- 主题切换 --------------------------
    def switch_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_btn.setText("☀️" if self.current_theme == "dark" else "🌙")
        self.apply_theme()

    def apply_theme(self):
        """浅色/深色主题样式"""
        if self.current_theme == "light":
            self.setStyleSheet("""
                QMainWindow { background-color: #f8f9fa; }
                QLabel { color: #202124; font-size: 10pt; }
                QLineEdit { background-color: white; color: #202124; border: 1px solid #dadce0; padding: 4px; }
                QPushButton { background-color: #e8f0fe; color: #3a7bd5; border: none; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background-color: #d2e3fc; }
                QComboBox { background-color: white; border: 1px solid #dadce0; padding: 4px; }
                QProgressBar { border: 1px solid #dadce0; }
                QProgressBar::chunk { background-color: #3a7bd5; }
                QFrame { border: 1px solid #dadce0; border-radius: 4px; padding: 8px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #1e1e1e; }
                QLabel { color: #f0f0f0; font-size: 10pt; }
                QLineEdit { background-color: #2d2d2d; color: #f0f0f0; border: 1px solid #383838; padding: 4px; }
                QPushButton { background-color: #2d3b66; color: #5d89d6; border: none; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background-color: #3a4b77; }
                QComboBox { background-color: #2d2d2d; color: #f0f0f0; border: 1px solid #383838; padding: 4px; }
                QProgressBar { border: 1px solid #383838; }
                QProgressBar::chunk { background-color: #5d89d6; }
                QFrame { border: 1px solid #383838; border-radius: 4px; padding: 8px; }
            """)

    # -------------------------- 启动生成 --------------------------
    def start_generate(self):
        # 1. 获取所有参数
        params = {
            "font": self.font_entry.text().strip(),
            "name": self.name_entry.text().strip(),
            "output": self.output_entry.text().strip(),
            "fps": self.fps_entry.text().strip(),
            "w": self.width_entry.text().strip(),
            "h": self.height_entry.text().strip(),
            "interval": self.interval_entry.text().strip(),
            "text_size": self.text_size_entry.text().strip(),
            "text_color": self.text_color_entry.text().strip(),
            "bg_type": self.bg_type.currentText(),
            "bg_value": self.bg_entry.text().strip()
        }

        # 2. 输入验证
        if not all([params["font"], params["name"], params["output"]]):
            QMessageBox.critical(self, "错误", "请填写所有必填项！")
            return

        try:
            fps = int(params["fps"])
            w, h = int(params["w"]), int(params["h"])
            interval = float(params["interval"])
            text_size = int(params["text_size"])
        except ValueError:
            QMessageBox.critical(self, "错误", "请输入有效数字！")
            return

        if not os.path.exists(params["font"]) or not os.path.exists(params["name"]):
            QMessageBox.critical(self, "错误", "字体/姓名文件不存在！")
            return

        # 3. 打包线程参数
        thread_params = (
            params["name"], params["font"], params["output"], fps, (w, h), interval,
            text_size, params["text_color"], params["bg_type"], params["bg_value"]
        )

        # 4. 启动线程
        self.generate_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.thread = VideoGeneratorThread(thread_params)
        self.thread.progress_update.connect(self.progress_bar.setValue)
        self.thread.task_finished.connect(self.on_generate_finish)
        self.thread.start()

    def on_generate_finish(self, success, msg):
        """生成完成回调"""
        self.generate_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.critical(self, "失败", msg)

# -------------------------- 程序入口 --------------------------
if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    window = NameVideoGenerator()
    window.show()
    sys.exit(app.exec_())