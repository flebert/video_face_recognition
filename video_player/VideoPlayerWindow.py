"""
Script which opens a tkinter frame with an included video player. The first input parameter
given over the command line should be the path to the video file to open. If the parameter is omitted
the frame is opened without any initial video file loaded.
"""

import logging
import os
import tkinter as tk
from tkinter import font, filedialog

from PIL import Image
from PIL.ImageTk import PhotoImage

from video_player.EncodingManager import EncodingManager
from video_player.VLCPlayer import VLCPlayer
import face_recognition as fr


class VideoPlayerWindow:
    """
    Class which opens and manages a video player in a tkinter frame using the python-vlc library
    """

    def __init__(self, logger, initial_source, num_jitters, frames_to_skip, face_recognition_model):
        """
        Constructor of the VideoPlayerWindow

        Creates the frame including the video player and loads the first
        video file if the path was given

        :param logger: object used to perform logging
        :type logger: logging.Logger

        :param initial_source: path to the initial video file
        :type initial_source: str

        :param num_jitters: How many times to re-sample the face when calculating encoding
        :type num_jitters: int

        :param frames_to_skip: The number of frames to skip when face detection is activated
        :type frames_to_skip: int

        :param face_recognition_model: The model used for face recognition, either "cnn" which is accurate, slower and
        used GPU or "hog" which is faster but not as precise
        :type face_recognition_model: str

        """
        self.__num_jitters = num_jitters

        self.__logger = logger

        # path where images for pictures are stored
        resource_path = os.path.join(os.path.abspath(__file__), "..", "..", "resources")

        # create root window and bind ways to close the window
        root = tk.Tk()
        root.title("Video Face Recognition")
        root.bind("<Escape>", lambda event: self.__close_window())
        root.protocol("WM_DELETE_WINDOW", lambda: self.__close_window())
        root.grid_rowconfigure(0, weight=1)
        root.configure(bg="grey")
        self.__root = root
        """The root window containing all the video player and the widgets"""

        # Create encoding manager
        self.__enc_manager = EncodingManager(self.__logger)

        # setup menubar
        self.__menubar = tk.Menu(self.__root, tearoff=0)
        """The menubar of the main frame"""
        file = tk.Menu(self.__menubar, tearoff=0)
        file.add_command(label="Open", command=self.__open_video)
        self.__menubar.add_cascade(label="File", menu=file)

        encoding = tk.Menu(self.__menubar, tearoff=0)
        self.__menubar.add_cascade(label="Encoding", menu=encoding)

        detector = tk.Menu(self.__menubar, tearoff=0)
        encoding.add_command(label="Add face encoding", command=lambda: self.__open_encoding_creation_dialog(detector))
        self.__is_activated = tk.BooleanVar()
        self.__is_activated.set(False)
        self.__is_activated.trace_add("write", lambda *args: self.__switch_activation_state(2))

        len_known_encodings = len(self.__enc_manager.known_face_encodings)
        if len_known_encodings == 0:
            detector.add_radiobutton(label="Activate (no known encodings)", variable=self.__is_activated,
                                     value=True, state=tk.DISABLED)
        else:
            detector.add_radiobutton(label=f"Activate ({len_known_encodings} face encodings)",
                                     variable=self.__is_activated, value=True)
        detector.add_radiobutton(label="Deactivate", variable=self.__is_activated, value=False)
        self.__menubar.add_cascade(label="Detector (deactivated)", menu=detector)
        self.__root.config(menu=self.__menubar)

        # setting default font
        def_font = font.nametofont("TkDefaultFont")
        def_font.config(size=12)

        # frame within root frame
        frame = tk.Frame(root, bg="black")
        frame.grid(row=0, column=0, columnspan=5, sticky="NESW")
        frame.grid_rowconfigure(0, weight=1)
        self.__frame = frame
        """The main frame of the application, contains the video player"""

        # Creating VLC player manager
        self.__vlc_player = VLCPlayer(self.__frame, logger, frames_to_skip, face_recognition_model)
        self.__vlc_player.register_event("MediaPlayerTimeChanged",
                                         lambda event: self.__update_time(self.__vlc_player.get_duration_in_sec(),
                                                                          self.__vlc_player.get_current_time_in_ms()))

        # play button
        button_size = (30, 30)
        image = Image.open(os.path.join(resource_path, "play-button.png"))
        resized = image.resize(button_size)
        self.__play_img = PhotoImage(resized)
        """An image used for the resume button"""
        image = Image.open(os.path.join(resource_path, "pause-btn.png"))
        resized = image.resize(button_size)
        self.__stop_img = PhotoImage(resized)
        """An image used for the pause button"""
        self.__play_button = tk.Button(root, image=self.__stop_img, bd=-2, bg="grey", command=self.__pause_video,
                                       activebackground="grey", state="disabled", height=40, width=40)
        """A button used to resume/pause the loaded video"""
        self.__play_button.grid(row=1, column=0, sticky="NWS")

        # time sliding bar and rest time (video duration - current position)
        self.__time = tk.IntVar()
        """Variable measuring the currently shown seconds of the video file"""
        self.__time.set(0)
        self.__time_bar = tk.Scale(root, variable=self.__time, from_=0, to=10000, orient="horizontal", bg="grey",
                                   showvalue=0, troughcolor="black", highlightbackground="grey", state="disabled",
                                   sliderlength=10, repeatdelay=700)
        """Sliding bar, which allows to jump between different positions in the video"""
        self.__time_bar.grid(row=1, column=1, sticky="EW")
        self.__time_bar.bind("<Button-1>", lambda event: self.__pause_video(event))

        self.__time_bar.bind("<ButtonRelease-1>",
                             lambda event: self.__vlc_player.go_to_position(self.__time.get(),
                                                                            self.__update_rest_time_label,
                                                                            self.__play_video))
        root.grid_columnconfigure(1, weight=1)

        self.__rest_time_label = tk.Label(root, text="00:00:00", bd=-2, bg="grey")
        """Label showing the rest duration of the video file in the format hh:mm:ss"""
        self.__rest_time_label.grid(row=1, column=2, sticky="NSE")

        # volume control icon
        image = Image.open(os.path.join(resource_path, "speaker.png"))
        resized = image.resize((25, 25))
        self.__volume_img = PhotoImage(resized)
        volume_label = tk.Label(root, image=self.__volume_img, bd=-2, bg="grey")
        volume_label.grid(row=1, column=3, sticky="NSE", padx=(20, 0))

        # volume spinbox
        self.__volume = tk.IntVar()
        self.__volume.set(50)
        self.__volume_spinner = tk.Spinbox(root, from_=0, to=100, textvariable=self.__volume, state="readonly",
                                           bd=-2, readonlybackground="grey", width=3, font=def_font, justify="right",
                                           increment=2)
        self.__volume_spinner.grid(row=1, column=4, sticky="NS")
        self.__volume_spinner.bind("<ButtonRelease-1>",
                                   lambda event: self.__logger_info(f"Changed audio to {self.__volume.get()}"))

        def __change_audio():
            volume = self.__volume.get()
            self.__vlc_player.set_audio_volume(volume)
            # fix placement of speaker symbol
            self.__volume_spinner.configure(width=(len(str(volume)) + 1))

        self.__volume.trace_add("write", lambda *event: __change_audio())

        self.__logger_info("Finished setting up the root frame and its widgets")

        self.source = initial_source
        """Source (Path) of the currently running video file"""
        if initial_source is not None:
            self.__logger_info("Path to initial video file was given")
            self.__play_video(initial_source)
        self.__open_window()

    def __open_window(self):
        """Open the root window with initial width and height and display it"""
        self.__logger_info("Start displaying the root frame")
        self.__root.geometry("400x400")
        self.__root.lift()
        self.__root.mainloop()

    def __close_window(self):
        """
        Closes the root window and related components such as the vlc video player
        """
        self.__logger_info("Start releasing media files and close root frame")
        self.__vlc_player.stop_media()
        self.__root.destroy()
        self.__logger_info("Media files were released and the root frame closed")

    def __open_video(self):
        """
        Opens a dialog to select a video file to open and if a file was selected,
        closes the current video and opens the new one
        """
        self.__logger_info("Menubar File->Open was clicked")
        self.__pause_video()
        self.__logger_info("Open File Chooser dialog to open video file")
        new_source = filedialog.askopenfilename(title="Select video file")
        if len(new_source) != 0 and new_source != self.source:
            self.__logger_info(f"Try to open file {new_source}")
            old_source = self.source
            self.__vlc_player.stop_media()
            try:
                self.__play_video(new_source)
            except:
                self.__logger_info("Could not play the new file")
                if old_source is not None:
                    self.__logger_info(f"Open previous video file {old_source}")
                    self.__play_video(old_source)
            self.__resume_video()
        elif new_source == self.source:
            self.__logger_info("video file was identical to currently loaded one, continue with current one")
        else:
            self.__logger_info("No video file selected, continue with current one")

    def __play_video(self, source):
        """
        Loads the video file at path 'source' and starts displaying it.
        Also, updates the time bar and displays the remaining time the video will run
        (see self.__init_time_bar(..) for details)

        :param source: the path to the video file to play
        :type source: str
        """
        self.__logger_info(f"Starting opening the video file {source}")
        self.source = source

        media_info = self.__vlc_player.open_media(source, self.__is_activated, self.__enc_manager)

        self.__play_button.configure(state="normal")

        self.__init_time_bar(media_info["duration_in_sec"])
        self.__time_bar.configure(state="normal")

        self.__logger_info("Successfully opened the video file and updated related widgets")
        self.__resume_video()

    def __pause_video(self, event=None):
        """Pauses the currently running video"""
        if event is not None:
            self.__logger_info("Ensure video is paused to allow jump to another position in the video file")
        else:
            time = self.__get_current_time(self.__time.get())
            self.__logger_info(f"Pause current video file at {time}")
        self.__play_button.configure(image=self.__play_img, command=self.__resume_video)
        self.__vlc_player.pause_media()

    def __resume_video(self):
        """Resumes the currently paused video"""
        time = self.__get_current_time(self.__time.get())
        self.__logger_info(f"Resume current video file at {time}")
        self.__play_button.configure(image=self.__stop_img, command=self.__pause_video)
        self.__vlc_player.resume_media()

    def __init_time_bar(self, length_in_sec):
        """
        Sets up the scrollbar used to jump between different time positions in the video file
        such that each unit move of the slider means one second. Additionally, self.__update_time
        is called to set the remaining time label to the duration of the video.

        :param length_in_sec: length of the current video file in seconds
        :type length_in_sec: int
        """
        self.__logger_info("Update time bar and label to fit video duration")

        # number of overall seconds to make time scroll bar work in units of seconds
        self.__time_bar.configure(to=length_in_sec)
        self.__time.set(0)

        self.__update_time(length_in_sec, 0)

    def __update_rest_time_label(self, length_in_sec, current_time_in_sec):
        """
        Updates the label showing the remaining duration of the video and
        ensures the format hh:mm:ss

        :param length_in_sec: duration of the video file in seconds
        :type length_in_sec: int
        :param current_time_in_sec: current time in the video file in seconds
        :type current_time_in_sec: int
        """
        # calculating length in hour:min:sec format for rest time label
        rest = length_in_sec - current_time_in_sec
        hours = rest // 3_600
        rest = rest % 3_600
        minutes = rest // 60
        rest = rest % 60
        seconds = rest

        # fill with zeros such that it follows the format hh:mm:ss
        unit_list = []
        for unit in [hours, minutes, seconds]:
            unit_list.append(str(unit).zfill(2))
        self.__rest_time_label.configure(text=":".join(unit_list))

    @staticmethod
    def __get_current_time(current_time_in_sec):
        """
        Returns the current time in the video file in hh:mm:ss format

        :param current_time_in_sec: the current time in the video file in seconds
        :type current_time_in_sec: int
        """
        # calculating length in hour:min:sec format for rest time label
        hours = current_time_in_sec // 3_600
        rest = current_time_in_sec % 3_600
        minutes = rest // 60
        rest = rest % 60
        seconds = rest

        # fill with zeros such that it follows the format hh:mm:ss
        unit_list = []
        for unit in [hours, minutes, seconds]:
            unit_list.append(str(unit).zfill(2))
        return ":".join(unit_list)

    def __update_time(self, length_in_sec, current_time_in_ms):
        """
        Updates the field self.__time with the current time and calls
        self.__update_rest_time_label to set the remaining time label to the duration of the video

        :param length_in_sec: duration of the video file in seconds
        :type length_in_sec: int
        :param current_time_in_ms: current time in the video file in milliseconds
        :type current_time_in_ms: int
        """
        self.__update_rest_time_label(length_in_sec, current_time_in_ms // 1000)
        self.__time.set(current_time_in_ms // 1000)

    def __switch_activation_state(self, index):
        """
        Depending on the field '__is_activated' either the Detector (Face recognition) is activated or deactivated,
        to make the calculation of surrounding rectangles simpler, resizing of the root window is only possible during
        the deactivated state
        :param index: the index of the detector menu item
        :type index: int
        """
        if self.__is_activated.get():
            self.__logger_info("Face detector/recognizer was activated")
            self.__menubar.entryconfigure(index, label="Detector (activated)")
        else:
            self.__logger_info("Face detector/recognizer was deactivated")
            self.__menubar.entryconfigure(index, label="Detector (deactivated)")

    def __open_encoding_creation_dialog(self, menu):
        """
        Opens first a dialog to choose a picture to derive the encoding from
        and then forwards it to the encoding manager which stores it in a file

        :param: the menu the submenu should be updated
        :type: tk.Menu
        """
        self.__logger_info("Menubar Encoding-> 'Add face encoding' was clicked")
        self.__pause_video()
        self.__logger_info("Open File Chooser dialog to select picture")
        pic_types = r"*.jpeg *.jpg *.JPG *.JPEG *.gif *.GIF *.png *.PNG"
        file_types = []
        for pic_type in pic_types.split(" "):
            file_types.append(("pictures", pic_type))
        new_source = filedialog.askopenfilename(title="Select picture",
                                                filetypes=file_types)

        if len(new_source) != 0:
            img = fr.load_image_file(new_source)
            encoding = fr.face_encodings(img, model="large", num_jitters=self.__num_jitters)[0]

            name = os.path.basename(new_source).split(".")[0]
            self.__enc_manager.add_encoding(name, encoding)

            menu.entryconfigure(0, label=f"Activate ({len(self.__enc_manager.known_face_encodings)} face encodings)",
                                state=tk.NORMAL)

    def __logger_info(self, msg):
        """
        Adds a log info entry starting with VideoPlayerWindow

        :param msg: the message to write
        :type msg: str
        """
        self.__logger.info(f"VideoPlayerWindow: {msg}")


def open_window(initial_source=None, num_jitters=20, frames_to_skip=3, face_recognition_model="hog"):
    """
    Open the video player window

    :param initial_source: The path to the video file to open during program start
    :type initial_source: str

    :param num_jitters: How many times to re-sample the face when calculating encoding
    :type num_jitters: int

    :param frames_to_skip: The number of frames to skip when face detection is activated
    :type frames_to_skip: int

    :param face_recognition_model: The model used for face recognition, either "cnn" which is accurate, slower and used GPU or
    "hog" which is faster but not as precise
    :type face_recognition_model: str
    """

    # starting VideoPlayerWindow with initial video path if given
    logging.basicConfig(filename="../video_face_recognition.log",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # set meaningful bounds
    if num_jitters > 100:
        num_jitters = 100
    elif num_jitters < 1:
        num_jitters = 1

    if frames_to_skip > 20:
        frames_to_skip = 20
    elif frames_to_skip < 0:
        frames_to_skip = 0

    if face_recognition_model not in ["cnn", "hog"]:
        face_recognition_model = "hog"

    if initial_source is not None:
        logger.info(f"Open VideoPlayerWindow with initial video {initial_source}")
    else:
        logger.info(f"Open VideoPlayerWindow without initial video")

    VideoPlayerWindow(logger, initial_source, num_jitters, frames_to_skip, face_recognition_model)