import os
import sys

from src.VideoPlayer.VideoPlayerWindow import VideoPlayerWindow

resource_path = os.path.join(os.path.abspath(__file__), "..", "..", "resources")
if len(sys.argv) > 1:
    VideoPlayerWindow(sys.argv[1])
else:
    VideoPlayerWindow()