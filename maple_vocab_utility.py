#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import QTimer
from datetime import datetime
from enum import Enum
from pyquery import PyQuery
import urllib.parse

from maple_utility import *
from data_export import *
from data_source import *
from web_query import *

# db_file_ = "/Users/liuzikai/Documents/Programming/MapleVocabUtility/test_vocab.db"
db_file_ = "/Volumes/Kindle/system/vocabulary/vocab.db"
output_path_ = "/Users/liuzikai/Desktop"
card_rd_threshold_ = 4
auto_query_delay_ = 3000  # [ms]


class RecordStatus(Enum):
    UNVIEWED = -1  # not viewed yet
    TOPROCESS = 0  # already viewed at least one (has been pronounced)
    CONFIRMED = 1
    DISCARDED = 2


class MapleUtility(QMainWindow, Ui_MapleUtility):
    web_to_html_finished = pyqtSignal()

    def __init__(self, app, db_file, output_path, parent=None):

        # Setup UI and connection

        super(MapleUtility, self).__init__(parent)
        self.setupUi(self)
        self.app = app
        self.setCentralWidget(self.mainWidget)
        self.confirmButton.clicked.connect(self.confirm_clicked)
        self.discardButton.clicked.connect(self.discard_clicked)
        self.entryList.selectionModel().selectionChanged.connect(self.selected_changed)
        self.subject.textChanged.connect(self.subject_changed)
        self.subject.installEventFilter(self)
        self.subjectSuggest.setVisible(False)
        self.subjectSuggest.clicked.connect(self.suggest_clicked)
        self.freqBar.mouseDoubleClickEvent = self.freq_bar_double_clicked
        self.pronSamantha.clicked.connect(self.pron_clicked)
        self.pronDaniel.clicked.connect(self.pron_clicked)
        self.paraphrase.textChanged.connect(self.paraphrase_changed)
        self.paraphrase.installEventFilter(self)
        self.extension.textChanged.connect(self.extension_changed)
        self.example.textChanged.connect(self.example_changed)
        self.example.installEventFilter(self)
        self.checkSource.stateChanged.connect(self.source_check_changed)
        self.source.textChanged.connect(self.source_changed)
        self.source.installEventFilter(self)
        self.hint.textChanged.connect(self.hint_changed)
        self.saveAllButton.clicked.connect(self.save_all_clicked)
        # These shortcuts are global, while the eventFilter needs to be connected to widgets manually
        self.next_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.next_shortcut.activated.connect(self.confirm_clicked)
        self.discard_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_clicked)
        self.new_entry_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_clicked)
        # There is no mouse signals for label. We use function override
        self.imageLabel.mousePressEvent = self.image_clicked
        self.imageLabel.mouseDoubleClickEvent = self.image_double_clicked
        self.loadKindle.clicked.connect(self.load_kindle_clicked)
        self.loadCSV.clicked.connect(self.load_csv_clicked)
        self.newEntry.clicked.connect(self.add_new_entry_clicked)
        self.clearList.clicked.connect(self.clear_list_clicked)
        self.saveBar.setVisible(False)
        self.checkR.stateChanged.connect(self.card_type_changed)
        self.checkS.stateChanged.connect(self.card_type_changed)
        self.checkD.stateChanged.connect(self.card_type_changed)
        self.webView.loadStarted.connect(self.web_load_started)
        self.webView.loadProgress.connect(self.web_load_progress)
        self.webView.loadFinished.connect(self.web_load_finished)
        self.queryCollins.clicked.connect(self.query_collins_clicked)
        self.queryGoogleImage.clicked.connect(self.query_google_images_clicked)
        self.queryGoogleTranslate.clicked.connect(self.query_google_translate_clicked)
        self.queryGoogle.clicked.connect(self.query_google_clicked)
        self.editor_components = [self.subject, self.subjectSuggest, self.pronSamantha, self.pronDaniel,
                                  self.paraphrase, self.imageLabel, self.extension, self.example, self.checkSource,
                                  self.source, self.hint, self.checkR, self.checkS, self.checkD, self.autoQuery,
                                  self.queryCollins, self.queryGoogleImage, self.queryGoogleTranslate, self.queryGoogle]

        # Setup threads and timers

        self.auto_query_timer = QTimer()
        self.auto_query_timer.setSingleShot(True)
        self.auto_query_timer.timeout.connect(self.auto_query_timeout)

        # Setup data

        self.db_file = db_file
        self.db = None
        self.output_path = output_path
        # self.importer_r = AnkiImporter()
        # self.importer_rd = AnkiImporter()
        self.is_saving = False
        self.has_changed = False
        self.loading_collins = False
        self.suggested_word = None

        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.update_ui_after_record_count_changed()  # setup initial interface

    def __del__(self):
        del self.db

    # -------------------------------- Records Data Handling --------------------------------

    def clear_records(self):
        """
        Helper function to clear all records.
        :return: None
        """

        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.entryList.blockSignals(True)
        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()
        self.entryList.blockSignals(False)

        self.update_ui_after_record_count_changed()

    def reload_kindle_data(self):
        """
        Clear records and load records from Kindle.
        :return: None
        """

        if os.path.isfile(self.db_file):

            # Set up database to KindleDB
            if self.db is not None:
                del self.db
                self.db = None
            self.db = KindleDB(self.db_file)

            self.reload_db()  # clear records and load data from db
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText("Failed to find Kindle DB file. Please make sure Kindle has connected.")
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
            return

    def reload_csv_data(self):
        """
        Clear records and load records from CSV file.
        :return: None
        """

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        csv_file, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "CSV Files (*.csv);;All Files (*)", options=options)
        if csv_file:

            # Setup database to CSV DB
            if self.db is not None:
                del self.db
                self.db = None
            self.db = CSVDB(csv_file)

            self.reload_db()  # clear records and load data from db

    def reload_db(self):

        """
        Helper function to clear records and load entries from database (KindleDB or CSVDB).
        :return: None
        """

        self.clear_records()

        self.records = self.db.fetch_all(new_only=True)

        self.entryList.blockSignals(True)  # ---------------- entry list signals blocked ---------------->

        # Initialize additional fields and add to list
        for r in self.records:
            r["status"] = RecordStatus.UNVIEWED
            r["pron"] = "Unknown"
            r["para"] = r["ext"] = r["hint"] = ""
            r["img"] = None  # no image
            r["freq"] = 0
            r["card"] = "R"
            r["tips"] = ""
            r["source_enabled"] = (r["source"] != "")
            r["usage"] = r["usage"].replace(r["subject"], u"<b>%s</b>" % r["subject"])
            self.entryList.addItem(r["subject"])  # signals has been blocked

        self.has_changed = False

        self.entryList.blockSignals(False)  # <---------------- entry list signals unblocked ----------------

        self.update_ui_after_record_count_changed()  # need to before loading first entry to make gui enabled

        # Setup initial entry, must be after necessary initialization
        if len(self.records) > 0:
            self.entryList.setCurrentRow(0)  # will trigger editor_load_entry()

    def html_extract(self, h):
        return PyQuery(h)("p").html().strip()

    def save_all(self):
        """
        Helper function to save all records
        :return: None
        """

        self.set_gui_enabled(False)  # ---------------- GUI disabled ---------------->
        self.editor_block_signals(True)  # ---------------- editor signals blocked ---------------->
        self.saveBar.setVisible(True)
        self.saveBar.setMaximum(len(self.records))

        self.is_saving = True

        save_file = "%s/maple-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        exporter = DataExporter()
        exporter.open_file(save_file)

        record_count = len(self.records)
        for i in range(record_count):

            r = self.records[i]

            # Set UI
            if record_count < 150 or i % (int(record_count / 100)) == 0 \
                    or r["status"] == RecordStatus.CONFIRMED or r["status"] == RecordStatus.DISCARDED:
                # Only show parts of animation to accelerate saving process
                self.saveBar.setValue(i)
                self.entryList.setCurrentRow(i)
                QtCore.QCoreApplication.processEvents()

            # Generate data
            if r["status"] == RecordStatus.CONFIRMED:

                example = self.html_extract(r["usage"])
                if r["source_enabled"] and r["source"] != "":
                    example += "<br>" + '<div align="right">' + self.html_extract(r["source"]) + '</div>'
                mp3 = exporter.generate_media(r["subject"], r["pron"])
                if r["img"]:
                    img_file = exporter.new_random_filename("png")
                    r["img"].save("%s/%s" % (exporter.media_path, img_file))
                    r["para"] += '<div><br><img src="%s"><br></div>' % img_file
                exporter.write_entry(r["subject"],
                                     "[sound:%s]" % mp3,
                                     self.html_extract(r["para"]),
                                     self.html_extract(r["ext"]),
                                     example,
                                     r["hint"],
                                     r["freq"],
                                     "1" if "R" in r["card"] else "",
                                     "1" if "S" in r["card"] else "",
                                     "1" if "D" in r["card"] else "")

            # Write back to DB
            if r["word_id"] is not None:
                if r["status"] == RecordStatus.CONFIRMED or r["status"] == RecordStatus.DISCARDED:
                    self.db.set_word_mature(r["word_id"], 100)

        if self.db is not None:
            self.db.commit_changes()

        exporter.close_file()

        self.entryList.setCurrentRow(record_count - 1)  # set selection to last
        self.set_gui_enabled(True)  # <---------------- GUI enabled ----------------
        self.editor_block_signals(False)  # <---------------- editor signals unblocked ----------------
        self.saveBar.setVisible(False)
        self.saveBar.setValue(len(self.records))

        self.is_saving = False
        self.has_changed = False

        return "\n" + save_file

    def cur_idx(self):
        """
        Helper function to get current index.
        :return: current index
        """
        return self.entryList.currentRow()

    def cur_record(self):
        """
        Helper function to get current record entry.
        :return: current record
        """
        return self.records[self.cur_idx()]

    # -------------------------------- UI Helper Functions --------------------------------

    def update_ui_after_record_count_changed(self):
        """
        Helper function to update UI after record count changed.
        :return: None
        """
        if len(self.records) > 0:
            self.set_gui_enabled(True)
        else:
            self.editor_block_signals(True)
            self.subject.document().setPlainText("Congratulation!")  # subject change will lead to opening of dictionary
            self.paraphrase.document().setPlainText("There is nothing to be processed.")
            self.extension.document().setPlainText("Great work!")
            self.example.document().setPlainText("")
            self.source.document().setPlainText("")
            self.hint.document().setPlainText("")
            self.freqBar.setMaximum(0)
            self.editor_block_signals(False)
            self.set_gui_enabled(False)

        self.update_progress_bar()

    def confirm_before_action(self, action_name):
        """
        If no changes are made, this function automatically return True.
        If unsaved changes are made, this function asks user to confirm.
        :param action_name: the action to be performed. Will be shown in the dialog box
        :return: True if no changes or user confirmed, False if user canceled.
        """
        if self.has_changed:
            quit_msg = "Are you sure you want to %s? Unsaved entries will be lost." % action_name
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            return reply == QtWidgets.QMessageBox.Yes
        else:
            return True

    def set_record_status(self, idx, status):
        """
        Set UI and change record entry.
        :param idx: index of record entry
        :param status: one of RecordStatus
        :return:
        """

        if self.records[idx]["status"] == status:  # nothing needs to be done
            return

        if status == RecordStatus.CONFIRMED or status == RecordStatus.DISCARDED:
            self.has_changed = True

        f = self.entryList.font()

        if status == RecordStatus.TOPROCESS:  # set TOPROCESS entry to normal form and update counts

            f.setItalic(False)
            f.setStrikeOut(False)

            if self.records[idx]["status"] == RecordStatus.CONFIRMED:
                self.confirmed_count -= 1
            elif self.records[idx]["status"] == RecordStatus.DISCARDED:
                self.discard_count -= 1

        elif status == RecordStatus.CONFIRMED:  # set CONFIRMED entry to italic and update counts

            f.setItalic(True)
            f.setStrikeOut(False)

            self.confirmed_count += 1

        elif status == RecordStatus.DISCARDED:  # strike out DISCARDED entry and update counts

            f.setItalic(False)
            f.setStrikeOut(True)

            self.discard_count += 1

        self.entryList.item(idx).setFont(f)
        self.update_progress_bar()

        self.records[idx]["status"] = status  # modify record

    def update_progress_bar(self):
        """
        Helper functions to update statistic bars.
        :return: None
        """
        record_count = len(self.records)
        self.unreadBar.setMaximum(record_count)
        self.unreadBar.setValue(record_count - (self.confirmed_count + self.discard_count))
        self.unreadBar.setToolTip("%d unread" % self.unreadBar.value())
        self.confirmedBar.setMaximum(record_count)
        self.confirmedBar.setValue(self.confirmed_count)
        self.confirmedBar.setToolTip("%d confirmed" % self.confirmedBar.value())
        self.discardBar.setMaximum(record_count)
        self.discardBar.setValue(self.discard_count)
        self.discardBar.setToolTip("%d discarded" % self.discardBar.value())

    def editor_load_entry(self, idx, forced_query=False):
        """
        Helper function to load an record entry to the main edit area
        :param idx: index of the entry
        :return: None
        """

        if idx < 0 or idx >= len(self.records):  # sanity check
            return

        r = self.records[idx]

        if not self.is_saving:
            if r["subject"] != "":

                if r["status"] == RecordStatus.UNVIEWED:
                    self.pronSamantha.click()  # including toggling and first-time pronouncing
                    self.set_record_status(idx, RecordStatus.TOPROCESS)

                if self.autoQuery.isChecked() or forced_query:
                    self.auto_query_timer.start(auto_query_delay_)
                    # Later query will be handled by timer signal
                    if r["freq"] == 0:  # not only UNVIEWED, but also when failure occurred last time and got nothing
                        self.freqBar.setMaximum(5)
                        self.freqBar.setValue(0)
                        self.freqBar.setTextVisible(False)
                else:
                    self.freqBar.setMaximum(5)  # recover maximum
                    self.freqBar.setTextVisible(True)

            else:
                self.freqBar.setMaximum(5)  # recover maximum
                self.freqBar.setTextVisible(True)

        self.editor_block_signals(True)  # ---------------- main editor signals blocked ---------------->

        self.subject.document().setPlainText(r["subject"])

        if r["pron"] == "Samantha":
            self.pronSamantha.toggle()  # only change UI display but not triggering pronunciation
        elif r["pron"] == "Daniel":
            self.pronDaniel.toggle()

        self.freqBar.setValue(r["freq"])
        self.freqBar.setToolTip(r["tips"])
        self.checkR.setChecked("R" in r["card"])
        self.checkS.setChecked("S" in r["card"])
        self.checkD.setChecked("D" in r["card"])

        self.paraphrase.document().setHtml(r["para"])
        self.extension.document().setHtml(r["ext"])
        self.example.document().setHtml(r["usage"])
        self.checkSource.setChecked(r["source_enabled"])
        self.source.document().setHtml(r["source"])
        self.source.setEnabled(r["source_enabled"])
        self.hint.document().setPlainText(r["hint"])

        if r["img"]:
            self.imageLabel.setPixmap(r["img"])
        else:
            self.imageLabel.setText("Click \nto paste \nimage")

        self.editor_block_signals(False)  # <---------------- main editor signals unblocked --v------

    def move_to_next(self):
        """
        Helper function to move to next record entry
        :return: None
        """
        if self.cur_idx() < len(self.records) - 1:
            self.entryList.setCurrentRow(self.cur_idx() + 1)
            # Loading data will be completed by selected_changed()
        elif self.cur_idx() == len(self.records) - 1:
            self.add_new_entry_clicked()

    def set_gui_enabled(self, value):
        """
        Helper functions to enable/disable UI components
        :param value: True/False
        :return: None
        """
        for component in [self.confirmButton, self.discardButton, self.saveAllButton] + self.editor_components:
            component.setEnabled(value)

    def editor_block_signals(self, value):
        """
        Helper function to block/unblock signals of main editor
        :param value: True/False
        :return: None
        """
        for component in self.editor_components:
            component.blockSignals(value)

    # -------------------------------- UI Signal Handlers --------------------------------

    @pyqtSlot()
    def confirm_clicked(self):
        self.set_record_status(self.cur_idx(), RecordStatus.CONFIRMED)
        self.move_to_next()

    @pyqtSlot()
    def discard_clicked(self):
        self.set_record_status(self.cur_idx(), RecordStatus.DISCARDED)
        self.move_to_next()

    @pyqtSlot()
    def selected_changed(self):
        self.editor_load_entry(self.cur_idx())

    @pyqtSlot()
    def pron_clicked(self):
        sender = self.sender()
        if sender:
            DataExporter.pronounce(self.cur_record()["subject"], sender.text())
            self.cur_record()["pron"] = sender.text()

    @pyqtSlot()
    def subject_changed(self):
        subject = self.subject.toPlainText()
        self.cur_record()["subject"] = subject
        # self.cur_record()["freq"] = 0
        self.entryList.item(self.cur_idx()).setText(subject)
        # self.editor_load_entry(self.cur_idx())

    @pyqtSlot()
    def suggest_clicked(self):
        self.subject.blockSignals(True)
        self.subject.setPlainText(self.suggested_word)
        self.subject.blockSignals(False)
        self.subjectSuggest.setVisible(False)

    def eventFilter(self, widget, event):
        """
        Handler of various key events
        :param widget:
        :param event:
        :return:
        """
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                if (widget is self.subject) or (widget is self.paraphrase):
                    self.cur_record()["status"] = RecordStatus.UNVIEWED
                    self.editor_load_entry(self.cur_idx(), True)
                    return True
            elif key == QtCore.Qt.Key_B and event.modifiers() == QtCore.Qt.ControlModifier:  # Ctrl + B
                if (widget is self.paraphrase) or (widget is self.example) or (widget is self.source):
                    widget: QtWidgets.QTextEdit
                    cursor = widget.textCursor()
                    fmt = cursor.charFormat()
                    if fmt.fontWeight() == QtGui.QFont.Bold:
                        fmt.setFontWeight(QtGui.QFont.Normal)
                    else:
                        fmt.setFontWeight(QtGui.QFont.Bold)
                    cursor.mergeCharFormat(fmt)
            elif key == QtCore.Qt.Key_I and event.modifiers() == QtCore.Qt.ControlModifier:  # Ctrl + I
                if (widget is self.paraphrase) or (widget is self.example) or (widget is self.source):
                    widget: QtWidgets.QTextEdit
                    cursor = widget.textCursor()
                    fmt = cursor.charFormat()
                    fmt.setFontItalic(not fmt.fontItalic())
                    cursor.mergeCharFormat(fmt)

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    @pyqtSlot()
    def paraphrase_changed(self):
        self.cur_record()["para"] = self.paraphrase.toHtml()

    @pyqtSlot()
    def extension_changed(self):
        self.cur_record()["ext"] = self.extension.toHtml()

    @pyqtSlot()
    def example_changed(self):
        self.cur_record()["usage"] = self.example.toHtml()

    @pyqtSlot()
    def source_changed(self):
        self.cur_record()["source"] = self.source.toHtml()

    @pyqtSlot()
    def source_check_changed(self):
        self.source.setEnabled(self.checkSource.isChecked())
        self.cur_record()["source_enabled"] = self.checkSource.isChecked()

    @pyqtSlot()
    def hint_changed(self):
        self.cur_record()["hint"] = self.hint.toPlainText()

    @pyqtSlot()
    def save_all_clicked(self):

        confirm_str = "%d confirmed, %d discarded, %d unread.\n\n" \
                      "Only confirmed ones will be saved. " \
                      "Confirmed and discarded ones will be marked as mutual on Kindle. " \
                      "Please make sure kindle is connected. \n\n" \
                      "Continue to save?" % (
                          self.confirmed_count, self.discard_count,
                          len(self.records) - self.confirmed_count - self.discard_count)
        ret = QtWidgets.QMessageBox.question(self, "Confirm", confirm_str, QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.Cancel)

        if ret == QtWidgets.QMessageBox.Yes:
            save_file = self.save_all()
            QtWidgets.QMessageBox.information(self, "Success",
                                              "Saved %d entries. Discard %d entries. %d entries unchanged.\n\n" \
                                              "Saved to %s" % (
                                                  self.confirmed_count, self.discard_count,
                                                  len(self.records) - self.confirmed_count - self.discard_count,
                                                  save_file),
                                              QtWidgets.QMessageBox.Ok)

    def closeEvent(self, event):
        if self.confirm_before_action("exit"):
            event.accept()
        else:
            event.ignore()

    @pyqtSlot()
    def image_clicked(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            mine_data = app.clipboard().mimeData()
            if mine_data.hasImage():
                px = QtGui.QPixmap(mine_data.imageData()).scaledToHeight(self.imageLabel.height(),
                                                                         mode=QtCore.Qt.SmoothTransformation)
                self.cur_record()["img"] = px
                self.imageLabel.setPixmap(px)
        elif event.button() == QtCore.Qt.RightButton:
            # web_interface.open_google_image_website(self.cur_record()["subject"])
            self.webView.page().profile().setHttpUserAgent(mac_user_agent)
            self.webView.load(QtCore.QUrl(google_image_url % urllib.parse.quote(self.cur_record()["subject"])))

    @pyqtSlot()
    def image_double_clicked(self, event):
        self.cur_record()["img"] = None
        self.imageLabel.setText("Click \nto paste \nimage")

    @pyqtSlot()
    def load_kindle_clicked(self):
        if self.confirm_before_action("reload database"):
            self.reload_kindle_data()

    @pyqtSlot()
    def load_csv_clicked(self):
        if self.confirm_before_action("reload database"):
            self.reload_csv_data()

    @pyqtSlot()
    def freq_bar_double_clicked(self, event):
        self.web_query(collins_url, self.cur_record()["subject"])  # reload website

    @pyqtSlot()
    def add_new_entry_clicked(self):
        self.records.append({
            "status": RecordStatus.UNVIEWED,
            "word_id": None,
            "subject": "",
            "pron": "Unknown",
            "para": "",
            "ext": "",
            "usage": "",
            "source": '<div align="right" style="font-size:12px"></div>',
            "source_enabled": False,
            "hint": "",
            "img": None,  # no image
            "freq": 0,
            "card": "R",
            "tips": ""
        })
        self.entryList.addItem("")  # signals has been blocked
        self.update_ui_after_record_count_changed()  # placed before editor_load_entry() for source to set correctly
        self.entryList.setCurrentRow(len(self.records) - 1)  # will trigger editor_load_entry()

        self.subject.setFocus()

    def clear_list_clicked(self):
        if self.confirm_before_action("clear list manually"):
            self.clear_records()

    def card_type_changed(self):
        self.cur_record()["card"] = "%s%s%s" % ("R" if self.checkR.isChecked() else "",
                                                "S" if self.checkS.isChecked() else "",
                                                "D" if self.checkD.isChecked() else "")

    @pyqtSlot()
    def query_collins_clicked(self):
        self.web_query(collins_url, self.cur_record()["subject"])

    @pyqtSlot()
    def query_google_images_clicked(self):
        self.web_query(google_image_url, self.cur_record()["subject"])

    @pyqtSlot()
    def query_google_translate_clicked(self):
        self.web_query(google_translate_url, self.cur_record()["subject"])

    @pyqtSlot()
    def query_google_clicked(self):
        self.web_query(google_url, self.cur_record()["subject"])

    # -------------------------------- Query Handlers --------------------------------

    def web_query(self, base_url, word):
        self.webView.page().profile().setHttpUserAgent(mac_user_agent)
        self.webView.page().profile().setProperty("X-Frame-Options", "Deny")
        self.loading_collins = (base_url == collins_url)
        self.webView.load(QtCore.QUrl(base_url % urllib.parse.quote(word)))
        # Further handling will be completed by slots

    @pyqtSlot()
    def web_load_started(self):
        self.freqBar.setMaximum(100)
        self.freqBar.setValue(0)
        self.freqBar.setTextVisible(False)

    @pyqtSlot(int)
    def web_load_progress(self, progress):
        self.freqBar.setValue(progress)
        if self.webView.hasFocus():
            self.paraphrase.setFocus()

    @pyqtSlot(bool)
    def web_load_finished(self, ok):
        self.freqBar.setMaximum(5)  # recover maximum
        self.freqBar.setValue(self.cur_record()["freq"])
        self.freqBar.setTextVisible(True)
        self.suggested_word = get_word_from_collins_url(self.webView.page().url().url())
        if self.suggested_word is not None:
            self.webView.page().runJavaScript("document.documentElement.outerHTML", self.collins_web_to_html_callback)
        if self.suggested_word is not None and self.suggested_word != self.subject.toPlainText():
            self.subjectSuggest.setText("Suggest: " + self.suggested_word)
            self.subjectSuggest.setVisible(True)
        else:
            self.subjectSuggest.setVisible(False)

        if self.webView.hasFocus():
            self.paraphrase.setFocus()

    def collins_web_to_html_callback(self, html_str):

        if self.cur_record()["freq"] == 0:  # not only UNVIEWED, but also retry if failure occurred last time
            (freq, tips) = parse_collins_word_frequency(html_str)
            self.set_word_freq(self.cur_idx(), freq, tips)

        js = collins_post_js
        self.webView.page().runJavaScript(js)  # run post js to eliminate ADs, etc.

    def set_word_freq(self, idx, freq, tips):
        r = self.records[idx]
        r["freq"] = freq
        if freq >= card_rd_threshold_:
            r["card"] = "RD"
        else:
            r["card"] = "R"
        r["tips"] = tips

        if idx == self.cur_idx():
            self.freqBar.setMaximum(5)
            self.freqBar.setValue(freq)
            self.freqBar.setToolTip(tips)
            self.checkR.setChecked("R" in r["card"])
            self.checkS.setChecked("S" in r["card"])
            self.checkD.setChecked("D" in r["card"])

    @pyqtSlot()
    def auto_query_timeout(self):
        self.web_query(collins_url, self.cur_record()["subject"])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility(app, db_file_, output_path_)
    mapleUtility.showMaximized()

    sys.exit(app.exec_())
