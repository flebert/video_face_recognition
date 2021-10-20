import os

import vlc
import time
import tkinter as tk

from src.FrameHandler import FrameHandler


class VLCPlayer:
    events = {"MediaPlayerTimeChanged": vlc.EventType.MediaPlayerTimeChanged}

    def __init__(self, frame, logger):
        self.__instance = vlc.Instance()
        """VLC instance used to create the media player"""
        self.__player = self.__instance.media_player_new()
        """VLC media player to play the video"""
        self.__vlc_event_manager = self.__player.event_manager()
        """VLC event manager used to catch changes in time"""

        self.__frame = frame
        """Frame where the vlc player should be shown in"""

        self.logger = logger
        """Logging object"""

        self.__img_label = tk.Label(frame, bd=-2, bg="black")
        self.__img_label.grid(row=0, column=0)
        self.__frame.grid_columnconfigure(0, weight=1)

        self.__frame_handler = FrameHandler(self, self.__img_label)

        logger.info(f"{logger.vlc}: Finished setting up the vlc media player")

    def register_event(self, event_type, command):
        """
        Attached an event to the vlc event manager
        :param event_type: vlc.EventType
        :type event_type: str
        :param command: a function to be called once the event is triggered
        """
        if event_type in VLCPlayer.events:
            self.__vlc_event_manager.event_attach(VLCPlayer.events[event_type], command)

    def get_duration_in_sec(self):
        """
        Returns the duration of the media file in seconds

        :rtype int
        """
        return self.__player.get_length() // 1000

    def get_robust_duration_in_sec(self):
        """
        Returns the duration of the media file in seconds.
        It makes sure that the time was already updated and is not 0 or less.
        It waits at most 2 seconds and probes for the duration 1000 times.

        :rtype int
        """
        length = 0
        i = 0
        while length <= 0 and i < 1000:
            length = self.__player.get_length()
            i = i + 1
            time.sleep(0.002)
        return length // 1000

    def get_current_time_in_sec(self):
        """
        Return the current time position in the media file in seconds

        :rtype int
        """
        return self.__player.get_time() // 1000

    def get_current_time_in_ms(self):
        """
        Return the current time position in the media file in milliseconds

        :rtype int
        """
        return self.__player.get_time()

    def set_audio_volume(self, volume):
        """
        Sets the audio volume of the media file

        :param volume: audio volume [0, 100] to set to
        :type volume: int
        """
        self.__player.audio_set_volume(volume)

    def stop_media(self, media_path):
        """
        Stops the media associated to path media_path

        :param media_path: media file to close
        :type media_path: str
        """
        if self.__player.get_media() is not None:
            file_name = os.path.basename(media_path)
            file_name = file_name.split(".")[0]
            self.__instance.vlm_stop_media(file_name)
            self.logger.info(f"{self.logger.vlc}: Current media file stopped")
        else:
            self.logger.info(f"{self.logger.vlc}: No current media file to stop")

    def pause_media(self):
        """
        Pauses the media in case the media is not already paused.
        """
        if self.__player.get_media() is None:
            self.logger.info(f"{self.logger.vlc}: No media to pause found")
        elif vlc.State.Paused != self.__player.get_media().get_state():
            self.__player.pause()
            self.logger.info(f"{self.logger.vlc}: Media is now paused")
        else:
            self.logger.info(f"{self.logger.vlc}: Media was already paused")

    def resume_media(self):
        """
        Resumes the media in case the media is not already running
        """
        if self.__player.get_media() is None:
            self.logger.info(f"{self.logger.vlc}: No media to resume found")
        elif vlc.State.Playing != self.__player.get_media().get_state():
            self.__player.play()
            self.logger.info(f"{self.logger.vlc}: Resuming current media file")
        else:
            self.logger.info(f"{self.logger.vlc}: Media file was already running")

    def open_media(self, media_path):
        """
        Opens the media file and starts playing it

        :param media_path: path of the media file to open
        :type media_path: str
        """
        # Open media source
        self.logger.info(f"{self.logger.vlc}: Start opening media file {media_path}")
        media = self.__instance.media_new(media_path)
        media.get_mrl()
        self.__player.set_media(media)

        media.parse()

        self.__player.play()
        self.__frame_handler.start()
        self.logger.info(f"{self.logger.vlc}: Successfully opened the media file")

    def go_to_position(self, time_in_sec, update_gui_command, state_end_command):
        """
        Jump in the media file to the specified location

        :param time_in_sec: time location in seconds to jump to
        :type time_in_sec: int
        :param update_gui_command: function to call to update surrounding gui
        (two input params: duration and current time)
        :param state_end_command: function to call to handle the case that the media file already ended
        (function has the media resource locator as the input param)
        """
        media = self.__player.get_media()
        if media is None:
            return
        if vlc.State.Ended == media.get_state():
            self.logger.info(f"{self.logger.vlc}: Media file already ended, therefore restart it")
            state_end_command(media.get_mrl())
        new_position = time_in_sec / self.get_duration_in_sec()
        self.__player.set_position(new_position)
        update_gui_command(self.get_duration_in_sec(), self.get_current_time_in_sec())
        pos_str = "{:.2f}".format(new_position)
        self.logger.info(f"{self.logger.vlc}: Go to position {pos_str} of the media file")

    def get_fps(self):
        """
        Returns the fps of the currently running video file (if the media type supports it)
        """
        return self.__player.get_fps()

    def get_player(self):
        """
        Returns the vlc media player
        """
        return self.__player
