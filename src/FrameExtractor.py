import ctypes

import vlc
from PIL import Image, ImageTk

CorrectVideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))


class FrameExtractor:
    video_width, video_height = (1, 1)
    buffer_size = 1
    buffer_1 = None
    buffer_1_p = None
    media_player = None
    label = None
    frame = None

    def __init__(self, vlc_player, label):
        media_player = vlc_player.get_player()
        FrameExtractor.media_player = media_player

        vlc.libvlc_video_set_callbacks(media_player, _lockcb, None, _display, None)

        FrameExtractor.label = label
        frame_name = label.winfo_parent()
        FrameExtractor.frame = label._nametowidget(frame_name)

    def start(self):
        width, height = vlc.libvlc_video_get_size(FrameExtractor.media_player, 0)
        _update_buffer(width, height)


def _update_buffer(width, height):
    FrameExtractor.video_width, FrameExtractor.video_height = width, height

    FrameExtractor.buffer_size = width * height * 4
    FrameExtractor.buffer_1 = (ctypes.c_ubyte * FrameExtractor.buffer_size)()
    FrameExtractor.buffer_1_p = ctypes.cast(FrameExtractor.buffer_1, ctypes.c_void_p)

    FrameExtractor.media_player.video_set_format("RV32", width, height, width * 4)


@CorrectVideoLockCb
def _lockcb(opaque, planes):
    planes[0] = FrameExtractor.buffer_1_p


# TODO switch Pillow to Opencv, add another buffer see github,
#       select frame rate to calculate and check for pause


@vlc.CallbackDecorators.VideoDisplayCb
def _display(opaque, picture):
    img = Image.frombuffer("RGBA", (FrameExtractor.video_width, FrameExtractor.video_height),
                           FrameExtractor.buffer_1, "raw", "BGRA", 0, 1)
    img = img.resize(_get_resize_size())
    ph = ImageTk.PhotoImage(img)
    FrameExtractor.label.config(image=ph)
    FrameExtractor.label.image = ph


def _get_resize_size():
    frame_width = FrameExtractor.frame.winfo_width()
    frame_height = FrameExtractor.frame.winfo_height()
    scale = min(frame_width/FrameExtractor.video_width, frame_height/FrameExtractor.video_height)
    return int(FrameExtractor.video_width*scale), int(FrameExtractor.video_height*scale)