import sys
import os
import yt_dlp
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QProgressBar
from PySide6.QtCore import Qt, QObject, Signal, QThread, Slot
from concurrent.futures import ThreadPoolExecutor
import datetime

class DownloadWorker(QObject):
    finished = Signal()
    progress = Signal(int, float, float, str)

    def __init__(self, video_url, output_path, selected_quality):
        super().__init__()
        self.video_url = video_url
        self.output_path = output_path
        self.selected_quality = selected_quality

    @Slot()
    def run(self):
        try:
            output_path = os.path.expanduser(self.output_path)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            ydl_opts = {
                'format': self.selected_quality,
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_url])
        except Exception as e:
            print(f'Error: {e}')
        finally:
            self.finished.emit()

    def update_progress(self, d):
        if 'status' in d and d['status'] == 'downloading':
            progress_info = d['_percent_str'].replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
            progress_value = int(progress_info.split('.')[0])
            total_size = d.get('total_bytes')
            downloaded_size = d.get('downloaded_bytes')

            if total_size and downloaded_size:
                time_left = d.get('eta', 'N/A')
                self.progress.emit(progress_value, total_size, downloaded_size, time_left)

class YouTubeDownloaderUI(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.thread_pool = ThreadPoolExecutor(max_workers=5)

    def init_ui(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(100, 100, 500, 400)

        # Stylish colors
        main_color = '#3498db'  # Blue color for demonstration, replace with your preferred color
        background_color = '#2c3e50'  # Dark background
        text_color = '#ecf0f1'  # Light text
        input_background_color = '#34495e'  # Dark gray background for input fields
        progress_bar_color = '#3498db'  # Blue color for progress bar

        # Styling for a modern appearance
        self.setStyleSheet("""
            QWidget {
                background-color: """ + background_color + """;
                color: """ + text_color + """;
            }
            QLabel {
                color: """ + text_color + """;
            }
            QLineEdit, QComboBox {
                background-color: """ + input_background_color + """;
                border: 1px solid #2c3e50;
                color: """ + text_color + """;
                padding: 8px;
                border-radius: 5px;
            }
            QLineEdit:hover, QComboBox:hover {
                border: 1px solid """ + main_color + """;
            }
            QPushButton {
                background-color: """ + main_color + """;
                color: #ffffff;
                padding: 10px;
                border: 1px solid """ + main_color + """;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QProgressBar {
                background-color: #34495e;
                color: #ffffff;
                border: 1px solid #2c3e50;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: """ + progress_bar_color + """;
                width: 5px;
            }
        """)

        # Widgets
        self.url_label = QLabel('Enter YouTube video URL:')
        self.url_input = QLineEdit(self)

        self.quality_label = QLabel('Select video quality:')
        self.quality_label.setStyleSheet(f"color: {main_color}; font-size: 14px;")
        self.quality_combo = QComboBox(self)
        self.quality_combo.addItems(['best', 'worst'])  # Add more options as needed

        self.output_label = QLabel('Select download location:')
        self.output_path = QLineEdit(self)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.select_output_path)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        self.download_button = QPushButton('Download', self)
        self.download_button.clicked.connect(self.start_download)

        self.progress_info_label = QLabel('')

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.quality_label)
        layout.addWidget(self.quality_combo)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_path)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_info_label)

        self.setLayout(layout)

    def select_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder', os.path.expanduser('~/Documents'))
        if folder:
            self.output_path.setText(folder)

    def start_download(self):
        video_url = self.url_input.text()
        output_path = self.output_path.text()
        selected_quality = self.quality_combo.currentText()

        if not video_url or not output_path:
            return

        download_worker = DownloadWorker(video_url, output_path, selected_quality)
        download_worker.finished.connect(self.handle_download_finished)
        download_worker.progress.connect(self.update_progress_info)

        self.thread_pool.submit(download_worker.run)

    def handle_download_finished(self):
        # Update UI or provide feedback when a download is finished
        print("Download finished")

    def update_progress_info(self, progress, total_size, downloaded_size, time_left):
        self.progress_bar.setValue(progress)

        total_size_mb = total_size / (1024 * 1024)
        downloaded_size_mb = downloaded_size / (1024 * 1024)

        info_text = f"Progress: {progress}% | Downloaded: {downloaded_size_mb:.2f} MB / {total_size_mb:.2f} MB | ETA: {time_left}"
        self.progress_info_label.setText(info_text)


def run_application():
    app = QApplication(sys.argv)
    main_window = YouTubeDownloaderUI()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_application()
