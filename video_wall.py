# Import required libraries and modules
from functools import partial
from PyQt5.QtCore import QTimer
from collections import defaultdict
import math
import sys
import os
import random
import cv2
from osxmetadata import OSXMetaData
from PyQt5.QtCore import Qt, QDir, QUrl, QSize
from PyQt5.QtGui import QIcon, QScreen
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QFileDialog, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QSizePolicy, QComboBox
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget


# Define the main VideoWall class which inherits from QWidget
class VideoWall(QWidget):
    def __init__(self, max_videos=32):
        super().__init__()

        self.max_videos = max_videos
        self.current_folder = None # initialize to None
        self.video_players = []  # Add this line to initialize the video_players attribute
        self.init_ui()
        self.extra_windows = {}  # Initialize to an empty dictionary

    # Initialize the user interface elements
    def init_ui(self):
        self.setWindowTitle('Video Wall')
        self.setWindowIcon(QIcon('icon.png'))

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a QHBoxLayout for the buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        # Screen selection buttons
        self.screens_layout = QHBoxLayout()
        layout.addLayout(self.screens_layout)
        screen_count = QApplication.desktop().screenCount()
        for i in range(screen_count):
            screen_btn = QPushButton(f'Screen {i + 1}', self)
            screen_btn.setCheckable(True)
            screen_btn.toggled.connect(partial(self.add_screen, screen_number=i))
            self.screens_layout.addWidget(screen_btn)

        # Screen selection combo box
        self.screens_layout = QHBoxLayout()
        layout.addLayout(self.screens_layout)

        # Folder selection button
        self.folder_btn = QPushButton('Select Folder', self)
        self.folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_btn)

        # Add the folder_btn to the buttons layout
        buttons_layout.addWidget(self.folder_btn)

        # Fit to screen button
        self.fit_to_screen_btn = QPushButton('Fit to Screen', self)
        self.fit_to_screen_btn.setCheckable(True)
        self.fit_to_screen_btn.toggled.connect(self.toggle_fit_to_screen)
        buttons_layout.addWidget(self.fit_to_screen_btn)

        # Number of videos dropdown
        self.num_videos_dropdown = QComboBox(self)
        self.num_videos_dropdown.addItems([str(i) for i in range(1, self.max_videos + 1)])
        self.num_videos_dropdown.currentIndexChanged.connect(self.update_video_display)
        layout.addWidget(self.num_videos_dropdown)

        # Add a QTimer for debouncing slider value changes
        self.slider_timer = QTimer()
        self.slider_timer.setSingleShot(True)
        self.slider_timer.timeout.connect(self.update_video_display)

        # Add a QHBoxLayout for tag sliders
        self.tag_sliders_layout = QHBoxLayout()
        layout.addLayout(self.tag_sliders_layout)

        # Video widgets grid layout
        self.video_grid = QGridLayout()
        layout.addLayout(self.video_grid)

        self.video_widgets = []

    # Define add_screen so I can toggle the window to show on another screen in another instance
    def add_screen(self, checked, screen_number):
        if checked:
            new_window = VideoWall()
            new_window.show()

            screen = QApplication.instance().screens()[screen_number]
            new_window.setGeometry(screen.availableGeometry())

            # Store the new window in an attribute
            self.extra_windows[screen_number] = new_window
        else:
            extra_window = self.extra_windows.pop(screen_number, None)
            if extra_window:
                extra_window.close()

    # Define a close event method to help with resource leaks
    def closeEvent(self, event):
        for player in self.video_players:
            player.stop()
            player.setMedia(QMediaContent())
            player.setVideoOutput(None)
        super().closeEvent(event)

    # Toggle the aspect ratio mode for all video widgets
    def toggle_fit_to_screen(self, checked):
        aspect_ratio_mode = Qt.KeepAspectRatio if not checked else Qt.IgnoreAspectRatio
        for video_widget in self.video_widgets:
            video_widget.setAspectRatioMode(aspect_ratio_mode)

    def on_slider_value_changed(self):
        # Restart the timer every time the slider value changes
        self.slider_timer.start(500)

    def on_media_status_changed(self, status, player):
        if status == QMediaPlayer.EndOfMedia:
            player.setPosition(0)
            player.play()

    # screen number
    def update_screen(self):
        screen_number = self.screen_combo.currentIndex()
        screen = QApplication.instance().screens()[screen_number]
        self.setGeometry(screen.availableGeometry())

    # Select a folder containing video files
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Video Folder', options=QFileDialog.ShowDirsOnly)

        print(f"Selected folder: {folder_path}")

        if folder_path:
            self.create_tag_sliders(folder_path)
            self.load_videos(folder_path)

    # Update the video display based on the number of videos dropdown value
    def update_video_display(self):
        num_videos = int(self.num_videos_dropdown.currentText())
        self.load_videos(self.current_folder)

    def create_tag_sliders(self, folder_path):
        # Remove previous sliders from the layout
        for i in reversed(range(self.tag_sliders_layout.count())):
            self.tag_sliders_layout.itemAt(i).widget().setParent(None)

        # Get all unique tags from video files
        tags = set()
        for f in os.listdir(folder_path):
            if f.endswith(('.mp4', '.mkv', '.avi', '.flv', '.mov')):
                file_path = os.path.join(folder_path, f)
                md = OSXMetaData(file_path)
                tags.update(md.tags)

        # Create sliders for each unique tag
        self.tag_sliders = {}
        for tag in tags:
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setTickInterval(10)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.valueChanged.connect(self.update_video_display)

            label = QLabel(f"{tag.name}")
            self.tag_sliders_layout.addWidget(label)
            self.tag_sliders_layout.addWidget(slider)
            self.tag_sliders[tag] = slider

    # Load and display video files from the selected folder
    def load_videos(self, folder_path):
        if not folder_path:
            return

        # Get video file paths and their tags
        videos = []
        video_tags = defaultdict(list)
        for f in os.listdir(folder_path):
            if f.endswith(('.mp4', '.mkv', '.avi', '.flv', '.mov')):
                file_path = os.path.join(folder_path, f)
                md = OSXMetaData(file_path)
                file_tags = md.tags
                videos.append(file_path)
                for tag in file_tags:
                    video_tags[tag].append(file_path)

        # Use slider values to influence the random selection of videos
        weighted_videos = []
        for tag, slider in self.tag_sliders.items():
            weight = slider.value()
            for video in video_tags[tag]:
                for _ in range(weight):
                    weighted_videos.append(video)

        random.shuffle(weighted_videos)

        self.current_folder = folder_path
        videos = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                  f.endswith(('.mp4', '.mkv', '.avi', '.flv', '.mov'))]

        random.shuffle(videos)

        print(f"Updating video display with {len(videos)} videos from folder: {folder_path}")

        for video_widget in self.video_widgets:
            player = self.video_players.pop(0)  # Remove the corresponding player from the list
            player.setVideoOutput(None)  # Disconnect the player from the video widget
            player.deleteLater()  # Schedule the player for deletion
            self.video_grid.removeWidget(video_widget)
            video_widget.deleteLater()

        self.video_widgets.clear()
        # Release resources of existing video players
        for player in self.video_players:
            player.stop()
            player.setMedia(QMediaContent())
            player.setVideoOutput(None)
            player.deleteLater()

        # Clear the video players list
        self.video_players.clear()

        num_videos = int(self.num_videos_dropdown.currentText())

        num_columns = math.ceil(math.sqrt(num_videos))
        num_rows = math.ceil(num_videos / num_columns)

        # Calculate the size of each video widget
        grid_size = self.video_grid.sizeHint()
        widget_size = QSize(grid_size.width() // num_columns, grid_size.height() // num_rows)

        for i, video_path in enumerate(videos[:num_videos]):
            video_widget = QVideoWidget()
            self.video_widgets.append(video_widget)
            self.video_grid.addWidget(video_widget, i // num_columns, i % num_columns)

            # Initialize a QMediaPlayer object to play the video
            player = QMediaPlayer()
            # Connect the mediaStatusChanged signal to the custom slot
            player.mediaStatusChanged.connect(lambda status, p=player: self.on_media_status_changed(status, p))
            player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
            player.setVideoOutput(video_widget)
            player.mediaStatusChanged.connect(partial(self.on_media_status_changed, player=player))
            player.error.connect(lambda error: print(f"Error: {error}"))

            # Add the player to the list
            self.video_players.append(player)

            # timer functionality to delay video start
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(player.play)
            timer.start(500)  # Start playing the video after a 500 ms delay

            # Print media status and error message (if any)
            print(f"Loading media: {video_path}")
            print(f"Media status: {player.mediaStatus()}")

            # Set the video widget size policy and aspect ratio mode
            video_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            video_widget.setAspectRatioMode(Qt.KeepAspectRatio)

            # Display the video widget
            video_widget.show()
        print("Added video widgets to layout")

# Define the main function that initializes the QApplication and runs the VideoWall
def main():
    app = QApplication(sys.argv)
    video_wall = VideoWall()
    video_wall.show()

    # Set the screen number based on user selection
    screen_number = 0 # Defaulted to 0 so it's on the main screen when it starts
    screen = app.screens()[screen_number]
    video_wall.setGeometry(screen.availableGeometry())

    sys.exit(app.exec_())

# Run the main function when the script is executed
if __name__ == '__main__':
    main()
