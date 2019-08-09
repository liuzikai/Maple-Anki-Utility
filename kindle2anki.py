import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from maple_utility import *
from anki_interface import *
from kindle_db import *
from datetime import datetime
import webbrowser

# db_file = "/Users/liuzikai/Documents/Programming/Kindle2Anki/vocab.db"
db_file_ = "/Volumes/Kindle/system/vocabulary/vocab.db"
output_path_ = "/Users/liuzikai/Desktop"


class MapleUtility(QMainWindow, Ui_MapleUtility):

    def __init__(self, db_file, output_path, new_only=True, parent=None):

        # Setup UI

        super(MapleUtility, self).__init__(parent)
        self.setupUi(self)

        self.setCentralWidget(self.mainWidget)
        self.nextButton.clicked.connect(self.next_click)
        self.discardButton.clicked.connect(self.discard_click)
        self.entryList.selectionModel().selectionChanged.connect(self.selected_changed)
        self.pronSamantha.clicked.connect(self.pron_clicked)
        self.pronDaniel.clicked.connect(self.pron_clicked)
        self.subject.textChanged.connect(self.subject_changed)
        self.paraphrase.textChanged.connect(self.paraphrase_changed)
        self.extension.textChanged.connect(self.extension_changed)
        self.example.textChanged.connect(self.example_changed)
        self.hint.textChanged.connect(self.hint_changed)
        self.saveAllButton.clicked.connect(self.save_all_clicked)
        self.next_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.next_shortcut.activated.connect(self.next_click)
        self.discard_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_click)

        # Setup data

        self.db = KindleDB(db_file)
        self.output_path = output_path
        self.importer = AnkiImporter()

        self.entries = self.db.fetch_all(new_only)
        self.records = []
        self.discard_count = 0
        self.confirmed_count = 0

        self.entryList.clear()
        for (word_id, word, usage, title, authors, category) in self.entries:
            # (status, subject, pronunciation, paraphrase, extension, usage, source, hint)
            self.records.append([
                -0xFF,  # undefined value, for set_record_status() to work properly
                word,
                "Unknown",
                "",
                "",
                usage,  # plain text, bold will be applied at load_entry()
                '<div align="right" style="font-size:12px"><I>%s</I>, %s</div>' % (title, authors),  # read-only
                ""
            ])

            self.entryList.addItem(word)
            self.set_record_status(self.entryList.count() - 1, 0)

        self.saving = False

        # Setup initial entry, must be after necessary initialization

        self.entryList.setCurrentRow(0)
        self.load_entry(self.cur_idx())

        self.update_progress_bar()

    def cur_idx(self):
        return self.entryList.currentRow()

    def set_record_status(self, idx, status):
        """
        Set UI and record entry
        :param idx:
        :param status: 0 - unread, -1 - discard, 1 confirmed
        :return:
        """

        if self.records[idx][0] == status:
            return

        f = self.entryList.font()
        if status == 0:  # unread

            f.setItalic(False)
            f.setStrikeOut(False)

            if self.records[idx][0] == 1:
                self.confirmed_count -= 1
            elif self.records[idx][0] == -1:
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

        self.records[idx][0] = status

    def update_progress_bar(self):
        self.progressBar.setMaximum(len(self.records))
        self.progressBar.setValue(self.confirmed_count + self.discard_count)

    def load_entry(self, idx):
        (status, subject, pronunciation, paraphrase, extension, usage, source, hint) = self.records[idx]

        self.subject.document().setPlainText(subject)  # subject change will lead to opening of dictionary

        if pronunciation == "Samantha":
            self.pronSamantha.toggle()
        elif pronunciation == "Daniel":
            self.pronDaniel.toggle()
        else:
            if not self.saving:
                self.pronSamantha.click()  # including toggling and first-time pronouncing

        self.paraphrase.document().setPlainText(paraphrase)
        self.extension.document().setPlainText(extension)
        self.example.document().setHtml(usage.replace(subject, u"<b>%s</b>" % subject))  # bold won't be saved as html
        self.source.document().setHtml(source)  # read-only
        self.hint.document().setPlainText(hint)

    def move_to_next(self):
        if self.cur_idx() < len(self.entries) - 1:
            self.entryList.setCurrentRow(self.cur_idx() + 1)
            # loading data will be completed by selected_changed()

    def next_click(self):
        self.set_record_status(self.cur_idx(), 1)  # confirmed
        self.move_to_next()

    def discard_click(self):
        self.set_record_status(self.cur_idx(), -1)  # discarded
        self.move_to_next()

    def selected_changed(self):
        self.load_entry(self.cur_idx())

    def pron_clicked(self):
        sender = self.sender()
        if sender:
            AnkiImporter.pronounce(self.records[self.cur_idx()][1], sender.text())
            self.records[self.cur_idx()][2] = sender.text()

    def subject_changed(self):
        subject = self.subject.toPlainText()
        self.records[self.cur_idx()][1] = subject
        self.entryList.item(self.cur_idx()).setText(subject)
        if not self.saving:
            webbrowser.open("dict://%s" % subject, autoraise=False)
            self.raise_()

    def paraphrase_changed(self):
        self.records[self.cur_idx()][3] = self.paraphrase.toPlainText()

    def extension_changed(self):
        self.records[self.cur_idx()][4] = self.extension.toPlainText()

    def example_changed(self):
        self.records[self.cur_idx()][5] = self.example.toPlainText()  # bold won't be saved as html

    def hint_changed(self):
        self.records[self.cur_idx()][7] = self.hint.toPlainText()

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
        self.extension.setEnabled(value)
        self.example.setEnabled(value)
        self.source.setEnabled(value)
        self.hint.setEnabled(value)

    def save_all(self):

        self.set_gui_enabled(False)
        self.progressBar.setMaximum(len(self.records))
        self.saving = True

        save_file = "%s/kindle-%s.txt" % (self.output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        self.importer.open_file(save_file)
        for i in range(len(self.records)):

            (status, subject, pronunciation, paraphrase, extension, usage, source, hint) = self.records[i]

            # Set UI
            self.progressBar.setValue(i)
            self.entryList.setCurrentRow(i)
            QtCore.QCoreApplication.processEvents()

            # Generate data
            if status == 1:  # confirmed
                example = '%s<br>%s' % (usage, source)
                mp3 = self.importer.generate_media(subject, pronunciation)
                self.importer.write_entry(subject.replace("\n", "<br>"), "[sound:%s]" % mp3, paraphrase, extension, example, hint)

            # Write back to DB
            if status != 0:
                self.db.set_word_mature(self.entries[i][0], 100)

        self.importer.close_file()

        self.set_gui_enabled(True)
        self.progressBar.setValue(len(self.records))
        self.saving = False

        return save_file

    def closeEvent(self, event):

        quit_msg = "Are you sure you want to exit the program? Unsaved edit will be lost."
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + '1024.png'))

    if os.path.isfile(db_file_):
        mapleUtility = MapleUtility(db_file_, output_path_)
        mapleUtility.show()
    else:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText("Failed to find Kindle DB file. Please make sure Kindle has connected.")
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.show()

    sys.exit(app.exec_())
