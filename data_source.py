#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime
import subprocess

data_dict = "data/"
backup_subdict = "backup/"


def eject_kindle_volume():
    os.system("hdiutil unmount /Volumes/Kindle")


def backup_file(file, suffix=""):

    if not os.path.exists(data_dict + backup_subdict):
        os.makedirs(data_dict + backup_subdict)

    backup_name = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    if suffix != "":
        backup_name += "_" + suffix
    backup_full_name = data_dict + backup_subdict + backup_name

    subprocess.Popen(['bash', '-c',
                      'cp "%s" "%s" && tar -czf "%s.tar.gz" "%s" && rm "%s"' %
                     (file, backup_full_name, backup_full_name, backup_full_name, backup_full_name)])


class CSVDB:

    def __init__(self, db_file):
        self.db_file = db_file
        self.changed = False
        self.csv_first_line = None
        self.csv_data = []

    def fetch_all(self, new_only):

        backup_file(self.db_file, suffix=os.path.basename(self.db_file))

        # Fetch data from DB, preserving all data.
        # self.csv_data = list of [subject, usage, title, authors, category, ...]
        with open(self.db_file, "r", encoding="utf-8") as file:
            self.csv_first_line = file.readline()
            if len(self.csv_first_line.split(",")) < 5:
                raise Exception("CSV file column number incorrect. At least 5 columns are required "
                                "([subject, usage, title, authors, category], while the content can be empty.)")
            # Discard the first line
            for line in file:
                self.csv_data.append(line.split(","))

        # Process entries from DB.
        records = []
        for i in range(len(self.csv_data)):
            entry = self.csv_data[i]
            if not new_only or entry[4] != "100":
                source = '<div align="right" style="font-size:12px"><I>%s</I>' % entry[2]
                if entry[3] != "":
                    source += ', %s' % entry[3]
                source += "</div>"
                records.append({
                    "word_id": str(i),
                    "subject": entry[0],
                    "usage": entry[1],
                    "source": source,
                })

        return records

    def set_word_mature(self, word_id, category):
        self.csv_data[int(word_id)][4] = str(category)

    def commit_changes(self):
        with open(self.db_file, "w", encoding="utf-8") as file:
            file.writelines(self.csv_first_line)
            for entry in self.csv_data:
                file.writelines(",".join(entry))


class KindleDB:

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        backup_file(self.db_file, "kindle")

    def fetch_all(self, new_only):
        # Fetch data from DB. Generate list of [id, word, usage, title, authors, category]
        entries = self.conn.execute(
            """
            SELECT
              WORDS.id,
              WORDS.word,
              LOOKUPS.usage,
              BOOK_INFO.title,
              BOOK_INFO.authors,
              WORDS.category
            FROM WORDS
              LEFT JOIN LOOKUPS ON WORDS.id = LOOKUPS.word_key
              LEFT JOIN BOOK_INFO ON LOOKUPS.book_key = BOOK_INFO.id
            {}
            """.format("WHERE WORDS.category = 0" if new_only else "")
        ).fetchall()

        # Process entries from DB.
        records = []
        for (word_id, word, usage, title, authors, category) in entries:
            records.append({
                "word_id": word_id,
                "subject": word,
                "usage": usage,
                "source": '<div align="right" style="font-size:12px"><I>%s</I>, %s</div>' % (title, authors),
            })

        return records

    def set_word_mature(self, word_id, category):
        self.conn.execute(
            """
            UPDATE words SET category = ? WHERE id = ?

            """, (category, str(word_id))
        )

    def commit_changes(self):
        self.conn.commit()

    def __del__(self):
        self.conn.close()
