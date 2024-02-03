# Video Wall

Video Wall is a Python application that allows users to display multiple videos from a folder across their screen(s). Users can control the number of videos displayed,  create more windows if you have multiple screens, and allows you to change the random videos picked based on the weights for tags found among the files. The application supports macOS and uses PyQt5 for the graphical user interface.

###{Story Time}
I have almost no experience with python and I am currently in the process of learning. However, I started this around 24 hours before putting the working code onto github and ChatGPT4 basically did most of the work. Debugging was interesting and with my limited knowledge on coding, ChatGPT4 was the only helpful version of the three versions available right now. Ran out of responses from 4 and had to use 3.5 and it was night and day. I wouldn't have gotten this done without ChatGPT4.

## Installation

1. Clone the repository or download the project files.
2. Install the required dependencies by running the following command in Terminal:

pip install opencv-python osxmetadata PyQt5


## Running the Application

### From Source

To run the application from the source code, open Terminal, navigate to the project directory, and execute the `video_wall.py` script:
python video_wall.py


### From Executable

Alternatively, you can run the standalone executable file located in the `dist` folder:

./dist/VideoWall


## Packaging the Application

To package the application into a standalone executable, you can use [PyInstaller](https://www.pyinstaller.org/):

pip install pyinstaller
pyinstaller --onefile --windowed video_wall.py



This will generate an executable file in the `dist` folder.

## License

This project is open-source and available under the [MIT License](LICENSE).
