"""
This script contains a class to access the video callback of a vlc player and use the frames to perform
face recognition and marking
"""
import ctypes

import cv2
import face_recognition as fr
import numpy as np
import vlc
from PIL import Image, ImageTk

CorrectVideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))


class FrameHandler:

    def __init__(self, vlc_player, label, is_detection_activated, encoding_manager, frames_to_skip,
                 face_recognition_model):
        """
        Constructor of the FrameHandler

        Manages the the video callback of the vlc media player such that each frame can be
        processed individually

        :param vlc_player: the VLCPlayer it receives the callback from
        :type vlc_player: video_player.VLCPlayer.VLCPlayer

        :param is_detection_activated: a tkinter.BoolVar checking whether the face recognition is activated or not

        :param encoding_manager: a unit managing available encodings
        :type encoding_manager: video_player.EncodingManager.EncodingManager

        :param frames_to_skip: Number of frames to skip, meaning if frames_to_skip=3 only every fourth frame is shown
        :type frames_to_skip: int

        :param face_recognition_model: The model used for face recognition, either "cnn" which is accurate, slower and
        used GPU or "hog" which is faster but not as precise
        :type face_recognition_model: str
        """
        self.__face_recognition_model = face_recognition_model

        self.vlc_player = vlc_player.get_player()

        self.label = label
        frame_name = label.winfo_parent()
        self.frame = label._nametowidget(frame_name)

        self.width, self.height = vlc.libvlc_video_get_size(self.vlc_player, 0)

        self.buffer_size = self.width * self.height * 4
        self.buf = (ctypes.c_ubyte * self.buffer_size)()
        self.buf_p = ctypes.cast(self.buf, ctypes.c_void_p)

        self.enc_manager = encoding_manager

        self.vlc_player.video_set_format("RV32", self.width, self.height, self.width * 4)

        self.__lockcb = self.__lock()
        self.__displaycb = self.__display()

        vlc.libvlc_video_set_callbacks(self.vlc_player, self.__lockcb, None, self.__displaycb, None)

        self.__is_detection_activated = is_detection_activated

        # number of frame shown to allow skipping of certain ones
        self.__frame_nr = 0

        # how many frame are shown/skipped
        self.__frame_to_show = frames_to_skip + 1

        # Face encodings/locations of last checked frame
        self.__face_locations = []
        self.__face_encodings = []

    def __lock(self):
        @CorrectVideoLockCb
        def _lockcb(opaque, planes):
            planes[0] = self.buf_p

        return _lockcb

    def __display(self):
        """
        Displays the processed frames received by the vlc media player
        """
        @vlc.CallbackDecorators.VideoDisplayCb
        def _display(opaque, picture):
            img = Image.frombuffer("RGBA", (self.width, self.height),
                                   self.buf, "raw", "BGRA", 0, 1)
            cv2_image = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2RGB)
            cv2_image = cv2.resize(cv2_image, self.__get_resize_size())

            if self.__frame_nr % self.__frame_to_show == 0 or not self.__is_detection_activated.get():
                if self.__is_detection_activated.get() and len(self.enc_manager.known_face_names):
                    self.__face_locations, self.__face_encodings = self.__perform_face_detection(cv2_image)
                    if len(self.__face_locations) > 0:
                        cv2_image = self.__draw_face_rectangle(cv2_image)

                cv2_image = cv2.cvtColor(np.array(cv2_image), cv2.COLOR_BGRA2RGB)
                img = Image.fromarray(cv2_image)
                ph = ImageTk.PhotoImage(img)
                self.label.config(image=ph)
                self.label.image = ph

            self.__frame_nr += 1

        return _display

    def __get_resize_size(self):
        """
        Get the resize size of the image such that it is centered in the root frame
        """
        frame_width = self.frame.winfo_width()
        frame_height = self.frame.winfo_height()
        scale = min(frame_width / self.width, frame_height / self.height)
        return int(self.width * scale), int(self.height * scale)

    def __perform_face_detection(self, img):
        """
        Detects face locators in the input img and uses the discovered face locators (potentially for multiple faces)
        an calculates the face encodings

        :param img: image to perform face recognition on
        """
        face_locations = fr.face_locations(img, model=self.__face_recognition_model, number_of_times_to_upsample=1)
        face_encodings = fr.face_encodings(img, face_locations)

        return face_locations, face_encodings

    def __draw_face_rectangle(self, img):
        """
        Draws on the input image around the discovered faces a red box with a label on the bottom
        """
        for (top, right, bottom, left), face_encoding in zip(self.__face_locations, self.__face_encodings):
            # See if the face is a match for the known face(s)
            matches = fr.compare_faces(self.enc_manager.known_face_encodings, face_encoding)

            name = "unknown"

            # Use known face with the smallest distance to the new face
            face_distances = fr.face_distance(self.enc_manager.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.enc_manager.known_face_names[best_match_index]

            # Draw a box around the face
            img = cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            (text_width, text_height), baseline = cv2.getTextSize(name, cv2.FONT_HERSHEY_PLAIN, 1, 2)
            img = cv2.rectangle(img, (left, bottom - text_height), (right, bottom), (0, 0, 255), -1)
            img = cv2.putText(img, name, (left + 6, bottom), cv2.FONT_HERSHEY_PLAIN, 1,
                              (255, 255, 255), 2)

        return img
