#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog

from data_manager import *
from maple_utility import *
from web_query import *

# KINDLE_DB_FILENAME = "/Users/liuzikai/Documents/Programming/MapleVocabUtility/test_vocab._db"
KINDLE_DB_FILENAME = "/Volumes/Kindle/system/vocabulary/vocab._db"
SAVE_PATH = "/Users/liuzikai/Desktop"


class MapleUtility(QMainWindow, Ui_MapleUtility):
    WEB_QUERY_WORKER_COUNT = 6
    CARD_RD_THRESHOLD = 4

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
        self.queryCollins.clicked.connect(self.query_collins_clicked)
        self.queryGoogleImage.clicked.connect(self.query_google_images_clicked)
        self.queryGoogleTranslate.clicked.connect(self.query_google_translate_clicked)
        self.queryGoogle.clicked.connect(self.query_google_clicked)
        self.webLoadingView.setVisible(False)
        self.editor_components = [self.subject, self.subjectSuggest, self.freqBar, self.pronSamantha, self.pronDaniel,
                                  self.paraphrase, self.imageLabel, self.extension, self.example, self.checkSource,
                                  self.source, self.hint, self.checkR, self.checkS, self.checkD,
                                  self.queryCollins, self.queryGoogleImage, self.queryGoogleTranslate, self.queryGoogle]
        self.is_saving = False

        # Create WebViews and setup QueryManager
        self.qm = QueryManager(self.WEB_QUERY_WORKER_COUNT)
        self.query_worker = []
        self.create_query_workers()
        self.qm.start_worker.connect(self.start_query_worker)  # worker, url
        self.qm.interrupt_worker.connect(self.interrupt_query_worker)  # worker
        self.qm.worker_usage.connect(self.handle_worker_usage)  # finished, working, free
        # self.qm.worker_progress.connect()  # worker, progress
        self.qm.worker_activated.connect(self.activate_query_worker)  # worker, finished
        self.qm.active_worker_progress.connect(self.handle_active_worker_progress)  # active_worker, process
        self.qm.collins_suggestion_retrieved.connect(self.handle_collins_suggestion)  # original_subject, suggestion
        self.qm.collins_freq_retrieved.connect(self.set_word_freq)  # original_subject, freq, tip
        self.qm.report_worker_usage()

        # Setup DataManager and connections
        self.data = DataManager()
        self.data.record_status_changed.connect(self.handle_record_status_changed)  # index, old_status, new_status
        self.data.record_cleared.connect(self.handle_record_clear)
        self.data.record_inserted.connect(self.handle_record_insertion)  # index, batch_loading(True)/add_single(False)
        self.data.record_count_changed.connect(self.update_ui_after_record_count_changed)
        self.data.save_progress.connect(self.update_ui_during_saving)

        # Setup initial interface
        self.update_ui_after_record_count_changed()

    # ================================ Web Query Related ================================

    def create_query_workers(self) -> None:

        for i in range(self.WEB_QUERY_WORKER_COUNT):
            wv = QtWebEngineWidgets.QWebEngineView(self.webViewFrame)
            wv.setMinimumSize(QtCore.QSize(600, 0))
            wv.setMaximumSize(QtCore.QSize(600, 16777215))
            wv.setObjectName("webView_" + str(i))
            self.webViewVerticalLayout.addWidget(wv)
            wv.setVisible(False)
            self.query_worker.append(wv)

            wv.loadStarted.connect(lambda idx=i: self.qm.load_started(idx))
            wv.loadProgress.connect(lambda progress, idx=i: self.qm.load_progress(idx, progress))
            wv.loadFinished.connect(lambda ok, idx=i: self.qm.load_finished(idx, ok))

            wv.page().profile().setHttpUserAgent(self.qm.MAC_USER_AGENT)
            wv.page().profile().setProperty("X-Frame-Options", "Deny")

    @QtCore.pyqtSlot(int, str)
    def start_query_worker(self, idx: int, url: str):
        self.query_worker[idx].load(QtCore.QUrl(url))
        print("Worker %d starts on %s" % (idx, url))

    @QtCore.pyqtSlot(int)
    def interrupt_query_worker(self, idx: int):
        self.query_worker[idx].stop()
        print("Worker %d interrupted" % idx)

    @QtCore.pyqtSlot(int, int, int)
    def handle_worker_usage(self, finished: int, working: int, free: int):
        self.queryStatusLabel.setText("%d/%d/%d" % (finished, working, free))

    @QtCore.pyqtSlot(int, bool)
    def activate_query_worker(self, idx: int, finished: bool):
        for i in range(self.WEB_QUERY_WORKER_COUNT):
            self.query_worker[i].setVisible((i == idx))
        self.webLoadingView.setVisible(not finished)

    @QtCore.pyqtSlot(int, int)
    def handle_active_worker_progress(self, active_worker: int, progress: int):
        self.webLoadingBar.setValue(progress)

    @QtCore.pyqtSlot(str, int, str)
    def set_word_freq(self, subject: str, freq: int, tips: str):
        for r in self.data.get_by_subject(subject):
            r["freq"] = freq
            if freq >= self.CARD_RD_THRESHOLD:
                r["card"] = "RD"
            else:
                r["card"] = "R"
            r["tips"] = tips

        if self.cur_record()["subject"] == subject:
            self.editor_load_entry(self.cur_idx())

    @QtCore.pyqtSlot(str, str)
    def handle_collins_suggestion(self, original_subject: str, suggestion: str):
        for r in self.data.get_by_subject(original_subject):
            r["suggestion"] = suggestion

        if self.cur_record()["subject"] == original_subject:
            self.editor_load_entry(self.cur_idx())

    # ================================ Data Manager Related Slots ================================

    @QtCore.pyqtSlot(int, bool)
    def handle_record_insertion(self, idx: int, batch_loading: bool):
        subject = self.data.get(idx)["subject"]
        self.entryList.selectionModel().blockSignals(True)  # -------- entryList signals blocked -------->
        self.entryList.insertItem(idx, subject)
        self.entryList.selectionModel().blockSignals(False)  # <-------- entryList signals unblocked --------
        if not batch_loading:
            self.entryList.setCurrentRow(idx)  # will trigger editor_load_entry()
            self.subject.setFocus()
        else:
            self.qm.queue(self.data.get(idx)["subject"], self.qm.COLLINS)

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
        self.unreadBar.setValue(self.data.count(self.data.UNVIEWED) + self.data.count(self.data.TOPROCESS))
        self.unreadBar.setToolTip("%d unread" % self.unreadBar.value())
        self.confirmedBar.setMaximum(self.data.count())
        self.confirmedBar.setValue(self.data.count(self.data.CONFIRMED))
        self.confirmedBar.setToolTip("%d confirmed" % self.confirmedBar.value())
        self.discardBar.setMaximum(self.data.count())
        self.discardBar.setValue(self.data.count(self.data.DISCARDED))
        self.discardBar.setToolTip("%d discarded" % self.discardBar.value())

    @QtCore.pyqtSlot()
    def handle_record_clear(self):
        self.qm.reset()
        self.entryList.selectionModel().blockSignals(True)
        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()
        self.entryList.selectionModel().blockSignals(False)

    @QtCore.pyqtSlot(int, int, int)
    def handle_record_status_changed(self, idx: int, _: int, new_status: int):
        f = self.entryList.font()
        if new_status == self.data.TOPROCESS:
            f.setItalic(False)
            f.setStrikeOut(False)
        elif new_status == self.data.CONFIRMED:
            f.setItalic(True)
            f.setStrikeOut(False)
        elif new_status == self.data.DISCARDED:
            f.setItalic(False)
            f.setStrikeOut(True)
        self.entryList.item(idx).setFont(f)

    @QtCore.pyqtSlot(int)
    def update_ui_during_saving(self, idx: int):
        self.saveBar.setValue(idx)
        self.entryList.setCurrentRow(idx)
        QtCore.QCoreApplication.processEvents()

    # ================================ Data Related Helper Functions ================================

    def cur_idx(self):
        return self.entryList.currentRow()

    def cur_record(self):
        return self.data.get(self.cur_idx())

    # ================================ UI Helper Functions ================================

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

    def editor_load_entry(self, idx):
        assert 0 <= idx <= self.data.count(), "Invalid index"

        r = self.data.get(idx)

        self.editor_block_signals(True)  # -------- main editor signals blocked -------->

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

        suggestion = r.get("suggestion")
        if suggestion is not None and suggestion != r["subject"]:
            self.subjectSuggest.setText("Suggest: " + suggestion)
            self.subjectSuggest.setVisible(True)

        self.editor_block_signals(False)  # <-------- main editor signals unblocked --------

    def move_to_next(self):
        self.qm.discard_by_subject(self.cur_record()["subject"])
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

    # ================================ UI Slots and Event Handler ================================

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                if (widget is self.subject) or (widget is self.paraphrase and self.paraphrase.toPlainText() == ""):
                    self.data.set_status(self.cur_idx(), self.data.UNVIEWED)
                    self.selected_changed()
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

    def closeEvent(self, event):
        if self.confirm_before_action("exit"):
            event.accept()
        else:
            event.ignore()

    @QtCore.pyqtSlot()
    def confirm_clicked(self):
        self.data.set_status(self.cur_idx(), self.data.CONFIRMED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def discard_clicked(self):
        self.data.set_status(self.cur_idx(), self.data.DISCARDED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def selected_changed(self):
        self.editor_load_entry(self.cur_idx())

        r = self.cur_record()
        if not self.is_saving:
            if r["subject"] != "":
                if r["status"] == self.data.UNVIEWED:
                    self.pronSamantha.click()  # including toggling and first-time pronouncing
                    self.data.set_status(self.cur_idx(), self.data.TOPROCESS)
                self.qm.request(r["subject"], self.qm.COLLINS)

    @QtCore.pyqtSlot()
    def pron_clicked(self):
        sender = self.sender()
        if sender:
            DataExporter.pronounce(self.cur_record()["subject"], sender.text())
            self.cur_record()["pron"] = sender.text()

    @QtCore.pyqtSlot()
    def subject_changed(self):
        self.qm.discard_by_subject(self.cur_record()["subject"])  # discard queries on original subject
        subject = self.subject.toPlainText()
        self.cur_record()["subject"] = subject
        self.entryList.item(self.cur_idx()).setText(subject)

    @QtCore.pyqtSlot()
    def suggest_clicked(self):
        # self.subject.blockSignals(True)
        self.subject.setPlainText(self.subjectSuggest.text()[len("Suggest: "):])
        # self.subject.blockSignals(False)
        self.subjectSuggest.setVisible(False)

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
                          self.data.count(self.data.CONFIRMED), self.data.count(self.data.DISCARDED),
                          self.data.count(self.data.UNVIEWED) + self.data.count(self.data.TOPROCESS))

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

            info = "Saved %d entries. Discard %d entries. %d entries unchanged.\n\n" \
                   "Saved to %s" % (
                       self.data.count(self.data.CONFIRMED),
                       self.data.count(self.data.DISCARDED),
                       self.data.count(self.data.UNVIEWED) + self.data.count(self.data.TOPROCESS),
                       filename)
            QtWidgets.QMessageBox.information(self, "Success", info, QtWidgets.QMessageBox.Ok)

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
            self.query_google_images_clicked()

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
        self.query_collins_clicked()

    @QtCore.pyqtSlot()
    def confirm_and_smart_duplicate_entry(self):
        self.data.set_status(self.cur_idx(), self.data.CONFIRMED)
        self.smart_duplicate_entry()

    @QtCore.pyqtSlot()
    def smart_duplicate_entry(self):
        cursor = self.example.textCursor()
        selection = cursor.selectedText()
        if selection == "":
            return
        r = self.cur_record()
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
    def card_type_changed(self):
        self.cur_record()["card"] = "%s%s%s" % ("R" if self.checkR.isChecked() else "",
                                                "S" if self.checkS.isChecked() else "",
                                                "D" if self.checkD.isChecked() else "")

    @QtCore.pyqtSlot()
    def query_collins_clicked(self):
        self.qm.request(self.cur_record()["subject"], self.qm.COLLINS)

    @QtCore.pyqtSlot()
    def query_google_images_clicked(self):
        self.qm.request(self.cur_record()["subject"], self.qm.GOOGLE_IMAGE)

    @QtCore.pyqtSlot()
    def query_google_translate_clicked(self):
        self.qm.request(self.cur_record()["subject"], self.qm.GOOGLE_TRANSLATE)

    @QtCore.pyqtSlot()
    def query_google_clicked(self):
        self.qm.request(self.cur_record()["subject"], self.qm.GOOGLE)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility(app)
    mapleUtility.showMaximized()

    sys.exit(app.exec_())
