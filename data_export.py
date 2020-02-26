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

    @staticmethod
    def new_random_filename(extension):
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

    def generate_media(self, word, speaker):
        filename = DataExporter.new_random_filename("mp3")
        subprocess.run(["say", "-v", speaker, "-r", "175", "-o", self.temp_media_file, word])
        with open(os.devnull, 'w') as devnull:
            subprocess.run(['lame', '-m', 'm', self.temp_media_file, "%s/%s" % (self.media_path, filename)],
                           stdout=devnull, stderr=devnull)

        return filename

    @staticmethod
    def pronounce(word, speaker):
        subprocess.Popen(["say", "-v", speaker, "-r", "175", word])  # non-blocking

    def open_file(self, output_file):
        self.f = open(output_file, "w", encoding="utf-8")
    
    def escape_str(self, s: str):
        ret = s
        for k, v in self.OUTPUT_ESCAPES.items():
            ret = ret.replace(k, v)
        return ret

    def write_entry(self, subject, pronunciation, paraphrase, extension, example, hint, freq, has_r, has_s, has_d):
        
        self.f.write(self.OUTPUT_DELIMITER.join([
            self.escape_str(subject),
            self.escape_str(pronunciation),
            self.escape_str(paraphrase),
            self.escape_str(extension),
            self.escape_str(example),
            self.escape_str(hint),
            self.escape_str(str(freq)),
            self.escape_str(str(has_r)),
            self.escape_str(str(has_s)),
            self.escape_str(str(has_d))
        ]) + "\n")

    def close_file(self):
        self.f.close()
