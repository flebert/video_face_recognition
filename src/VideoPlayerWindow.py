"""
Script which opens a tkinter frame with an included video player. The first input parameter
given over the command line should be the path to the video file to open. If the parameter is omitted
the frame is opened without any initial video file loaded.
"""

import os
import sys
import tkinter as tk
from tkinter import font, filedialog
from PIL import Image
from PIL.ImageTk import PhotoImage
import vlc


class VideoPlayerWindow:
    """
    Class which opens and manages a video player in a tkinter frame using the python-vlc library
    """

    def __init__(self, initial_source=None):
        """
        Constructor of the VideoPlayerWindow

        Creates the frame including the video player and loads the first
        video file if the path was given

        :param initial_source: path to the initial video file
        :type initial_source: str
        """
        # path where images for pictures are stored
        resource_path = os.path.join(os.path.abspath(__file__), "..", "..", "resources")

        # create root window and bind ways to close the window
        root = tk.Tk()
        root.title("Actor Face Recognition")
        root.bind("<Escape>", lambda event: self.__close_window())
        root.protocol("WM_DELETE_WINDOW", lambda: self.__close_window())
        root.grid_rowconfigure(0, weight=1)
        root.configure(bg="grey")
        self.__root = root
        """The root window containing all the video player and the widgets"""

        # setup menubar
        self.__menubar = tk.Menu(self.__root, tearoff=0)
        """The menubar of the main frame"""
        file = tk.Menu(self.__menubar, tearoff=0)
        file.add_command(label="Open", command=lambda: self.__open_video())
        self.__menubar.add_cascade(label="File", menu=file)
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
        self.__time_bar.bind("<Button-1>", self.__vlc_pause)
        self.__time_bar.bind("<ButtonRelease-1>", self.__vlc_jump_to_scale_pos)
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

        def __change_audio():
            volume = self.__volume.get()
            self.__player.audio_set_volume(volume)
            # fix placement of speaker symbol
            self.__volume_spinner.configure(width=(len(str(volume))+1))
        self.__volume.trace_add("write", lambda *event: __change_audio())

        # Creating VLC player
        self.__instance = vlc.Instance()
        """VLC instance used to create the media player"""
        self.__player = self.__instance.media_player_new()
        """VLC media player to play the video"""
        self.__vlc_event_manager = self.__player.event_manager()
        """VLC event manager used to catch changes in time"""
        self.__vlc_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged,
                                              lambda event: self.__update_time(self.__player.get_length(),
                                                                               self.__player.get_time()))
        self.source = initial_source
        """Source (Path) of the currently running video file"""
        if initial_source is not None:
            self.__play_video(initial_source)
        self.__open_window()

    def __open_window(self):
        """Open the root window with initial width and height and display it"""
        self.__root.geometry("400x400")
        self.__root.mainloop()

    def __close_window(self, source=None, destroy_root=True):
        """
        Closes the root window and related components such as the video file,
        method can also be used to close only the video file by setting destroy_root to False

        :param source: the path to the video file to close (if not given, the currently running one is used)
        :type source: int
        :param destroy_root: decision on whether the root window should also be closed
        :type destroy_root: bool
        """
        try:
            if source is None:
                file_name = os.path.basename(self.source)
            else:
                file_name = os.path.basename(source)
            file_name = file_name.split(".")[0]
            self.__instance.vlm_stop_media(file_name)
        except TypeError:
            # no media source was loaded
            pass
        if destroy_root:
            self.__root.destroy()

    def __open_video(self):
        """
        Opens a dialog to select a video file to open and if a file was selected,
        closes the current video and opens the new one
        """
        if self.source is not None:
            self.__vlc_pause()
        file = filedialog.askopenfilename(title="Select video file")
        if len(file) != 0 and file != self.source:
            source = self.source
            try:
                self.__close_window(destroy_root=False)
                self.__play_video(file)
            except:
                if source is not None:
                    self.__play_video(source)
            self.__resume_video()

    def __play_video(self, source):
        """
        Loads the video file at path 'source' and starts displaying it.
        Also, updates the time bar and displays the remaining time the video will run
        (see self.__init_time_bar(..) for details)

        :param source: the path to the video file to play
        :type source: str
        """
        self.source = source

        # Function to start player from given source
        Media = self.__instance.media_new(source)
        Media.get_mrl()
        self.__player.set_media(Media)

        # self.player.play()
        self.__player.set_hwnd(self.__frame.winfo_id())
        self.__player.play()
        self.__play_button.configure(state="normal")
        length_in_ms = self.__player.get_length()
        while length_in_ms == 0:
            length_in_ms = self.__player.get_length()
        self.__init_time_bar(length_in_ms)
        self.__time_bar.configure(state="normal")

    def __pause_video(self):
        """Pauses the currently running video"""
        self.__play_button.configure(image=self.__play_img, command=self.__resume_video)
        self.__player.pause()

    def __resume_video(self):
        """Resumes the currently paused video"""
        self.__play_button.configure(image=self.__stop_img, command=self.__pause_video)
        self.__player.play()

    def __init_time_bar(self, length_in_ms):
        """
        Sets up the scrollbar used to jump between different time positions in the video file
        such that each unit move of the slider means one second. Additionally, self.__update_time
        is called to set the remaining time label to the duration of the video.

        :param length_in_ms: length of the current video file in milliseconds
        :type length_in_ms: int
        """
        # number of overall seconds to make time scroll bar work in units of seconds
        self.__time_bar.configure(to=length_in_ms // 1000)
        self.__time.set(0)

        self.__update_time(length_in_ms, 0)

    def __update_rest_time_label(self, length_in_ms, current_time_in_ms):
        """
        Updates the label showing the remaining duration of the video and
        ensures the format hh:mm:ss

        :param length_in_ms: duration of the video file in milliseconds
        :type length_in_ms: int
        :param current_time_in_ms: current time in the video file in milliseconds
        :type current_time_in_ms: int
        """
        # calculating length in hour:min:sec format for rest time label
        rest = length_in_ms - current_time_in_ms
        hours = rest // 3_600_000
        rest = rest % 3_600_000
        minutes = rest // 60_000
        rest = rest % 60_000
        seconds = rest // 1000

        # fill with zeros such that it follows the format hh:mm:ss
        unit_list = []
        for unit in [hours, minutes, seconds]:
            unit_list.append(str(unit).zfill(2))
        self.__rest_time_label.configure(text=":".join(unit_list))

    def __update_time(self, length_in_ms, current_time_in_ms):
        """
        Updates the field self.__time with the current time and calls
        self.__update_rest_time_label to set the remaining time label to the duration of the video

        :param length_in_ms: duration of the video file in milliseconds
        :type length_in_ms: int
        :param current_time_in_ms: current time in the video file in milliseconds
        :type current_time_in_ms: int
        """
        self.__update_rest_time_label(length_in_ms, current_time_in_ms)
        self.__time.set(current_time_in_ms // 1000)

    def __vlc_pause(self, event=None):
        """
        Pauses the video in case the video is not already paused.
        Used to pause the video during the time the scrollbar slider is moved
        by the user.
        """
        if self.source is not None and "State.Paused" != str(self.__player.get_media().get_state()):
            self.__pause_video()

    def __vlc_jump_to_scale_pos(self, event=None):
        """
        Updates the position in the video file with the current time bar slider position and
        update the remaining duration label.
        Special case: If the video file ended before moving the slider, the video is restarted
        """
        if self.source is None:
            return
        if "State.Ended" == str(self.__player.get_media().get_state()):
            self.__play_video(self.__player.get_media().get_mrl())
        new_position = self.__time.get() / (self.__player.get_length() // 1000)
        self.__player.set_position(new_position)
        self.__update_rest_time_label(self.__player.get_length(), self.__player.get_time())


# starting VideoPlayerWindow with initial video path if given
if len(sys.argv) > 1:
    VideoPlayerWindow(sys.argv[1])
else:
    VideoPlayerWindow()
