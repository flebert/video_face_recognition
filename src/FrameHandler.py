import ctypes

import cv2
import vlc
from PIL import Image, ImageTk
import numpy as np

CorrectVideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))


class FrameHandler:
    video_width, video_height = (1, 1)
    buffer_size = 1
    buffer_1 = None
    buffer_1_p = None
    media_player = None
    label = None
    frame = None

    def __init__(self, vlc_player, label):
        media_player = vlc_player.get_player()
        FrameHandler.media_player = media_player

        vlc.libvlc_video_set_callbacks(media_player, _lockcb, None, _display, None)

        FrameHandler.label = label
        frame_name = label.winfo_parent()
        FrameHandler.frame = label._nametowidget(frame_name)

    def start(self):
        width, height = vlc.libvlc_video_get_size(FrameHandler.media_player, 0)
        _update_buffer(width, height)


def _update_buffer(width, height):
    FrameHandler.video_width, FrameHandler.video_height = width, height

    FrameHandler.buffer_size = width * height * 4
    FrameHandler.buffer_1 = (ctypes.c_ubyte * FrameHandler.buffer_size)()
    FrameHandler.buffer_1_p = ctypes.cast(FrameHandler.buffer_1, ctypes.c_void_p)

    FrameHandler.media_player.video_set_format("RV32", width, height, width * 4)


@CorrectVideoLockCb
def _lockcb(opaque, planes):
    planes[0] = FrameHandler.buffer_1_p

# TODO find out what blocks switch of media file
# TODO select frame rate to calculate


@vlc.CallbackDecorators.VideoDisplayCb
def _display(opaque, picture):
    img = Image.frombuffer("RGBA", (FrameHandler.video_width, FrameHandler.video_height),
                           FrameHandler.buffer_1, "raw", "BGRA", 0, 1)
    cv2_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
    cv2_image = cv2.resize(cv2_image, _get_resize_size())
    # TODO: perform here the face detection and recognition
    cv2_image = cv2.cvtColor(np.array(cv2_image), cv2.COLOR_BGRA2RGB)
    img = Image.fromarray(cv2_image)
    ph = ImageTk.PhotoImage(img)
    FrameHandler.label.config(image=ph)
    FrameHandler.label.image = ph


def _get_resize_size():
    frame_width = FrameHandler.frame.winfo_width()
    frame_height = FrameHandler.frame.winfo_height()
    scale = min(frame_width / FrameHandler.video_width, frame_height / FrameHandler.video_height)
    return int(FrameHandler.video_width * scale), int(FrameHandler.video_height * scale)
