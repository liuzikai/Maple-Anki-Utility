# -*- coding: utf-8 -*-

from data_source import *
from data_exporter import *
from html_cleaner import *
from PyQt5 import QtCore, QtGui
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum


class RecordStatus(Enum):
    UNVIEWED = 0   # not viewed yet
    TOPROCESS = 1  # already viewed at least one (has been pronounced)
    CONFIRMED = 2
    DISCARDED = 3


@dataclass
class Record:
    cid: int
    subject: str
    status: RecordStatus = RecordStatus.UNVIEWED
    db_id: Optional[str] = None
    pronunciation: str = "Unknown"
    paraphrase: str = ""
    extension: str = ""
    example: str = ""
    source_enabled: bool = False  # need to preserve source even not enabled, do not combine with source
    source: str = '<div align="right" style="font-size:12px"></div>'
    hint: str = ""
    image: Optional[QtGui.QPixmap] = None
    freq: int = 0
    freq_note: str = ""
    cards: str = "R"
    suggestion: Optional[str] = None
    saved_as_subject: Optional[str] = None


class DataManager(QtCore.QObject):

    record_status_changed = QtCore.pyqtSignal(int, RecordStatus, RecordStatus)  # cid, old_status, new_status
    record_inserted = QtCore.pyqtSignal(int, bool)  # cid, batch_loading(True)/add_single(False)
    record_cleared = QtCore.pyqtSignal()
    record_count_changed = QtCore.pyqtSignal()
    batch_load_started = QtCore.pyqtSignal()
    batch_load_finished = QtCore.pyqtSignal()

    def __init__(self, output_path: str, media_path: str):

        super().__init__()

        self._db: Optional[DB] = None

        self._records: List[Record] = []
        self._counts: Dict[RecordStatus, int] = {
            RecordStatus.UNVIEWED: 0,
            RecordStatus.TOPROCESS: 0,
            RecordStatus.CONFIRMED: 0,
            RecordStatus.DISCARDED: 0
        }

        self._output_path: str = output_path
        self._media_path: str = media_path
        self._exporter: Optional[DataExporter] = None  # lazy construction

    def __del__(self):
        if self._db is not None:
            del self._db
        if self._exporter is not None:
            self._exporter.close_file()
            del self._exporter

    def get(self, cid: int) -> Record:
        return self._records[cid]

    def count(self, status: Optional[RecordStatus] = None) -> int:
        if status is None:
            return len(self._records)
        else:
            return self._counts[status]

    def clear(self) -> None:
        """Clear all records and emit signals."""
        self._records.clear()
        self._counts = {
            RecordStatus.UNVIEWED: 0,
            RecordStatus.TOPROCESS: 0,
            RecordStatus.CONFIRMED: 0,
            RecordStatus.DISCARDED: 0
        }
        self.record_cleared.emit()
        self.record_count_changed.emit()

    def reload_kindle_data(self, db_file: str) -> bool:
        """
        Clear _records and load _records from Kindle.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(db_file):
            return False

        # Set up database to KindleDB
        if self._db is not None:
            del self._db
            self._db = None
        self._db = KindleDB(db_file)

        self._reload_from_db()

        return True

    def reload_csv_data(self, csv_file: str) -> bool:
        """
        Clear _records and load _records from CSV file.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(csv_file):
            return False

        # Setup database to CSV DB
        if self._db is not None:
            del self._db
            self._db = None
        self._db = CsvDB(csv_file)

        self._reload_from_db()

        return True

    def reload_things_list(self, things_list: str) -> None:
        """
        Clear _records and load _records from given Things list.
        :return: None
        """
        # Setup database to Things DB
        if self._db is not None:
            del self._db
            self._db = None
        self._db = ThingsDB(things_list)

        self._reload_from_db()

    def _reload_from_db(self) -> None:

        self.clear()  # will emit signals

        self.batch_load_started.emit()

        raw_record = self._db.fetch_all(new_only=True)
        for raw in raw_record:
            r = Record(
                cid=len(self._records),  # use new index in self._records as cid
                subject=raw["subject"],
                db_id=raw["word_id"],
                example=raw["usage"].replace(raw["subject"], u"<b>%s</b>" % raw["subject"]),
                source_enabled=(raw["source"] != ""),
                source=raw["source"]
            )
            self._records.append(r)
            self.record_inserted.emit(r.cid, True)

        self._counts[RecordStatus.UNVIEWED] = len(self._records)
        self._counts[RecordStatus.TOPROCESS] = self._counts[RecordStatus.CONFIRMED] = self._counts[RecordStatus.DISCARDED] = 0

        self.record_count_changed.emit()  # need to be ahead of batch_load_finished to enable editor

        self.batch_load_finished.emit()

    def set_status(self, cid: int, status: RecordStatus) -> None:
        """Set record status."""

        r = self._records[cid]
        # Even if the state is the same, we still do retract-save process since some entry may have been changed

        old_status = r.status

        if old_status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED] and status in [RecordStatus.UNVIEWED, RecordStatus.TOPROCESS]:
            if self._db is not None and r.db_id is not None:
                self._db.set_word_mature(r.db_id, 0)  # retract db status

        if old_status == RecordStatus.CONFIRMED:  # regardless of new status
            if self._exporter is not None:
                self._exporter.retract_subject(r.saved_as_subject)
                r.saved_as_subject = None

        self._counts[old_status] -= 1
        r.status = status
        self._counts[status] += 1

        # Save record and commit changes
        if status == RecordStatus.CONFIRMED:
            if self._exporter is None:
                self._construct_exporter()
            self._save_entry(cid)

        if status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            if self._db is not None and r.db_id is not None:
                self._db.set_word_mature(r.db_id, 100)
                self._db.commit_changes()

        self.record_status_changed.emit(cid, old_status, status)
        self.record_count_changed.emit()

    def _construct_exporter(self) -> None:
        save_file = "%s/maple-%s.txt" % (self._output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        self._exporter = DataExporter(self._media_path)
        self._exporter.open_file(save_file)

    def _save_entry(self, cid: int) -> None:
        r = self._records[cid]

        example = clean_html(r.example)
        if r.source_enabled and r.source != "":
            example += "<br>" + r.source
        mp3 = self._exporter.generate_media(r.subject, r.pronunciation) if r.pronunciation != "Unknown" else ""
        paraphrase = clean_html(r.paraphrase)
        if r.image is not None:

            img_file = self._exporter.new_random_filename("png")
            # Retry until there is no duplication
            while os.path.exists(os.path.join(self._exporter.media_path, img_file)):
                img_file = self._exporter.new_random_filename("png")

            r.image.save(os.path.join(self._exporter.media_path, img_file))
            paraphrase += '<div><br><img src="%s"><br></div>' % img_file

        self._exporter.write_entry(r.subject,
                                   "[sound:%s]" % mp3,
                                   paraphrase,
                                   clean_html(r.extension),
                                   example,
                                   r.hint,
                                   r.freq,
                                   "1" if "R" in r.cards else "",
                                   "1" if "S" in r.cards else "",
                                   "1" if "D" in r.cards else "")

        r.saved_as_subject = r.subject

    def add_new_single_entry(self, subject: str = "", example: str = "", source_enabled: bool = False,
                             source: str = '<div align="right" style="font-size:12px"></div>') -> int:
        """Add a new single entry and return its cid. Trigger record_inserted and record_count_changed signals."""

        cid = len(self._records)
        self._records.append(Record(
            cid=cid,
            subject=subject,
            example=example,
            source_enabled=source_enabled,
            source=source
        ))

        self._counts[RecordStatus.UNVIEWED] += 1
        self.record_inserted.emit(cid, False)
        self.record_count_changed.emit()
        return cid

    @staticmethod
    def pronounce(word: str, speaker: str) -> None:
        DataExporter.pronounce(word, speaker)
