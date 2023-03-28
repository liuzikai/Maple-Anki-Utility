#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime
import subprocess
from abc import ABC, abstractmethod


class DB(ABC):
    """
    Abstract base class for MapleVocabUtility data source.
    """

    DATA_DICT = "data/"
    BACKUP_SUBDICT = "backup/"

    @abstractmethod
    def fetch_all(self, new_only: bool) -> [dict]:
        """
        Fetch all entries in the data base. Each item in the return is a dict with the following keys:
        - "word_id" -> str
        - "subject" -> str
        - "usage" -> str
        - "source" -> str
        Can throw RuntimeError.
        :param new_only: Only fetch new entries
        :return: The list of entries in the database
        """
        pass

    @abstractmethod
    def set_word_mature(self, word_id: str, category: int) -> None:
        """
        Set an entry as new/learned. The change may be cached and not taking effect until calling commit_changes()
        Can throw RuntimeError.
        :param word_id: ID from fetch_all()
        :param category: 0 for new, 100 for learned
        :return: None
        """
        pass

    @abstractmethod
    def commit_changes(self) -> None:
        """
        Commit changes of setting of word mature.
        Can throw RuntimeError.
        :return: None
        """
        pass

    @staticmethod
    def backup_file(file: str, suffix: str = "") -> None:
        """
        Make a copy of the file as backup at current directory
        :param file:
        :param suffix:
        :return:
        """

        if not os.path.exists(DB.DATA_DICT + DB.BACKUP_SUBDICT):
            os.makedirs(DB.DATA_DICT + DB.BACKUP_SUBDICT)

        backup_name = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        if suffix != "":
            backup_name += "_" + suffix
        backup_full_name = DB.DATA_DICT + DB.BACKUP_SUBDICT + backup_name

        subprocess.Popen(['bash', '-c',
                          'cp "%s" "%s" && tar -czf "%s.tar.gz" "%s" && rm "%s"' %
                          (file, backup_full_name, backup_full_name, backup_full_name, backup_full_name)])


class ThingsDB(DB):

    def __init__(self, things_list: str):
        self.things_list = things_list
        self.word_categories = {}

    def fetch_all(self, new_only: bool) -> [dict]:
        records = []
        script = """
            set retList to {}
            tell application "Things3"
                repeat with toDo in to dos of project "%s"
                    set end of retList to (name of toDo & "😅" & notes of toDo)
                end repeat
            end tell
            set AppleScript's text item delimiters to "🥲"
            set retString to retList as string
            return retString
        """ % self.things_list
        p = subprocess.Popen(["osascript"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(script.encode())
        if p.returncode != 0:
            raise RuntimeError(f"Failed to run applescript to fetch word list.\n"
                               f"Please make sure Things 3 is installed and the list is configured properly.\n\n"
                               f"{err.decode('utf-8')}")

        for entry in out.decode("utf-8").split("🥲"):
            entry = entry.strip()
            if len(entry) == 0:
                continue
            p = entry.split("😅")
            assert len(p) == 2, "Invalid applescript output entry"
            records.append({
                "word_id": p[0],  # using word as word_id
                "subject": p[0],
                "usage": p[1],
                "source": "",
            })
            self.word_categories[p[0]] = 0

        return records

    def set_word_mature(self, word_id: str, category: int) -> None:

        if self.word_categories[word_id] == category:
            return

        if category == 100:
            script = f"""
                tell application "Things3"
                    set proj to project "{self.things_list}"
                    set toDo to to do named "{word_id}" of proj
                    delete toDo
                end tell
            """
        else:
            script = f"""
                tell application "Things3"
                    set toDo to to do named "{word_id}" of list "Trash"
                    set project of toDo to project "{self.things_list}"
                end tell
            """

        # Move to-do immediately instead of waiting for commit_changes(), but in async way
        p = subprocess.Popen(["osascript"], stdin=subprocess.PIPE)
        p.stdin.write(script.encode())
        p.stdin.close()

        self.word_categories[word_id] = category

    def commit_changes(self) -> None:
        pass


class CsvDB(DB):
    """
    CSV data source. The csv should have 5 columns: subject, usage, title, authors, category. The first line of the
    file is regarded as heading and gets discarded.
    """

    def __init__(self, db_file):
        self.db_file = db_file
        self.csv_first_line = None
        self.csv_data = []

    def fetch_all(self, new_only: bool) -> [dict]:

        DB.backup_file(self.db_file, suffix=os.path.basename(self.db_file))

        # Fetch data from DB, preserving all data.
        # self.csv_data = list of [subject, usage, title, authors, category, ...]
        with open(self.db_file, "r", encoding="utf-8") as file:
            self.csv_first_line = file.readline()
            if len(self.csv_first_line.split(",")) < 5:
                raise RuntimeError("CSV file column number incorrect. At least 5 columns are required "
                                   "([subject, usage, title, authors, category], while the content can be empty.)")
            # Discard the first line
            for line in file:
                self.csv_data.append(line.split(","))

        # Process entries from DB
        records = []
        for i in range(len(self.csv_data)):
            entry = self.csv_data[i]
            if not new_only or entry[4] != "100":
                source = ""
                if entry[2] != "":
                    source += '<div align="right" style="font-size:12px"><I>%s</I>' % entry[2]
                    if entry[3] != "":
                        source += ', %s' % entry[3]
                    source += "</div>"
                records.append({
                    "word_id": str(i),  # use line number as word_id
                    "subject": entry[0],
                    "usage": entry[1],
                    "source": source,
                })

        return records

    def set_word_mature(self, word_id: str, category: int) -> None:
        self.csv_data[int(word_id)][4] = str(category)

    def commit_changes(self):
        with open(self.db_file, "w", encoding="utf-8") as file:
            file.writelines(self.csv_first_line)
            for entry in self.csv_data:
                file.writelines(",".join(entry))


class KindleDB(DB):
    """
    Kindle vocabulary builder database. Using SQLite3 format.
    """

    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        DB.backup_file(self.db_file, "kindle")

    def fetch_all(self, new_only: bool) -> [dict]:
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
                "word_id": word_id,  # use kindle db id as word_id
                "subject": word,
                "usage": usage,
                "source": '<div align="right" style="font-size:12px"><I>%s</I>, %s</div>' % (title, authors),
            })

        return records

    def set_word_mature(self, word_id: str, category: int) -> None:
        self.conn.execute(
            """
            UPDATE words SET category = ? WHERE id = ?
            """, (category, str(word_id))
        )

    def commit_changes(self) -> None:
        self.conn.commit()

    def __del__(self):
        self.conn.close()


def eject_kindle_volume():
    os.system("hdiutil unmount /Volumes/Kindle")
