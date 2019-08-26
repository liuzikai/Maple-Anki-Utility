import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from maple_utility import *
from anki_interface import *
from kindle_db import *
from datetime import datetime
import webbrowser
import web_interface

db_file_ = "/Users/liuzikai/Documents/Programming/Kindle2Anki/vocab.db"
# db_file_ = "/Volumes/Kindle/system/vocabulary/vocab.db"
output_path_ = "/Users/liuzikai/Desktop"
card_rd_threshold_ = 4


class MapleUtility(QMainWindow, Ui_MapleUtility):

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
        self.imageLabel.mousePressEvent = self.image_click
        self.imageLabel.mouseDoubleClickEvent = self.image_double_click
        self.reloadDB.clicked.connect(self.reload_click)
        self.saveBar.setVisible(False)

        # Setup threads

        self.web_worker = web_interface.WebWorker()
        self.web_worker.finished.connect(self.set_word_freq)

        # Setup data

        self.db = KindleDB(db_file)
        self.output_path = output_path
        self.importer_r = AnkiImporter()
        self.importer_rd = AnkiImporter()
        self.saving = False
        self.has_changed = False

        self.entries = []
        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.reload_data()

    def reload_data(self):

        self.entries = self.db.fetch_all(new_only=True)
        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()

        for (word_id, word, usage, title, authors, category) in self.entries:
            self.records.append({
                "status": -0xFF,  # undefined value, for set_record_status() to work properly
                "subject": word,
                "pron": "Unknown",
                "para": "",
                "ext": "",
                "usage": usage,  # plain text, bold will be applied at load_entry()
                "source": '<div align="right" style="font-size:12px"><I>%s</I>, %s</div>' % (title, authors),
                # read-only
                "hint": "",
                "img": None,  # no image
                "freq": 0,
                "card": 0,
                "tips": ""
            })

            self.entryList.addItem(word)
            self.set_record_status(self.entryList.count() - 1, 0)

        self.has_changed = False

        # Setup initial entry, must be after necessary initialization
        if len(self.records) > 0:
            self.entryList.setCurrentRow(0)
            self.load_entry(self.cur_idx())
            self.set_gui_enabled(True)
        else:
            self.subject.document().setPlainText("Congratulation!")  # subject change will lead to opening of dictionary
            self.paraphrase.document().setPlainText("There is nothing to be processed.")
            self.extension.document().setPlainText("Great work!")
            self.example.document().setPlainText("")
            self.source.document().setPlainText("")
            self.hint.document().setPlainText("")
            self.set_gui_enabled(False)
        self.update_progress_bar()

    def confirm_before_action(self, action_name):
        if self.has_changed:
            quit_msg = "Are you sure you want to %s? Unsaved edit will be lost." % action_name
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
        :param status: 0 - unread, -1 - discard, 1 confirmed
        :return:
        """

        if self.records[idx]["status"] == status:
            return

        self.has_changed = True

        f = self.entryList.font()
        if status == 0:  # unread

            f.setItalic(False)
            f.setStrikeOut(False)

            if self.records[idx]["status"] == 1:
                self.confirmed_count -= 1
            elif self.records[idx]["status"] == -1:
                self.discard_count -= 1

        elif status == 1:  # confirmed

            f.setItalic(True)
            f.setStrikeOut(False)

            self.confirmed_count += 1

        elif status == -1:  # discarded

            f.setItalic(False)
            f.setStrikeOut(True)

            self.discard_count += 1

        self.entryList.item(idx).setFont(f)
        self.update_progress_bar()

        self.records[idx]["status"] = status

    def update_progress_bar(self):
        self.unreadBar.setMaximum(len(self.records))
        self.unreadBar.setValue(len(self.records) - (self.confirmed_count + self.discard_count))
        self.confirmedBar.setMaximum(len(self.records))
        self.confirmedBar.setValue(self.confirmed_count)
        self.discardBar.setMaximum(len(self.records))
        self.discardBar.setValue(self.discard_count)

    def load_entry(self, idx):

        if idx < 0 or idx >= len(self.records):
            return

        r = self.records[idx]

        self.subject.document().setPlainText(r["subject"])  # subject change will lead to opening of dictionary

        if r["pron"] == "Samantha":
            self.pronSamantha.toggle()
        elif r["pron"] == "Daniel":
            self.pronDaniel.toggle()
        else:
            if not self.saving:
                self.pronSamantha.click()  # including toggling and first-time pronouncing

        if r["freq"] == 0 and not self.saving:
            self.web_worker.query(idx, r["subject"])
            # Later freqBar and cardType will be updated by set_word_freq() slot

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

    def move_to_next(self):
        if self.cur_idx() < len(self.entries) - 1:
            self.entryList.setCurrentRow(self.cur_idx() + 1)
            # Loading data will be completed by selected_changed()

    def next_click(self):
        self.set_record_status(self.cur_idx(), 1)  # confirmed
        self.move_to_next()

    def discard_click(self):
        self.set_record_status(self.cur_idx(), -1)  # discarded
        self.move_to_next()

    def selected_changed(self):
        self.load_entry(self.cur_idx())

    def pron_clicked(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        sender = self.sender()
        if sender:
            AnkiImporter.pronounce(self.records[self.cur_idx()]["subject"], sender.text())
            self.records[self.cur_idx()]["pron"] = sender.text()

    def subject_changed(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        subject = self.subject.toPlainText()
        self.records[self.cur_idx()]["subject"] = subject
        self.entryList.item(self.cur_idx()).setText(subject)
        if not self.saving:
            webbrowser.open("dict://%s" % subject, autoraise=False)
            self.raise_()

    def paraphrase_changed(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        self.records[self.cur_idx()]["para"] = self.paraphrase.toPlainText()

    def extension_changed(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        self.records[self.cur_idx()]["ext"] = self.extension.toPlainText()

    def example_changed(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        self.records[self.cur_idx()]["usage"] = self.example.toPlainText()  # bold won't be saved as html

    def hint_changed(self):
        if self.cur_idx() < 0 or self.cur_idx() >= len(self.records):
            return
        self.records[self.cur_idx()]["hint"] = self.hint.toPlainText()

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

    def save_all(self):

        self.set_gui_enabled(False)
        self.saveBar.setVisible(True)
        self.saveBar.setMaximum(len(self.records))
        self.saving = True

        save_file_r = "%s/kindle-r-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        save_file_rd = "%s/kindle-rd-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        self.importer_r.open_file(save_file_r)
        self.importer_rd.open_file(save_file_rd)
        for i in range(len(self.records)):

            # (status, subject, pronunciation, paraphrase, extension, usage, source, hint, img) = self.records[i]
            r = self.records[i]

            # Set UI
            self.saveBar.setValue(i)
            self.entryList.setCurrentRow(i)
            QtCore.QCoreApplication.processEvents()

            # Generate data
            if r["status"] == 1:  # confirmed

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
                                     r["hint"])

            # Write back to DB
            if r["status"] != 0:
                self.db.set_word_mature(self.entries[i][0], 100)

        self.importer_r.close_file()
        self.importer_rd.close_file()

        self.set_gui_enabled(True)
        self.saveBar.setVisible(False)
        self.saveBar.setValue(len(self.records))
        self.saving = False
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
                px = QtGui.QPixmap(mine_data.imageData()).scaledToHeight(self.imageLabel.height())
                self.records[self.cur_idx()]["img"] = px
                self.imageLabel.setPixmap(px)
        elif event.button() == QtCore.Qt.RightButton:
            webbrowser.open("https://www.google.com/search?tbm=isch&q=" + self.records[self.cur_idx()]["subject"])

    def image_double_click(self, event):
        self.records[self.cur_idx()]["img"] = None
        self.imageLabel.setText("Click \nto paste \nimage")

    def reload_click(self):
        if self.confirm_before_action("reload database"):
            self.reload_data()

    def freq_bar_double_click(self, event):
        webbrowser.open(web_interface.collins_url + self.records[self.cur_idx()]["subject"])

    @QtCore.pyqtSlot(int, int, str)
    def set_word_freq(self, idx, freq, tips):
        self.records[idx]["freq"] = freq
        if freq >= card_rd_threshold_:
            self.records[idx]["card"] = 1
        else:
            self.records[idx]["card"] = 0
        self.records[idx]["tips"] = tips

        if idx == self.cur_idx():
            self.freqBar.setValue(freq)
            self.freqBar.setToolTip(tips)
            self.cardType.setCurrentIndex(self.records[idx]["card"])


if __name__ == '__main__':

    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    if os.path.isfile(db_file_):
        mapleUtility = MapleUtility(app, db_file_, output_path_)
        mapleUtility.show()
    else:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText("Failed to find Kindle DB file. Please make sure Kindle has connected.")
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.show()

    sys.exit(app.exec_())
