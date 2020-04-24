#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
import urllib.parse

from maple_utility import *
from data_manager import *
from web_query import *

# KINDLE_DB_FILENAME = "/Users/liuzikai/Documents/Programming/MapleVocabUtility/test_vocab._db"
KINDLE_DB_FILENAME = "/Volumes/Kindle/system/vocabulary/vocab._db"
SAVE_PATH = "/Users/liuzikai/Desktop"


class MapleUtility(QMainWindow, Ui_MapleUtility):

    CARD_RD_THRESHOLD = 4

    web_to_html_finished = pyqtSignal()

    def __init__(self, app, parent=None):

        self.app = app

        # Setup UI and connections
        super(MapleUtility, self).__init__(parent)
        self.setupUi(self)
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
        self.confirm_and_smart_duplicate_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Return"), self)
        self.confirm_and_smart_duplicate_shortcut.activated.connect(self.confirm_and_smart_duplicate_entry)
        self.discard_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_clicked)
        self.new_entry_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_clicked)
        self.smart_duplicate_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+N"), self)
        self.smart_duplicate_shortcut.activated.connect(self.smart_duplicate_entry)
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
        self.webView.page().profile().setHttpUserAgent(mac_user_agent)
        self.webView.page().profile().setProperty("X-Frame-Options", "Deny")
        self.queryCollins.clicked.connect(self.query_collins_clicked)
        self.queryGoogleImage.clicked.connect(self.query_google_images_clicked)
        self.queryGoogleTranslate.clicked.connect(self.query_google_translate_clicked)
        self.queryGoogle.clicked.connect(self.query_google_clicked)
        self.webLoadingView.setVisible(False)
        self.editor_components = [self.subject, self.subjectSuggest, self.freqBar, self.pronSamantha, self.pronDaniel,
                                  self.paraphrase, self.imageLabel, self.extension, self.example, self.checkSource,
                                  self.source, self.hint, self.checkR, self.checkS, self.checkD, self.autoQuery,
                                  self.queryCollins, self.queryGoogleImage, self.queryGoogleTranslate, self.queryGoogle]
        self.is_saving = False

        # Create WebViews and setup QueryManager
        # TODO

        # Setup DataManager and connections
        self.data = DataManager()
        self.data.record_status_changed.connect(self.handle_record_status_changed) # index, old_status, new_status
        self.data.record_cleared.connect(self.handle_record_clear)
        self.data.record_inserted.connect(self.handle_record_insertion)  # index, batch_loading(True)/add_single(False)
        self.data.record_count_changed.connect(self.update_ui_after_record_count_changed)
        self.data.save_progress.connect(self.update_ui_during_saving)

        # Setup initial interface
        self.update_ui_after_record_count_changed()


    # TODO: add QtWebEngineView dynamically
    def ():
        self.verticalLayout_6.addWidget(self.webLoadingView)
        self.webView = QtWebEngineWidgets.QWebEngineView(self.widget_8)
        self.webView.setMinimumSize(QtCore.QSize(600, 0))
        self.webView.setMaximumSize(QtCore.QSize(600, 16777215))
        self.webView.setObjectName("webView")
        self.verticalLayout_6.addWidget(self.webView)
        self.verticalLayout_2.addWidget(self.widget_8)

    @QtCore.pyqtSlot()
    def update_ui_after_record_count_changed(self):
        if self.data.count() > 0:
            self.set_gui_enabled(True)
            self.freqBar.setMaximum(5)
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

        self.unreadBar.setMaximum(self.data.count())
        self.unreadBar.setValue(self.data.count(UNVIEWED) + self.data.count(TOPROCESS))
        self.unreadBar.setToolTip("%d unread" % self.unreadBar.value())
        self.confirmedBar.setMaximum(self.data.count())
        self.confirmedBar.setValue(self.data.count(CONFIRMED))
        self.confirmedBar.setToolTip("%d confirmed" % self.confirmedBar.value())
        self.discardBar.setMaximum(self.data.count())
        self.discardBar.setValue(self.data.count(DISCARDED))
        self.discardBar.setToolTip("%d discarded" % self.discardBar.value())

    def confirm_before_action(self, action_name):
        """
        If no changes are made, this function automatically return True.
        If unsaved changes are made, this function asks user to confirm.
        :param action_name: the action to be performed. Will be shown in the dialog box
        :return: True if no changes or user confirmed, False if user canceled.
        """
        if self.data.has_changed:
            quit_msg = "Are you sure you want to %s? Unsaved entries will be lost." % action_name
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            return reply == QtWidgets.QMessageBox.Yes
        else:
            return True

    def cur_idx(self):
        return self.entryList.currentRow()

    def cur_record(self):
        return self.data.get(self.cur_idx())

    def editor_load_entry(self, idx, forced_query=False):
        if idx < 0 or idx >= self.data.count():  # sanity check
            return

        r = self.data.get(idx)

        if not self.is_saving:
            if r["subject"] != "":
                if r["status"] == UNVIEWED:
                    self.pronSamantha.click()  # including toggling and first-time pronouncing
                    self.data.set_status(idx, TOPROCESS)

                if self.autoQuery.isChecked() or forced_query:
                    if forced_query or self.query_immediately:
                        self.request_query(0)
                        self.query_immediately = False
                    else:
                        self.request_query(self.AUTO_QUERY_DELAY, True)
                    # Later query will be handled by timer signal

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

    @QtCore.pyqtSlot(int, bool)
    def handle_record_insertion(self, idx: int, batch_loading: bool):
        self.entryList.blockSignals(True)  # ---------------- entryList signals blocked ---------------->
        self.entryList.insertItem(idx, self.data.get(idx)["subject"])
        self.entryList.blockSignals(False)  # <---------------- entryList signals unblocked ----------------
        if not batch_loading:
            self.entryList.setCurrentRow(idx)  # will trigger editor_load_entry()
            self.subject.setFocus()

    def move_to_next(self):
        if self.cur_idx() < self.data.count() - 1:
            self.entryList.setCurrentRow(self.cur_idx() + 1)
            # Loading data will be completed by selected_changed()
        elif self.cur_idx() == self.data.count() - 1:
            self.add_new_entry_clicked()

    def set_gui_enabled(self, value):
        for component in [self.confirmButton, self.discardButton, self.saveAllButton] + self.editor_components:
            component.setEnabled(value)

    def editor_block_signals(self, value):
        for component in self.editor_components:
            component.blockSignals(value)

    @QtCore.pyqtSlot(int)
    def update_ui_during_saving(self, idx: int):
        self.saveBar.setValue(idx)
        self.entryList.setCurrentRow(idx)
        QtCore.QCoreApplication.processEvents()

    # -------------------------------- UI Signal Handlers --------------------------------

    @QtCore.pyqtSlot()
    def confirm_clicked(self):
        self.data.set_status(self.cur_idx(), CONFIRMED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def discard_clicked(self):
        self.data.set_status(self.cur_idx(), DISCARDED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def selected_changed(self):
        self.editor_load_entry(self.cur_idx())

    @QtCore.pyqtSlot()
    def pron_clicked(self):
        sender = self.sender()
        if sender:
            DataExporter.pronounce(self.cur_record()["subject"], sender.text())
            self.cur_record()["pron"] = sender.text()

    @QtCore.pyqtSlot()
    def subject_changed(self):
        subject = self.subject.toPlainText()
        self.cur_record()["subject"] = subject
        # self.cur_record()["freq"] = 0
        self.entryList.item(self.cur_idx()).setText(subject)
        # self.editor_load_entry(self.cur_idx())

    @QtCore.pyqtSlot()
    def suggest_clicked(self):
        # self.subject.blockSignals(True)
        self.subject.setPlainText(self.suggested_word)
        # self.subject.blockSignals(False)
        self.subjectSuggest.setVisible(False)

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                if (widget is self.subject) or (widget is self.paraphrase and self.paraphrase.toPlainText() == ""):
                    self.data.set_status(self.cur_idx(), UNVIEWED)
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

    @QtCore.pyqtSlot()
    def paraphrase_changed(self):
        self.cur_record()["para"] = self.paraphrase.toHtml()

    @QtCore.pyqtSlot()
    def extension_changed(self):
        self.cur_record()["ext"] = self.extension.toHtml()

    @QtCore.pyqtSlot()
    def example_changed(self):
        self.cur_record()["usage"] = self.example.toHtml()

    @QtCore.pyqtSlot()
    def source_changed(self):
        self.cur_record()["source"] = self.source.toHtml()

    @QtCore.pyqtSlot()
    def source_check_changed(self):
        self.source.setEnabled(self.checkSource.isChecked())
        self.cur_record()["source_enabled"] = self.checkSource.isChecked()
        self.source.setHtml('<div align="right">' + self.source.toHtml() + '</div>')

    @QtCore.pyqtSlot()
    def hint_changed(self):
        self.cur_record()["hint"] = self.hint.toPlainText()

    @QtCore.pyqtSlot()
    def save_all_clicked(self):
        confirm_str = "%d confirmed, %d discarded, %d unread.\n\n" \
                      "Only confirmed ones will be saved. " \
                      "Confirmed and discarded ones will be marked as mutual on Kindle. " \
                      "Please make sure kindle is connected. \n\n" \
                      "Continue to save?" % (
                          self.data.count(CONFIRMED), self.data.count(DISCARDED),
                          self.data.count(UNVIEWED) + self.data.count(TOPROCESS))

        ret = QtWidgets.QMessageBox.question(self, "Confirm", confirm_str, QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.Cancel)

        if ret == QtWidgets.QMessageBox.Yes:
            self.set_gui_enabled(False)  # ---------------- GUI disabled ---------------->
            self.editor_block_signals(True)  # ---------------- editor signals blocked ---------------->
            self.saveBar.setVisible(True)
            self.saveBar.setMaximum(self.data.count())

            self.is_saving = True

            filename = self.data.save_all(SAVE_PATH)

            self.entryList.setCurrentRow(self.data.count() - 1)  # set selection to last
            self.set_gui_enabled(True)  # <---------------- GUI enabled ----------------
            self.editor_block_signals(False)  # <---------------- editor signals unblocked ----------------
            self.saveBar.setVisible(False)
            self.saveBar.setValue(self.data.count())

            self.is_saving = False

            QtWidgets.QMessageBox.information(self, "Success",
                                              "Saved %d entries. Discard %d entries. %d entries unchanged.\n\n" \
                                              "Saved to %s" % (
                                                  self.data.count(CONFIRMED), self.data.count(DISCARDED),
                                                  self.data.count(UNVIEWED) + self.data.count(TOPROCESS),
                                                  filename),
                                              QtWidgets.QMessageBox.Ok)

    def closeEvent(self, event):
        if self.confirm_before_action("exit"):
            event.accept()
        else:
            event.ignore()

    @QtCore.pyqtSlot()
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
            # self.webView.page().profile().setHttpUserAgent(mac_user_agent)
            self.webView.load(QtCore.QUrl(google_image_url % urllib.parse.quote(self.cur_record()["subject"])))

    @QtCore.pyqtSlot()
    def image_double_clicked(self, event):
        self.cur_record()["img"] = None
        self.imageLabel.setText("Click \nto paste \nimage")

    @QtCore.pyqtSlot()
    def load_kindle_clicked(self) -> bool:
        if self.confirm_before_action("reload database"):
            if not self.data.reload_kindle_data(KINDLE_DB_FILENAME):
                self.report_error("Failed to find Kindle DB file. Please make sure Kindle has connected.")
                return False
        return True

    @QtCore.pyqtSlot()
    def load_csv_clicked(self) -> bool:
        if self.confirm_before_action("reload database"):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            csv_file, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                      "CSV Files (*.csv);;All Files (*)", options=options)
            if csv_file:
                if not self.data.reload_csv_data(csv_file):
                    self.report_error("Failed to load CSV file.")
                    return False

        return True

    @staticmethod
    def report_error(info: str) -> None:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText(info)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

    @QtCore.pyqtSlot()
    def freq_bar_double_clicked(self, event):
        self.request_query(0)  # reload website immediately

    @QtCore.pyqtSlot()
    def confirm_and_smart_duplicate_entry(self):
        self.data.set_status(self.cur_idx(), CONFIRMED)
        self.smart_duplicate_entry()

    @QtCore.pyqtSlot()
    def smart_duplicate_entry(self):
        cursor = self.example.textCursor()
        selection = cursor.selectedText()
        if selection == "":
            return
        r = self.cur_record()
        self.query_immediately = True  # if auto query is enabled, surly we want to query the new word immediately
        self.data.add_new_single_entry(self.cur_idx() + 1,
                                       selection,
                                       self.example.toPlainText().replace(selection, '<b>%s</b>' % selection),
                                       r["source_enabled"],
                                       r["source"])

    @QtCore.pyqtSlot()
    def add_new_entry_clicked(self):
        if self.app.keyboardModifiers() == QtCore.Qt.ShiftModifier and self.cur_idx() != -1:
            self.data.add_new_single_entry(self.cur_idx() + 1,
                                           "",
                                           self.cur_record()["usage"],
                                           self.cur_record()["source_enabled"],
                                           self.cur_record()["source"])
        else:
            self.data.add_new_single_entry(self.cur_idx() + 1)

    @QtCore.pyqtSlot()
    def clear_list_clicked(self):
        if self.confirm_before_action("clear list manually"):
            self.data.clear()

    @QtCore.pyqtSlot()
    def handle_record_clear(self):
        self.entryList.blockSignals(True)
        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()
        self.entryList.blockSignals(False)

    @QtCore.pyqtSlot()
    def card_type_changed(self):
        self.cur_record()["card"] = "%s%s%s" % ("R" if self.checkR.isChecked() else "",
                                                "S" if self.checkS.isChecked() else "",
                                                "D" if self.checkD.isChecked() else "")

    @QtCore.pyqtSlot(int, int, int)
    def handle_record_status_changed(self, idx: int, _: int, new_status: int):
        f = self.entryList.font()
        if new_status == TOPROCESS:
            f.setItalic(False)
            f.setStrikeOut(False)
        elif new_status == CONFIRMED:
            f.setItalic(True)
            f.setStrikeOut(False)
        elif new_status == DISCARDED:
            f.setItalic(False)
            f.setStrikeOut(True)
        self.entryList.item(idx).setFont(f)

    @QtCore.pyqtSlot()
    def query_collins_clicked(self):
        self.request_query(0)

    @QtCore.pyqtSlot()
    def query_google_images_clicked(self):
        self.web_query(google_image_url % urllib.parse.quote(self.cur_record()["subject"]))

    @QtCore.pyqtSlot()
    def query_google_translate_clicked(self):
        self.web_query(google_translate_url % urllib.parse.quote(self.cur_record()["subject"]))

    @QtCore.pyqtSlot()
    def query_google_clicked(self):
        self.web_query(google_url % urllib.parse.quote(self.cur_record()["subject"]))


    def set_word_freq(self, idx: int, freq: int, tips: str) -> None:
        r = self.data.get(idx)
        r["freq"] = freq
        if freq >= self.CARD_RD_THRESHOLD:
            r["card"] = "RD"
        else:
            r["card"] = "R"
        r["tips"] = tips

        if idx == self.cur_idx():
            self.freqBar.setValue(freq)
            self.freqBar.setToolTip(tips)
            self.checkR.setChecked("R" in r["card"])
            self.checkS.setChecked("S" in r["card"])
            self.checkD.setChecked("D" in r["card"])



if __name__ == '__main__':
    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility(app)
    mapleUtility.showMaximized()

    sys.exit(app.exec_())
