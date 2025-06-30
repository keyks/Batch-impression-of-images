import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QComboBox, QLineEdit, QMessageBox, QScrollArea, QGroupBox)
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent  # 正确导入
from PyQt5.QtCore import Qt
from PIL import Image
import os


def image_to_c_array(image_path, mode='逐行式', threshold=127, array_name="BMP1"):
    img = Image.open(image_path).convert('L')
    width, height = img.size
    binary_data = []

    for y in range(height):
        row_data = []
        for x in range(width):
            pixel_value = img.getpixel((x, y))
            row_data.append(1 if pixel_value > threshold else 0)
        binary_data.append(row_data)

    if mode == '逐行式':
        pass
    elif mode == '逐列式':
        binary_data = [[binary_data[y][x] for y in range(height)] for x in range(width)]
    elif mode == '行列式':
        binary_data = [binary_data[y] if (y % 2 == 0) else binary_data[y][::-1] for y in range(height)]
    elif mode == '列行式':
        binary_data = [
            [binary_data[y][x] for y in range(height)] if (x % 2 == 0) else [binary_data[y][x] for y in range(height)][
                                                                            ::-1] for x in range(width)
        ]
    else:
        raise ValueError("不支持的模式！")

    byte_array = []
    for y in range(0, height, 8):
        for x in range(width):
            byte = 0
            for bit in range(8):
                if y + bit < height:
                    byte |= (binary_data[y + bit][x] << bit)
            byte_array.append(byte)

    hex_array = ', '.join([f"0x{byte:02x}" for byte in byte_array])
    c_array = f"unsigned char {array_name}[] = {{\n{hex_array}\n}};"

    return c_array, width, height, binary_data


class ImageModApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(spacing=10)

        # 文件选择部分
        file_group = QGroupBox("输入与输出")
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit(self)
        self.file_path_edit.setFixedHeight(25)
        file_layout.addWidget(QLabel("选择输入图像文件:"))
        file_layout.addWidget(self.file_path_edit)
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedSize(60, 25)
        self.browse_button.clicked.connect(self.open_file_dialog)
        file_layout.addWidget(self.browse_button)

        self.folder_button = QPushButton("选择输出文件夹")
        self.folder_button.setFixedSize(100, 25)
        self.folder_button.clicked.connect(self.select_folder)
        file_layout.addWidget(self.folder_button)

        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # 模式与阈值部分
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        mode_label = QLabel("选择取模方式:")
        mode_layout.addWidget(mode_label)
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItems(["逐行式", "逐列式", "行列式", "列行式"])
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("输入灰度阈值 (0-255) [默认127]:")
        threshold_layout.addWidget(threshold_label)
        self.threshold_edit = QLineEdit(self)
        self.threshold_edit.setPlaceholderText("127")
        self.threshold_edit.setFixedHeight(25)
        self.threshold_edit.returnPressed.connect(self.preview_image)  # 按下Enter键时调用预览函数
        threshold_layout.addWidget(self.threshold_edit)
        settings_layout.addLayout(threshold_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # 运行按钮
        self.run_button = QPushButton("运行")
        self.run_button.setFixedSize(80, 30)
        self.run_button.clicked.connect(self.run_modification)
        main_layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

        # 预览区域
        self.preview_area = QScrollArea(self)
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(256, 256)
        self.preview_area.setWidget(self.preview_label)
        main_layout.addWidget(self.preview_area, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)
        self.setWindowTitle('图片取模程序')
        self.setFixedSize(500, 700)
        self.show()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        filenames, _ = QFileDialog.getOpenFileNames(self, "选择图片文件", "",
                                                    "Image Files (*.png *.jpg *.jpeg *.bmp);;", options=options)
        if filenames:
            self.file_path_edit.setText('; '.join(filenames))
            self.update_preview(filenames[0])  # 选择图片后预览

    def select_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", options=options)
        if folder:
            self.output_folder = folder

    def run_modification(self):
        image_paths = self.file_path_edit.text().split('; ')
        mode = self.mode_combo.currentText()

        try:
            threshold = int(self.threshold_edit.text()) if self.threshold_edit.text() else 127
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保输入的阈值是数字！")
            return

        if not image_paths or image_paths[0] == '':
            QMessageBox.warning(self, "输入错误", "请选择至少一个图片文件！")
            return

        if 'output_folder' not in self.__dict__:
            QMessageBox.warning(self, "保存路径错误", "请设置保存输出文件夹！")
            return

        output_file_path = os.path.join(self.output_folder, "output.txt")

        try:
            with open(output_file_path, 'w') as f:
                for i in range(len(image_paths)):
                    f.write(f"OLED_DrawBMP(0, 0, 60, 8, BMP{i + 1}, 0);\n")
                f.write("\n")
                for i in range(len(image_paths)):
                    f.write(f"extern unsigned char BMP{i + 1}[];\n")
                f.write("\n")
                for i, image_path in enumerate(image_paths):
                    c_array, _, _, _ = image_to_c_array(image_path, mode, threshold, array_name=f"BMP{i + 1}")
                    f.write(c_array + "\n\n")
            QMessageBox.information(self, "完成", "操作成功！结果已保存。")

            self.update_preview(image_paths[0], threshold, mode)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")

    def preview_image(self):
        """ 按下Enter键时预览处理后的图像 """
        image_paths = self.file_path_edit.text().split('; ')
        if image_paths and image_paths[0] != '':
            try:
                threshold = int(self.threshold_edit.text()) if self.threshold_edit.text() else 127
                self.update_preview(image_paths[0], threshold, self.mode_combo.currentText())
            except ValueError:
                QMessageBox.warning(self, "输入错误", "请确保输入的阈值是数字！")

    def update_preview(self, image_path, threshold=None, mode=None):
        try:
            if threshold is not None and mode is not None:
                _, width, height, binary_data = image_to_c_array(image_path, mode, threshold)
            else:
                width, height = Image.open(image_path).size

            processed_image = Image.new('L', (width, height))
            for y in range(height):
                for x in range(width):
                    if threshold is not None:
                        pixel_value = 255 if binary_data[y][x] else 0
                        processed_image.putpixel((x, y), pixel_value)
                    else:
                        processed_image.putpixel((x, y), 255)

            qimage = QImage(processed_image.tobytes(), width, height, QImage.Format_Grayscale8)
            self.preview_label.setPixmap(QPixmap.fromImage(qimage).scaled(256, 256, Qt.KeepAspectRatio))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览时发生错误: {str(e)}")


def main():
    app = QApplication(sys.argv)
    ex = ImageModApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
