"""
This script contains a class to access the video callback of a vlc player and use the frames to perform
face recognition and marking
"""
import ctypes

import cv2
import vlc
from PIL import Image, ImageTk
import numpy as np
import face_recognition as fr

CorrectVideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))


class FrameHandler:

    def __init__(self, vlc_player, label):
        self.vlc_player = vlc_player.get_player()

        self.label = label
        frame_name = label.winfo_parent()
        self.frame = label._nametowidget(frame_name)

        self.width, self.height = vlc.libvlc_video_get_size(self.vlc_player, 0)

        self.buffer_size = self.width * self.height * 4
        self.buf = (ctypes.c_ubyte * self.buffer_size)()
        self.buf_p = ctypes.cast(self.buf, ctypes.c_void_p)

        self.vlc_player.video_set_format("RV32", self.width, self.height, self.width * 4)

        self.__lockcb = self.__lock()
        self.__displaycb = self.__display()

        vlc.libvlc_video_set_callbacks(self.vlc_player, self.__lockcb, None, self.__displaycb, None)

    def __lock(self):
        @CorrectVideoLockCb
        def _lockcb(opaque, planes):
            planes[0] = self.buf_p

        return _lockcb

    def __display(self):
        @vlc.CallbackDecorators.VideoDisplayCb
        def _display(opaque, picture):
            img = Image.frombuffer("RGBA", (self.width, self.height),
                                   self.buf, "raw", "BGRA", 0, 1)
            cv2_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
            cv2_image = cv2.resize(cv2_image, self.__get_resize_size())
            # TODO: perform here the face detection and recognition
            cv2_image = cv2.cvtColor(np.array(cv2_image), cv2.COLOR_BGRA2RGB)
            img = Image.fromarray(cv2_image)
            ph = ImageTk.PhotoImage(img)
            self.label.config(image=ph)
            self.label.image = ph

        return _display

    def __get_resize_size(self):
        frame_width = self.frame.winfo_width()
        frame_height = self.frame.winfo_height()
        scale = min(frame_width / self.width, frame_height / self.height)
        return int(self.width * scale), int(self.height * scale)
