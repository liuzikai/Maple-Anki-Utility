import sqlite3


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
              ws.id,
              ws.word,
              lus.usage,
              bi.title,
              bi.authors,
              ws.category
            FROM WORDS AS ws
              LEFT JOIN LOOKUPS AS lus ON ws.id = lus.word_key
              LEFT JOIN BOOK_INFO AS bi ON lus.book_key = bi.id
            {}
            """.format("WHERE ws.category = 0" if new_only else "")
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
