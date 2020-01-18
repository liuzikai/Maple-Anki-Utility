#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from datetime import datetime
from enum import Enum
from maple_utility import *
from data_export import *
from data_source import *
import web_query
import urllib.parse


# db_file_ = "/Users/liuzikai/Documents/Programming/MapleVocabUtility/test_vocab.db"
db_file_ = "/Volumes/Kindle/system/vocabulary/vocab.db"
output_path_ = "/Users/liuzikai/Desktop"
card_rd_threshold_ = 4

mac_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"
ios_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"


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
        self.freqBar.mouseDoubleClickEvent = self.freq_bar_double_clicked
        self.pronSamantha.clicked.connect(self.pron_clicked)
        self.pronDaniel.clicked.connect(self.pron_clicked)
        self.paraphrase.textChanged.connect(self.paraphrase_changed)
        self.extension.textChanged.connect(self.extension_changed)
        self.example.textChanged.connect(self.example_changed)
        self.hint.textChanged.connect(self.hint_changed)
        self.saveAllButton.clicked.connect(self.save_all_clicked)
        self.next_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.next_shortcut.activated.connect(self.confirm_clicked)
        self.discard_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_clicked)
        self.new_entry_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_clicked)
        # TODO: handle event using filter
        self.imageLabel.mousePressEvent = self.image_clicked
        self.imageLabel.mouseDoubleClickEvent = self.image_double_clicked
        self.loadKindle.clicked.connect(self.load_kindle_clicked)
        self.loadCSV.clicked.connect(self.load_csv_clicked)
        self.newEntry.clicked.connect(self.add_new_entry_clicked)
        self.clearList.clicked.connect(self.clear_list_clicked)
        self.saveBar.setVisible(False)
        self.cardType.currentIndexChanged.connect(self.card_type_changed)
        self.webView.loadFinished.connect(self.web_load_finished)
        self.editor_components = [self.subject, self.pronSamantha, self.pronDaniel, self.paraphrase, self.imageLabel,
                                  self.extension, self.example, self.source, self.hint, self.cardType]

        # Setup threads and timers

        self.web_worker = web_query.CollinsWorker(self.webView)
        self.web_worker.finished.connect(self.set_word_freq)
        self.mac_dict_worker = web_query.MacDictWorker()
        self.mac_dict_worker.finished.connect(self.after_opening_mac_dict)

        # Setup data

        self.db_file = db_file
        self.db = None
        self.output_path = output_path
        # self.importer_r = AnkiImporter()
        # self.importer_rd = AnkiImporter()
        self.is_saving = False
        self.has_changed = False

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
            r["card"] = ""
            r["tips"] = ""
            self.entryList.addItem(r["subject"])  # signals has been blocked

        self.has_changed = False

        self.entryList.blockSignals(False)  # <---------------- entry list signals unblocked ----------------

        self.update_ui_after_record_count_changed()  # need to before loading first entry to make gui enabled

        # Setup initial entry, must be after necessary initialization
        if len(self.records) > 0:
            self.entryList.setCurrentRow(0)  # will trigger editor_load_entry()

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

    def editor_load_entry(self, idx):
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

                if self.autoQuery.isChecked():
                    self.load_collins(r["subject"])
                    if r["freq"] == 0:  # not only UNVIEWED, but also when failure occurred last time and got nothing
                        self.freqBar.setMaximum(0)  # change it to the loading style
                        # Later freqBar and cardType will be updated by set_word_freq() slot
                else:
                    self.freqBar.setMaximum(5)  # recover maximum

            else:
                self.freqBar.setMaximum(5)  # recover maximum

        self.editor_block_signals(True)  # ---------------- main editor signals blocked ---------------->

        self.subject.document().setPlainText(r["subject"])

        if r["pron"] == "Samantha":
            self.pronSamantha.toggle()  # only change UI display but not triggering pronunciation
        elif r["pron"] == "Daniel":
            self.pronDaniel.toggle()

        self.freqBar.setValue(r["freq"])
        self.freqBar.setToolTip(r["tips"])
        self.cardType.setCurrentIndex(self.cardType.findText(r["card"]))

        self.paraphrase.document().setPlainText(r["para"])
        self.extension.document().setPlainText(r["ext"])
        self.example.document().setHtml(
            r["usage"].replace(r["subject"], u"<b>%s</b>" % r["subject"]))  # bold won't be saved as html
        self.source.document().setHtml(r["source"])  # read-only
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

    def confirm_clicked(self):
        self.set_record_status(self.cur_idx(), RecordStatus.CONFIRMED)
        self.move_to_next()

    def discard_clicked(self):
        self.set_record_status(self.cur_idx(), RecordStatus.DISCARDED)
        self.move_to_next()

    def selected_changed(self):
        self.editor_load_entry(self.cur_idx())

    def pron_clicked(self):
        sender = self.sender()
        if sender:
            DataExporter.pronounce(self.cur_record()["subject"], sender.text())
            self.cur_record()["pron"] = sender.text()

    def subject_changed(self):
        subject = self.subject.toPlainText()
        self.cur_record()["subject"] = subject
        # self.cur_record()["freq"] = 0
        self.entryList.item(self.cur_idx()).setText(subject)
        # self.editor_load_entry(self.cur_idx())

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress and widget is self.subject:
            key = event.key()
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                self.cur_record()["freq"] = 0
                self.editor_load_entry(self.cur_idx())
                return True
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def paraphrase_changed(self):
        self.cur_record()["para"] = self.paraphrase.toPlainText()

    def extension_changed(self):
        self.cur_record()["ext"] = self.extension.toPlainText()

    def example_changed(self):
        self.cur_record()["usage"] = self.example.toPlainText()  # bold won't be saved as html

    def hint_changed(self):
        self.cur_record()["hint"] = self.hint.toPlainText()

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

        save_files = {}
        exporters = {}

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

                # Select proper exporter
                card_ = r["card"]
                if card_ not in exporters.keys():  # it's the first time we encounter this type of card
                    save_files[card_] = "%s/maple-%s-%s.txt" % \
                                        (self.output_path, card_, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
                    exporters[card_] = DataExporter()
                    exporters[card_].open_file(save_files[card_])

                exporter = exporters[card_]

                example = '%s<br>%s' % (r["usage"], r["source"])
                mp3 = exporter.generate_media(r["subject"], r["pron"])
                if r["img"]:
                    img_file = exporter.new_random_filename("png")
                    r["img"].save("%s/%s" % (exporter.media_path, img_file))
                    r["para"] += '<div><br><img src="%s"><br></div>' % img_file
                exporter.write_entry(r["subject"],
                                     "[sound:%s]" % mp3,
                                     r["para"],
                                     r["ext"],
                                     example,
                                     r["hint"],
                                     r["freq"])

            # Write back to DB
            if r["word_id"] is not None:
                if r["status"] == RecordStatus.CONFIRMED or r["status"] == RecordStatus.DISCARDED:
                    self.db.set_word_mature(r["word_id"], 100)

        if self.db is not None:
            self.db.commit_changes()

        for exporter in exporters.values():
            exporter.close_file()

        self.entryList.setCurrentRow(record_count - 1)  # set selection to last
        self.set_gui_enabled(True)  # <---------------- GUI enabled ----------------
        self.editor_block_signals(False)  # <---------------- editor signals unblocked ----------------
        self.saveBar.setVisible(False)
        self.saveBar.setValue(len(self.records))

        self.is_saving = False
        self.has_changed = False

        return "\n" + "\n".join(save_files.values())

    def closeEvent(self, event):

        if self.confirm_before_action("exit"):
            event.accept()
        else:
            event.ignore()

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
            self.webView.load(QtCore.QUrl(web_query.google_image_url + urllib.parse.quote(self.cur_record()["subject"])))

    def image_double_clicked(self, event):
        self.cur_record()["img"] = None
        self.imageLabel.setText("Click \nto paste \nimage")

    def load_kindle_clicked(self):
        if self.confirm_before_action("reload database"):
            self.reload_kindle_data()

    def load_csv_clicked(self):
        if self.confirm_before_action("reload database"):
            self.reload_csv_data()

    def freq_bar_double_clicked(self, event):
        self.load_collins(self.cur_record()["subject"])  # reload website

    @pyqtSlot(int, int, str)
    def set_word_freq(self, idx, freq, tips):
        self.records[idx]["freq"] = freq
        if freq >= card_rd_threshold_:
            self.records[idx]["card"] = "RD"
        else:
            self.records[idx]["card"] = "R"
        self.records[idx]["tips"] = tips

        if idx == self.cur_idx():
            self.freqBar.setMaximum(5)
            self.freqBar.setValue(freq)
            self.freqBar.setToolTip(tips)
            self.cardType.setCurrentIndex(self.cardType.findText(self.records[idx]["card"]))

    def load_collins(self, word):

        self.webView.page().profile().setHttpUserAgent(mac_user_agent)
        self.webView.page().profile().setProperty("X-Frame-Options", "Deny")
        self.webView.load(QtCore.QUrl(web_query.collins_url + urllib.parse.quote(word)))
        # Wait for slot web_load_finished

    @pyqtSlot(str)
    def after_opening_mac_dict(self, word):
        self.raise_()

    @pyqtSlot(bool)
    def web_load_finished(self, ok):
        # if ok:
        # self.webView.loadFinished.disconnect()
        self.webView.page().runJavaScript("document.documentElement.outerHTML", self.web_to_html_callback)
        # TODO: handle the case of failure

    def web_to_html_callback(self, html_str):

        if self.cur_record()["freq"] == 0:  # not only UNVIEWED, but also retry if failure occurred last time
            (freq, tips) = web_query.parse_collins_word_frequency(html_str)
            self.set_word_freq(self.cur_idx(), freq, tips)

        js = """
$('iframe').remove()
$('.topslot_container').remove()
$('.cB-hook').remove()
$('#videos').remove()
$('.socialButtons').remove()
$('.tabsNavigation').remove()
$('.res_cell_right').remove()
$('.btmslot_a-container').remove()
$('.exercise').remove()
$('.mpuslot_b-container').remove()
$('._hj-f5b2a1eb-9b07_feedback_minimized_label').remove()
$('.share-button').remove()
"""
        self.webView.page().runJavaScript(js)

    def add_new_entry_clicked(self):
        self.records.append({
            "status": RecordStatus.UNVIEWED,
            "word_id": None,
            "subject": "",
            "pron": "Unknown",
            "para": "",
            "ext": "",
            "usage": "",
            "source": "",
            "hint": "",
            "img": None,  # no image
            "freq": 0,
            "card": "",
            "tips": ""
        })
        self.entryList.addItem("")  # signals has been blocked
        self.entryList.setCurrentRow(len(self.records) - 1)  # will trigger editor_load_entry()
        self.update_ui_after_record_count_changed()
        self.subject.setFocus()

    def clear_list_clicked(self):
        if self.confirm_before_action("clear list manually"):
            self.clear_records()

    def card_type_changed(self):
        self.cur_record()["card"] = self.cardType.currentText()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility(app, db_file_, output_path_)
    mapleUtility.showMaximized()

    sys.exit(app.exec_())