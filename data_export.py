#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os
import html


class DataExporter:

    OUTPUT_DELIMITER = "\t"
    OUTPUT_ESCAPES = {
        "\n": "<br>",
        "\r": "<br>",
        # ";": "&#59;"
    }

    def __init__(self):
        # TODO: instead of hard-coding find a better way to acquire these paths
        self.media_path = "/Users/liuzikai/Library/Application Support/Anki2/liuzikai/collection.media"
        self.temp_media_file = "/tmp/isay.aiff"
        self.f = None

        self.media_proc = None

    def __del__(self):
        if self.media_proc is not None:
            # Wait for completion of media generation
            self.media_proc: subprocess.Popen
            self.media_proc.wait()
            assert self.media_proc.returncode == 0, "Fail to generate media"

    @staticmethod
    def new_random_filename(extension: str) -> str:
        """
        Returns a path using the given extension that may be used for
        writing out a temporary file.
        """

        from string import ascii_lowercase, digits
        alphanumerics = ascii_lowercase + digits

        from random import choice
        from time import time
        return '%x-%s.%s' % (
            int(time()),
            ''.join(choice(alphanumerics) for _ in range(30)),
            extension
        )

    def generate_media(self, word: str, speaker: str) -> str:
        if self.media_proc is not None:
            self.media_proc: subprocess.Popen
            self.media_proc.wait()
            assert self.media_proc.returncode == 0, "Fail to generate media"

        filename = DataExporter.new_random_filename("mp3")
        say_command = " ".join(["say", "-v", speaker, "-r", "175", "-o", self.temp_media_file, word])
        lame_command = " ".join(['lame', '-m', 'm', self.temp_media_file, "%s/%s" % (self.media_path, filename)])
        self.media_proc = subprocess.Popen(say_command + " && " + lame_command, shell=True,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # non-blocking
        return filename

    @staticmethod
    def pronounce(word: str, speaker: str) -> None:
        subprocess.Popen(["say", "-v", speaker, "-r", "175", word])  # non-blocking

    def open_file(self, output_file: str) -> None:
        self.f = open(output_file, "w", encoding="utf-8")

    def file_opened(self) -> bool:
        return self.f is not None

    def close_file(self) -> None:
        self.f.close()
        self.f = None

    def escape_str(self, s: str):
        ret = s
        for k, v in self.OUTPUT_ESCAPES.items():
            ret = ret.replace(k, v)
        return ret

    def write_entry(self, subject: str, pronunciation: str, paraphrase: str, extension: str, example: str, hint: str,
                    freq: int, has_r: str, has_s: str, has_d: str):
        self.f.write(self.OUTPUT_DELIMITER.join([
            self.escape_str(subject),
            self.escape_str(pronunciation),
            self.escape_str(paraphrase),
            self.escape_str(extension),
            self.escape_str(example),
            self.escape_str(hint),
            self.escape_str(str(freq)),
            self.escape_str(has_r),
            self.escape_str(has_s),
            self.escape_str(has_d)
        ]) + "\n")
        self.f.flush()

    def retract_subject(self, subject: str) -> None:
        assert self.file_opened(), "No file opened"
        output_file = self.f.name

        # Close the output file
        self.close_file()

        # Read all lines and delete the specific line
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            line_num = -1
            for i in range(len(lines)):
                if lines[i].startswith(self.escape_str(subject) + self.OUTPUT_DELIMITER):
                    line_num = i
                    break
            assert line_num != -1, "Fail to find the line of given subject"
            del lines[line_num]

        # Re-open the output file and write back the revised content
        self.open_file(output_file)
        self.f.write("\n".join(lines))
