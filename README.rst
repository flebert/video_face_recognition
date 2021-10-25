==============================
Actor Face Recognition Project
==============================
|  This library provides a simple tkinter GUI to view video files and recognize
   faces in real-time. These faces can be labelled using beforehand created face encodings.
|  As such, the library provides the necessary functionality to create these face
   encodings and open/display videos based on menu buttons.
|  To achieve this, this library builds a wrapper to the python-vlc library to load and display the video
   files using the VLC software. To recognize/detect faces and to create face encodings
   `face_recognition <https://github.com/ageitgey/face_recognition>`_ is used.
   `face_recognition <https://github.com/ageitgey/face_recognition>`_ employs
   `dlib's <http://dlib.net/>`_ deep learning face recognition model.

Trivia
    During development and testing, movie trailers and face encodings of their actors were used.
    This is the sole reason why the following examples focus on the Joker
    trailer and I named this project **Actor** Face Recognition. It can be used for any video
    and all human faces.



Features
============

Installation
============
This Software uses the python binding to access the locally installed VLC media
player. Therefore, it can only be run if VLC is installed on the machine.

Usage
======
