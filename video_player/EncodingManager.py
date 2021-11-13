"""
A script to handle read/writes of face encodings from/into files of type .encoding
"""
import os
import pickle
import logging


class EncodingManager:

    def __init__(self, logger):
        """
        Constructor of the EncodingManager

        Manages the known face encodings and names, provides functionality to read and persist them

        :param logger: object used to perform logging
        :type logger: logging.Logger
        """
        self.__encodings_path = os.path.join(os.path.abspath(__file__), "..", "..", "encodings")
        self.known_face_names = []
        self.known_face_encodings = []

        self.__logger = logger

        self.__logger_info(f"Searching {self.__encodings_path} for face encodings")

        count = 0
        with os.scandir(self.__encodings_path) as entries:
            for entry in entries:
                file_name, ending = entry.name.split(".")
                if entry.is_file() and ending == "encoding":
                    with open(entry.path, 'rb') as encoding_file:
                        count = count + 1
                        encoding = pickle.load(encoding_file)
                        self.known_face_encodings.append(encoding)
                        self.known_face_names.append(file_name)
        self.__logger_info(f"{count} face encodings were found with names {self.known_face_names}")

    def add_encoding(self, name, encoding):
        """
        Adds an encoding to the encoding manager and writes in back into a "name".encoding file
        """
        file_name = name+".encoding"
        path = os.path.join(self.__encodings_path, file_name)
        if os.path.exists(path):
            self.__logger.warning(f"EncodingManager: file {path} already exists")
            return False
        else:
            with open(path, "wb") as encoding_file:
                pickle.dump(encoding, encoding_file)
            self.known_face_names.append(name)
            self.known_face_encodings.append(encoding)
            return True

    def __logger_info(self, msg):
        """
        Adds a log info entry starting with EncodingManager

        :param msg: the message to write
        :type msg: str
        """
        self.__logger.info(f"EncodingManager: {msg}")