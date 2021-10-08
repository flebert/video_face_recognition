import os
import tkinter as tk
from tkinter import font, filedialog
from PIL import Image
from PIL.ImageTk import PhotoImage
import vlc


class VideoPlayerWindow:
    def __init__(self, initial_source=None):
        # path where images for pictures are stored
        resource_path = os.path.join(os.path.abspath(__file__), "..", "..", "..", "resources")

        # root window
        root = tk.Tk()
        root.title("Actor Face Recognition")
        root.bind("<Escape>", lambda event: self.__close_window())
        root.protocol("WM_DELETE_WINDOW", lambda: self.__close_window())
        root.grid_rowconfigure(0, weight=1)
        root.configure(bg="grey")
        self.root = root

        # menubar
        self.menubar = tk.Menu(self.root, tearoff=0)
        file = tk.Menu(self.menubar, tearoff=0)
        file.add_command(label="Open", command=lambda: self.__open_video())
        self.menubar.add_cascade(label="File", menu=file)
        self.root.config(menu=self.menubar)

        # setting default font
        def_font = font.nametofont("TkDefaultFont")
        def_font.config(size=12)

        # frame within root frame
        frame = tk.Frame(root, bg="black")
        frame.grid(row=0, column=0, columnspan=3, sticky="NESW")
        frame.grid_rowconfigure(0, weight=1)
        self.frame = frame

        # play button
        button_size = (30, 30)
        image = Image.open(os.path.join(resource_path, "play-button.png"))
        resized = image.resize(button_size)
        self.play_img = PhotoImage(resized)
        image = Image.open(os.path.join(resource_path, "pause-btn.png"))
        resized = image.resize(button_size)
        self.stop_img = PhotoImage(resized)
        self.play_button = tk.Button(root, image=self.stop_img, bd=-2, bg="grey", command=self.__pause_video,
                                     activebackground="grey", state="disabled", height=40, width=40)
        self.play_button.grid(row=1, column=0, sticky="NWS")

        # time sliding bar and rest time
        self.time = tk.IntVar()
        self.time.set(0)
        self.time_bar = tk.Scale(root, variable=self.time, from_=0, to=10000, orient="horizontal", bg="grey",
                                 showvalue=0, troughcolor="black", highlightbackground="grey", state="disabled",
                                 sliderlength=10, repeatdelay=700)
        self.time_bar.grid(row=1, column=1, sticky="EW")
        self.time_bar.bind("<Button-1>", self.__vlc_pause)
        self.time_bar.bind("<ButtonRelease-1>", self.__vlc_jump_to_scale_pos)
        root.grid_columnconfigure(1, weight=1)

        self.rest_time_label = tk.Label(root, text="00:00:00", bd=-2, bg="grey")
        self.rest_time_label.grid(row=1, column=2, sticky="NSE")

        # Creating VLC player
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.vlc_event_manager = self.player.event_manager()
        self.vlc_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged,
                                            lambda event: self.__update_time(self.player.get_length(),
                                                                             self.player.get_time()))
        self.source = initial_source
        if initial_source is not None:
            self.play_video(initial_source)
        self.__open_window()

    def __open_window(self):
        self.root.geometry("400x400")
        self.root.mainloop()

    def __close_window(self, source=None, destroy_root=True):
        try:
            if source is None:
                file_name = os.path.basename(self.source)
            else:
                file_name = os.path.basename(source)
            file_name = file_name.split(".")[0]
            self.instance.vlm_stop_media(file_name)
        except TypeError:
            # no media source was loaded
            pass
        if destroy_root:
            self.root.destroy()

    def __open_video(self):
        file = filedialog.askopenfilename(title="Select video file")
        if len(file) != 0 and file != self.source:
            source = self.source
            try:
                self.__close_window(destroy_root=False)
                self.play_video(file)
            except:
                if source is not None:
                    self.play_video(source)

    def play_video(self, source):
        self.source = source

        # Function to start player from given source
        Media = self.instance.media_new(source)
        Media.get_mrl()
        self.player.set_media(Media)

        # self.player.play()
        self.player.set_hwnd(self.frame.winfo_id())
        self.player.play()
        self.play_button.configure(state="normal")
        length_in_ms = self.player.get_length()
        while length_in_ms == 0:
            length_in_ms = self.player.get_length()
        self.__init_time_bar(length_in_ms)

    def __pause_video(self):
        self.play_button.configure(image=self.play_img, command=self.__resume_video)
        self.player.pause()

    def __resume_video(self):
        self.play_button.configure(image=self.stop_img, command=self.__pause_video)
        self.player.play()

    def __init_time_bar(self, length_in_ms):
        # number of overall seconds to make time scroll bar work in units of seconds
        self.time_bar.configure(to=length_in_ms // 1000, state="normal")
        self.time.set(0)

        self.__update_time(length_in_ms, 0)

    def __update_rest_time_label(self, length_in_ms, current_time_in_ms):
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
        self.rest_time_label.configure(text=":".join(unit_list))

    def __update_time(self, length_in_ms, current_time_in_ms):
        self.__update_rest_time_label(length_in_ms, current_time_in_ms)
        self.time.set(current_time_in_ms // 1000)

    def __vlc_pause(self, event):
        if "State.Paused" != str(self.player.get_media().get_state()):
            self.__pause_video()

    def __vlc_jump_to_scale_pos(self, event=None):
        if "State.Ended" == str(self.player.get_media().get_state()):
            self.play_video(self.player.get_media().get_mrl())
        new_position = self.time.get() / (self.player.get_length() // 1000)
        self.player.set_position(new_position)
        self.__update_rest_time_label(self.player.get_length(), self.player.get_time())
