import sqlite3
import os


def eject_kindle_volume():
    os.system("hdiutil unmount /Volumes/Kindle")


class KindleDB:

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)

    def fetch_all(self, new_only):
        """

        :param new_only:
        :return: list of [id, word, usage, title, authors, category]
        """
        return self.conn.execute(
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

    def set_word_mature(self, word_id, category):
        self.conn.execute(
            """
            UPDATE words SET category = ? WHERE id = ?

            """, (category, str(word_id))
        )
        self.conn.commit()

    def __del__(self):
        self.conn.close()
