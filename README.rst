==============================
Video Face Recognition Project
==============================
|  This library provides a simple tkinter GUI to view video files and recognize
   faces in real-time. These faces can be labelled using beforehand created face encodings.
|  As such, the library provides the necessary functionality to create these face
   encodings and open/display videos based on menu buttons.
|  To achieve this, this library builds a wrapper to the `python-vlc <https://github.com/oaubert/python-vlc>`_
   library to load and display the video
   files using the VLC software. To recognize/detect faces and to create face encodings
   `face_recognition <https://github.com/ageitgey/face_recognition>`_ is used.
   `face_recognition <https://github.com/ageitgey/face_recognition>`_ employs
   `dlib's <http://dlib.net/>`_ deep learning face recognition model.

Trivia
    During development and testing, movie trailers and face encodings of their actors were used.
    This is the sole reason why the following examples focus on the Joker
    trailer. It can be used for any video and all human faces.



Features
============

Installation
============
Important
    This Software uses the python bindings to access the locally installed VLC media
    player. Therefore, **VLC has to be installed on the machine**.

|  As a packaging and dependency management tool I used `Poetry <https://python-poetry.org/>`_.
   Therefore, Poetry has to be installed. For a detailed guide view the documentation
   `here <https://python-poetry.org/docs/#installation>`_.
|  Once Poetry is installed and the git repository was downloaded. Ideally all one has
   to do is to run in the project directory:

    poetry install

|  to install the dependencies listed in the poetry.lock file. If it was successful, congratulations
   you are already finished with the installation.
|  What if it fails:

    Most likely the python version you used was not compatible.
    For reference, during development I used the version 3.8.10 during the setup.


How to open the video player ?
==============================
To open the GUI including the video player and tkinter frame one has to:

#. Navigate into the video_face_recognition directory
#. Open a python interpreter
#. Import the video_player module
#. |  Open the window using the so called open_window() method
   |  (Alternatively open_window accepts one parameter, the path to an initial video file which should be opened.)

Note:
 Video files can also be switched using the GUI later one.

**Example using Windows 10**::

    cd path_to_directory\video_face_recognition
    py
    import video_player as vp
    # without initial video file
    vp.open_window()

    # or with an initial video file
    vp.open_window("JOKER.mp4")

