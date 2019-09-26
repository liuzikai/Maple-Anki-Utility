#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from datetime import datetime
from enum import Enum
from maple_utility import *
from anki_output import *
from data_input import *
import web_interface
import urllib.parse


# db_file_ = "/Users/liuzikai/Documents/Programming/Kindle2Anki/vocab.db"
db_file_ = "/Volumes/Kindle/system/vocabulary/vocab.db"
output_path_ = "/Users/liuzikai/Desktop"
card_rd_threshold_ = 4

mac_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"
ios_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"


class RecordStatus(Enum):
    UNVIEWED = -1
    TOPROCESS = 0
    CONFIRMED = 1
    DISCARDED = 2


class MapleUtility(QMainWindow, Ui_MapleUtility):

    web_to_html_finished = pyqtSignal()

    def __init__(self, app, db_file, output_path, parent=None):

        # Setup UI

        super(MapleUtility, self).__init__(parent)
        self.setupUi(self)

        self.app = app
        self.setCentralWidget(self.mainWidget)
        self.nextButton.clicked.connect(self.next_click)
        self.discardButton.clicked.connect(self.discard_click)
        self.entryList.selectionModel().selectionChanged.connect(self.selected_changed)
        self.subject.textChanged.connect(self.subject_changed)
        self.subject.installEventFilter(self)
        self.freqBar.mouseDoubleClickEvent = self.freq_bar_double_click
        self.pronSamantha.clicked.connect(self.pron_clicked)
        self.pronDaniel.clicked.connect(self.pron_clicked)
        self.paraphrase.textChanged.connect(self.paraphrase_changed)
        self.extension.textChanged.connect(self.extension_changed)
        self.example.textChanged.connect(self.example_changed)
        self.hint.textChanged.connect(self.hint_changed)
        self.saveAllButton.clicked.connect(self.save_all_clicked)
        self.next_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.next_shortcut.activated.connect(self.next_click)
        self.discard_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_click)
        self.new_entry_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_click)
        # TODO: handle event using fliter
        self.imageLabel.mousePressEvent = self.image_click
        self.imageLabel.mouseDoubleClickEvent = self.image_double_click
        self.loadKindle.clicked.connect(self.reload_kindle_click)
        self.loadCSV.clicked.connect(self.reload_csv_click)
        self.newEntry.clicked.connect(self.add_new_entry_click)
        self.clearList.clicked.connect(self.clear_list_click)
        self.saveBar.setVisible(False)
        self.cardType.currentIndexChanged.connect(self.card_type_changed)

        # Setup threads and timers

        self.web_worker = web_interface.CollinsWorker(self.webView)
        self.web_worker.finished.connect(self.set_word_freq)
        self.mac_dict_worker = web_interface.MacDictWorker()
        self.mac_dict_worker.finished.connect(self.after_opening_mac_dict)

        # Setup data

        self.db_file = db_file
        self.db = None
        self.output_path = output_path
        self.importer_r = AnkiImporter()
        self.importer_rd = AnkiImporter()
        self.is_saving = False
        self.has_changed = False

        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.update_ui_after_entry_count_changed()  # setup initial interface

    def clear_records(self):
        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.entryList.blockSignals(True)
        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()
        self.entryList.blockSignals(False)

        self.update_ui_after_entry_count_changed()

    def reload_kindle_data(self):

        if os.path.isfile(self.db_file):
            if self.db is not None:
                del self.db
                self.db = None
            self.db = KindleDB(self.db_file)
            self.reload_db()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText("Failed to find Kindle DB file. Please make sure Kindle has connected.")
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
            return

    def reload_csv_data(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        csv_file, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "CSV Files (*.csv);;All Files (*)", options=options)
        if csv_file:
            if self.db is not None:
                del self.db
                self.db = None
            self.db = CSVDB(csv_file)
            self.reload_db()

    def reload_db(self):

        self.clear_records()

        self.records = self.db.fetch_all(new_only=True)

        self.entryList.blockSignals(True)

        # Initialize additional fields and add to list
        for r in self.records:
            r["status"] = RecordStatus.UNVIEWED
            r["pron"] = "Unknown"
            r["para"] = r["ext"] = r["hint"] = ""
            r["img"] = None  # no image
            r["freq"] = 0
            r["card"] = 0
            r["tips"] = ""
            self.entryList.addItem(r["subject"])  # signals has been blocked

        self.has_changed = False

        # Setup initial entry, must be after necessary initialization
        if len(self.records) > 0:
            self.entryList.setCurrentRow(0)  # signal of entryList has been block, will not trigger editor_load_entry()
            self.editor_load_entry(self.cur_idx())

        self.update_ui_after_entry_count_changed()

        self.entryList.blockSignals(False)

    def update_ui_after_entry_count_changed(self):
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
        if self.has_changed:
            quit_msg = "Are you sure you want to %s? Unsaved entries will be lost." % action_name
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            return reply == QtWidgets.QMessageBox.Yes
        else:
            return True

    def cur_idx(self):
        return self.entryList.currentRow()

    def set_record_status(self, idx, status):
        """
        Set UI and record entry
        :param idx:
        :param status: one of RecordStatus
        :return:
        """

        if self.records[idx]["status"] == status:
            return

        if status == RecordStatus.CONFIRMED or status == RecordStatus.DISCARDED:
            self.has_changed = True

        f = self.entryList.font()

        if status == RecordStatus.TOPROCESS:

            f.setItalic(False)
            f.setStrikeOut(False)

            if self.records[idx]["status"] == RecordStatus.CONFIRMED:
                self.confirmed_count -= 1
            elif self.records[idx]["status"] == RecordStatus.DISCARDED:
                self.discard_count -= 1

        elif status == RecordStatus.CONFIRMED:

            f.setItalic(True)
            f.setStrikeOut(False)

            self.confirmed_count += 1

        elif status == RecordStatus.DISCARDED:

            f.setItalic(False)
            f.setStrikeOut(True)

            self.discard_count += 1

        self.entryList.item(idx).setFont(f)
        self.update_progress_bar()

        self.records[idx]["status"] = status

    def update_progress_bar(self):
        record_count = len(self.records)
        self.unreadBar.setMaximum(record_count)
        self.unreadBar.setValue(record_count - (self.confirmed_count + self.discard_count))
        self.confirmedBar.setMaximum(record_count)
        self.confirmedBar.setValue(self.confirmed_count)
        self.discardBar.setMaximum(record_count)
        self.discardBar.setValue(self.discard_count)

    def editor_load_entry(self, idx):

        if idx < 0 or idx >= len(self.records):
            return

        r = self.records[idx]

        if not self.is_saving:
            if r["subject"] != "":

                if r["status"] == RecordStatus.UNVIEWED:
                    self.pronSamantha.click()  # including toggling and first-time pronouncing
                    self.set_record_status(idx, RecordStatus.TOPROCESS)

                if self.autoQuery.isChecked():
                    self.load_collins(r["subject"])
                    if r["freq"] == 0:  # not only UNVIEWED, but also retry if failure occurred last time and got nothing
                        self.freqBar.setMaximum(0)
                        # Later freqBar and cardType will be updated by set_word_freq() slot
                else:
                    self.freqBar.setMaximum(5)  # recover maximum

            else:
                self.freqBar.setMaximum(5)  # recover maximum

        self.editor_block_signals(True)

        self.subject.document().setPlainText(r["subject"])

        if r["pron"] == "Samantha":
            self.pronSamantha.toggle()
        elif r["pron"] == "Daniel":
            self.pronDaniel.toggle()

        self.freqBar.setValue(r["freq"])
        self.freqBar.setToolTip(r["tips"])
        self.cardType.setCurrentIndex(r["card"])

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

        self.editor_block_signals(False)

    def move_to_next(self):
        if self.cur_idx() < len(self.records) - 1:
            self.entryList.setCurrentRow(self.cur_idx() + 1)
            # Loading data will be completed by selected_changed()
        elif self.cur_idx() == len(self.records) - 1:
            self.add_new_entry_click()

    def next_click(self):
        self.set_record_status(self.cur_idx(), RecordStatus.CONFIRMED)
        self.move_to_next()

    def discard_click(self):
        self.set_record_status(self.cur_idx(), RecordStatus.DISCARDED)
        self.move_to_next()

    def selected_changed(self):
        self.editor_load_entry(self.cur_idx())

    def pron_clicked(self):
        sender = self.sender()
        if sender:
            AnkiImporter.pronounce(self.cur_record()["subject"], sender.text())
            self.cur_record()["pron"] = sender.text()

    def cur_record(self):
        return self.records[self.cur_idx()]

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

    def set_gui_enabled(self, value):
        self.nextButton.setEnabled(value)
        self.discardButton.setEnabled(value)
        self.saveAllButton.setEnabled(value)
        self.subject.setEnabled(value)
        self.pronSamantha.setEnabled(value)
        self.pronDaniel.setEnabled(value)
        self.paraphrase.setEnabled(value)
        self.imageLabel.setEnabled(value)
        self.extension.setEnabled(value)
        self.example.setEnabled(value)
        self.source.setEnabled(value)
        self.hint.setEnabled(value)
        self.cardType.setEnabled(value)

    def editor_block_signals(self, value):
        self.subject.blockSignals(value)
        self.pronSamantha.blockSignals(value)
        self.pronDaniel.blockSignals(value)
        self.paraphrase.blockSignals(value)
        self.imageLabel.blockSignals(value)
        self.extension.blockSignals(value)
        self.example.blockSignals(value)
        self.source.blockSignals(value)
        self.hint.blockSignals(value)
        self.cardType.blockSignals(value)

    def save_all(self):

        self.set_gui_enabled(False)
        self.editor_block_signals(True)
        self.saveBar.setVisible(True)
        self.saveBar.setMaximum(len(self.records))
        self.is_saving = True

        save_file_r = "%s/kindle-r-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        save_file_rd = "%s/kindle-rd-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        self.importer_r.open_file(save_file_r)
        self.importer_rd.open_file(save_file_rd)

        record_count = len(self.records)
        for i in range(record_count):

            r = self.records[i]

            # Set UI
            if record_count < 150 or i % (int(record_count / 100)) == 0:
                # Disable parts of animation to accelerate saving process
                self.saveBar.setValue(i)
                self.entryList.setCurrentRow(i)
                QtCore.QCoreApplication.processEvents()

            # Generate data
            if r["status"] == RecordStatus.CONFIRMED:

                # Select proper importer
                if r["card"] == 0:
                    importer = self.importer_r
                else:
                    importer = self.importer_rd

                example = '%s<br>%s' % (r["usage"], r["source"])
                mp3 = importer.generate_media(r["subject"], r["pron"])
                if r["img"]:
                    img_file = importer.new_random_filename("png")
                    r["img"].save("%s/%s" % (importer.media_path, img_file))
                    r["para"] += '<div><br><img src="%s"><br></div>' % img_file
                importer.write_entry(r["subject"],
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

        self.importer_r.close_file()
        self.importer_rd.close_file()

        self.set_gui_enabled(True)
        self.entryList.blockSignals(False)
        self.editor_block_signals(False)
        self.saveBar.setVisible(False)
        self.saveBar.setValue(len(self.records))
        self.is_saving = False
        self.has_changed = False

        return "\n\n" + save_file_r + "\n\n" + save_file_rd

    def closeEvent(self, event):

        if self.confirm_before_action("exit"):
            event.accept()
        else:
            event.ignore()

    def image_click(self, event):
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
            self.webView.load(QtCore.QUrl(web_interface.google_image_url + urllib.parse.quote(self.cur_record()["subject"])))

    def image_double_click(self, event):
        self.cur_record()["img"] = None
        self.imageLabel.setText("Click \nto paste \nimage")

    def reload_kindle_click(self):
        if self.confirm_before_action("reload database"):
            self.reload_kindle_data()

    def reload_csv_click(self):
        if self.confirm_before_action("reload database"):
            self.reload_csv_data()

    def freq_bar_double_click(self, event):
        self.load_collins(self.cur_record()["subject"])  # reload website

    @pyqtSlot(int, int, str)
    def set_word_freq(self, idx, freq, tips):
        self.records[idx]["freq"] = freq
        if freq >= card_rd_threshold_:
            self.records[idx]["card"] = 1
        else:
            self.records[idx]["card"] = 0
        self.records[idx]["tips"] = tips

        if idx == self.cur_idx():
            self.freqBar.setMaximum(5)
            self.freqBar.setValue(freq)
            self.freqBar.setToolTip(tips)
            self.cardType.setCurrentIndex(self.records[idx]["card"])

    def load_collins(self, word):
        self.webView.loadFinished.connect(self.web_load_finished)
        self.webView.page().profile().setHttpUserAgent(mac_user_agent)
        self.webView.load(QtCore.QUrl(web_interface.collins_url + urllib.parse.quote(word)))
        # Wait for slot web_load_finished

    @pyqtSlot(str)
    def after_opening_mac_dict(self, word):
        self.raise_()

    @pyqtSlot(bool)
    def web_load_finished(self, ok):
        # if ok:
        self.webView.loadFinished.disconnect()
        self.webView.page().toHtml(self.web_to_html_callback)
        # TODO: handle the case of failure

    def web_to_html_callback(self, html):

        if self.cur_record()["freq"] == 0:  # not only UNVIEWED, but also retry if failure occurred last time
            (freq, tips) = web_interface.parse_collins_word_frequency(html)
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
"""
        self.webView.page().runJavaScript(js)

    def add_new_entry_click(self):
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
            "card": 0,
            "tips": ""
        })
        self.entryList.addItem("")  # signals has been blocked
        self.entryList.setCurrentRow(len(self.records) - 1)  # will trigger editor_load_entry()
        self.update_ui_after_entry_count_changed()
        self.subject.setFocus()

    def clear_list_click(self):
        if self.confirm_before_action("clear list manually"):
            self.clear_records()

    def card_type_changed(self):
        self.cur_record()["card"] = self.cardType.currentIndex()

    def __del__(self):
        del self.db


if __name__ == '__main__':

    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility(app, db_file_, output_path_)
    mapleUtility.showMaximized()

    sys.exit(app.exec_())
