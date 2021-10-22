# -*- coding: utf-8 -*-

# To compile pyqt: pyuic5 maple_utility.ui > maple_utility.py

import sys
import os
from typing import Optional, Dict, cast
from PyQt6 import QtCore, QtWidgets, QtGui
from data_manager import DataManager, Record, RecordStatus
from maple_utility import Ui_MapleUtility
from web_query_view import WebQueryView, QueryType, QuerySettings

# KINDLE_DB_FILENAME = "/Users/liuzikai/Documents/Programming/MapleVocabUtility/resource/test_vocab.db"
KINDLE_DB_FILENAME = "/Volumes/Kindle/system/vocabulary/vocab.db"
CSV_DEFAULT_DIRECTORY = "/Users/liuzikai/Documents/Archive/GRE"
THINGS_VOCAB_LIST = "English Quick List"
SAVE_PATH = "/Users/liuzikai/Desktop"
ANKI_MEDIA_PATH = "/Users/liuzikai/Library/Application Support/Anki2/liuzikai/collection.media"


class MapleUtility(QtWidgets.QMainWindow, Ui_MapleUtility):
    """MapleVocabUtility MainWindow."""

    CARD_RD_THRESHOLD = 4

    def __init__(self, parent=None):

        # Setup UI and connections
        super(MapleUtility, self).__init__(parent)
        self.setupUi(self)
        self.setCentralWidget(self.mainWidget)
        self.confirmButton.clicked.connect(self.confirm_clicked)
        self.discardButton.clicked.connect(self.discard_clicked)
        self.entryList.selectionModel().selectionChanged.connect(self.selected_changed)
        self.subject.textChanged.connect(self.subject_changed)
        self.subject.installEventFilter(self)  # response to Return key
        self.subjectSuggest.setVisible(False)
        self.subjectSuggest.clicked.connect(self.suggest_clicked)
        self.pronA.clicked.connect(self.pron_clicked)
        self.pronB.clicked.connect(self.pron_clicked)
        self.paraphrase.textChanged.connect(self.paraphrase_changed)
        self.paraphrase.installEventFilter(self)  # response to Ctrl + I/B
        self.extension.textChanged.connect(self.extension_changed)
        self.extension.installEventFilter(self)  # response to Ctrl + I/B
        self.example.textChanged.connect(self.example_changed)
        self.example.installEventFilter(self)  # response to Ctrl + I/B
        self.checkSource.stateChanged.connect(self.source_check_changed)
        self.source.textChanged.connect(self.source_changed)
        self.source.installEventFilter(self)  # response to Ctrl + I/B
        self.hint.textChanged.connect(self.hint_changed)
        # These shortcuts are global
        self.confirm_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self.confirm_shortcut.activated.connect(self.confirm_clicked)
        self.confirm_and_smart_duplicate_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Return"), self)
        self.confirm_and_smart_duplicate_shortcut.activated.connect(self.confirm_and_smart_duplicate_entry)
        self.confirmButton.setToolTip("Shortcut: Ctrl + Return\nConfirm and smart duplicate: Ctrl + Shift + Return")
        self.discard_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_clicked)
        self.discardButton.setToolTip("Shortcut: Ctrl + Alt + Return")
        self.new_entry_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_clicked)
        self.smart_duplicate_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+N"), self)
        self.smart_duplicate_shortcut.activated.connect(self.smart_duplicate_entry)
        self.newEntry.setToolTip("Shortcut: Ctrl + N\nSmart duplicate: Ctrl + Shift + N")
        # There is no mouse signal for label. Override functions.
        self.imageLabel.mousePressEvent = self.image_clicked
        self.imageLabel.mouseDoubleClickEvent = self.image_double_clicked
        self.englishMode.clicked.connect(self.change_to_english_mode)
        self.deutschMode.clicked.connect(self.change_to_deutsch_mode)
        self.loadKindle.clicked.connect(self.load_kindle_clicked)
        self.loadCSV.clicked.connect(self.load_csv_clicked)
        self.loadThings.clicked.connect(self.load_things_clicked)
        self.newEntry.clicked.connect(self.add_new_entry_clicked)
        self.clearList.clicked.connect(self.clear_list_clicked)
        self.checkR.stateChanged.connect(self.card_type_changed)
        self.checkS.stateChanged.connect(self.card_type_changed)
        self.checkD.stateChanged.connect(self.card_type_changed)
        self.queryCollins.clicked.connect(self.query_collins_clicked)
        self.queryGoogleImage.clicked.connect(self.query_google_images_clicked)
        self.queryGoogleTranslate.clicked.connect(self.query_google_translate_clicked)
        self.queryGoogle.clicked.connect(self.query_google_clicked)
        self.webLoadingView.setVisible(False)
        self.editor_components = [self.subject, self.subjectSuggest, self.freqBar, self.pronA, self.pronB,
                                  self.paraphrase, self.imageLabel, self.extension, self.example, self.checkSource,
                                  self.source, self.hint, self.checkR, self.checkS, self.checkD,
                                  self.queryCollins, self.queryGoogleImage, self.queryGoogleTranslate, self.queryGoogle]

        # Setup WebQueryView
        self.wqv = WebQueryView(self.webViewFrame)
        self.wqv.setMinimumSize(QtCore.QSize(600, 0))
        self.wqv.setMaximumSize(QtCore.QSize(600, 16777215))
        self.webViewVerticalLayout.insertWidget(0, self.wqv)
        self.wqv.usage_updated.connect(self.handle_query_worker_usage)
        self.wqv.active_worker_progress.connect(self.handle_active_worker_progress)
        self.wqv.collins_suggestion_retrieved.connect(self.handle_collins_suggestion)
        self.wqv.collins_freq_retrieved.connect(self.set_word_freq)
        self.forceStopQuery.clicked.connect(self.wqv.force_stop_active_worker)
        self.wqv.report_worker_usage()  # update query usage label

        # Setup DataManager and connections
        self.data = DataManager(SAVE_PATH, ANKI_MEDIA_PATH)
        self.data.record_inserted.connect(self.handle_record_insertion)  # cid, batch_loading(True) / add_single(False)
        self.data.record_status_changed.connect(self.handle_record_status_changed)  # cid, old_status, new_status
        self.data.record_cleared.connect(self.handle_record_clear)
        self.data.record_count_changed.connect(self.update_ui_after_record_count_changed)
        self.data.batch_load_finished.connect(self.handle_record_batch_load_finished)

        # QListWidgetItem can only be deleted when records are cleared
        self.cid_to_item: Dict[int, QtWidgets.QListWidgetItem] = {}

        # Setup initial UI
        self.update_ui_after_record_count_changed()

    # ================================ Web Query Related ================================

    @QtCore.pyqtSlot(int, int, int)
    def handle_query_worker_usage(self, finished: int, working: int, free: int):
        self.queryStatusLabel.setText("%d/%d/%d" % (finished, working, free))

    @QtCore.pyqtSlot(int)
    def handle_active_worker_progress(self, progress: int):
        if progress == -1:
            self.webLoadingView.setVisible(False)
        else:
            self.webLoadingView.setVisible(True)
            self.webLoadingBar.setValue(progress)

    @QtCore.pyqtSlot(int, int, str)
    def set_word_freq(self, cid: int, freq: int, freq_note: str):
        r = self.data.get(cid)
        r.freq = freq
        if freq >= self.CARD_RD_THRESHOLD:
            r.cards = "RD"
        else:
            r.cards = "R"
        r.freq_note = freq_note
        if self.cur_cid() == cid:
            self.editor_load_entry(self.cur_cid())

    @QtCore.pyqtSlot(int, str)
    def handle_collins_suggestion(self, cid: int, suggestion: str):
        self.data.get(cid).suggestion = suggestion
        if self.cur_cid() == cid:
            self.editor_load_entry(self.cur_cid())

    # ================================ Data Manager Related Slots ================================

    @QtCore.pyqtSlot(int, bool)
    def handle_record_insertion(self, cid: int, batch_loading: bool):
        subject = self.data.get(cid).subject

        self.entryList.selectionModel().blockSignals(True)  # --------- entryList signals blocked -------->

        if batch_loading:
            row = self.entryList.count()
        else:
            row = self.entryList.currentRow() + 1  # add item after current row
        self.entryList.insertItem(row, subject)

        item = self.entryList.item(row)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, cid)
        self.cid_to_item[cid] = item

        self.entryList.selectionModel().blockSignals(False)  # <-------- entryList signals unblocked --------

        if not batch_loading:
            self.entryList.setCurrentRow(row)  # will trigger editor_load_entry()
            self.subject.setFocus()
        else:
            self.wqv.prefetch_queued(subject, QueryType.COLLINS, cid)

    @QtCore.pyqtSlot()
    def update_ui_after_record_count_changed(self):
        if self.data.count() > 0:
            self.set_gui_enabled(True)
            self.freqBar.setMaximum(5)
        else:
            self.editor_block_signals(True)  # --------- editor signals blocked -------->
            self.subject.document().setPlainText("Congratulation!")  # subject change will lead to opening of dictionary
            self.paraphrase.document().setPlainText("There is nothing to be processed.")
            self.extension.document().setPlainText("Great work!")
            self.example.document().setPlainText("")
            self.source.document().setPlainText("")
            self.hint.document().setPlainText("")
            self.freqBar.setMaximum(0)
            self.editor_block_signals(False)  # <-------- editor signals unblocked --------
            self.set_gui_enabled(False)

        self.unreadBar.setMaximum(self.data.count())
        self.unreadBar.setValue(self.data.count(RecordStatus.UNVIEWED) + self.data.count(RecordStatus.TOPROCESS))
        self.unreadBar.setToolTip("%d unread" % self.unreadBar.value())
        self.confirmedBar.setMaximum(self.data.count())
        self.confirmedBar.setValue(self.data.count(RecordStatus.CONFIRMED))
        self.confirmedBar.setToolTip("%d confirmed" % self.confirmedBar.value())
        self.discardBar.setMaximum(self.data.count())
        self.discardBar.setValue(self.data.count(RecordStatus.DISCARDED))
        self.discardBar.setToolTip("%d discarded" % self.discardBar.value())

    @QtCore.pyqtSlot()
    def handle_record_batch_load_finished(self):
        if self.data.count() > 0:
            QtCore.QCoreApplication.processEvents()
            self.entryList.setCurrentRow(0)
            self.paraphrase.setFocus()

    @QtCore.pyqtSlot()
    def handle_record_clear(self):
        self.wqv.reset()
        self.entryList.selectionModel().blockSignals(True)  # --------- entryList signals blocked -------->
        self.cid_to_item.clear()
        self.entryList.clear()
        QtCore.QCoreApplication.processEvents()
        self.entryList.selectionModel().blockSignals(False)  # <-------- entryList signals unblocked --------

    @QtCore.pyqtSlot(int, RecordStatus, RecordStatus)
    def handle_record_status_changed(self, cid: int, old_status: RecordStatus, new_status: RecordStatus):
        f = self.entryList.font()
        if new_status == RecordStatus.CONFIRMED:
            f.setItalic(True)
            f.setStrikeOut(False)
            self.wqv.discard_by_cid(cid)
        elif new_status == RecordStatus.DISCARDED:
            f.setItalic(False)
            f.setStrikeOut(True)
            self.wqv.discard_by_cid(cid)
        else:
            f.setItalic(False)
            f.setStrikeOut(False)
        self.cid_to_item[cid].setFont(f)

    # ================================ Data Related Helper Functions ================================

    def cur_cid(self) -> Optional[int]:
        item = self.entryList.currentItem()
        if item is None:
            return None
        else:
            return item.data(QtCore.Qt.ItemDataRole.UserRole)

    def cur_record(self) -> Optional[Record]:
        cid = self.cur_cid()
        if cid is None:
            return None
        else:
            return self.data.get(cid)

    # ================================ UI Helper Functions ================================

    def editor_load_entry(self, cid: int) -> None:
        r = self.data.get(cid)

        self.editor_block_signals(True)  # -------- main editor signals blocked -------->

        self.subject.document().setPlainText(r.subject)
        if r.pronunciation == "Samantha" or r.pronunciation == "Anna":
            self.pronA.toggle()  # only change UI display but not triggering pronunciation
        elif r.pronunciation == "Daniel" or r.pronunciation == "Markus":
            self.pronB.toggle()  # only change UI display but not triggering pronunciation
        self.freqBar.setValue(r.freq)
        self.freqBar.setToolTip(r.freq_note)
        self.checkR.setChecked("R" in r.cards)
        self.checkS.setChecked("S" in r.cards)
        self.checkD.setChecked("D" in r.cards)
        self.paraphrase.document().setHtml(r.paraphrase)
        self.extension.document().setHtml(r.extension)
        self.example.document().setHtml(r.example)
        self.checkSource.setChecked(r.source_enabled)
        self.source.setEnabled(r.source_enabled)
        self.source.document().setHtml(r.source)
        self.hint.document().setPlainText(r.hint)
        if r.image is not None:
            self.imageLabel.setPixmap(r.image)
        else:
            self.imageLabel.setText("Click to\npaste\nimage")
        if r.suggestion is not None:
            self.subjectSuggest.setText("Suggest: " + r.suggestion)
            self.subjectSuggest.setVisible(True)
        else:
            self.subjectSuggest.setVisible(False)

        self.editor_block_signals(False)  # <-------- main editor signals unblocked --------

    def move_to_next(self) -> None:
        # Discard by cid will be performed by record_status_changed signal
        if self.entryList.currentRow() < self.entryList.count() - 1:
            self.entryList.selectionModel().blockSignals(True)  # --------- entryList signals blocked -------->
            self.entryList.setCurrentRow(self.entryList.currentRow() + 1)
            self.selected_changed(query_immediately=False)  # delay query
            self.entryList.selectionModel().blockSignals(False)  # <-------- entryList signals unblocked --------
        else:
            self.add_new_entry_clicked()

    def set_gui_enabled(self, value: bool) -> None:
        for component in [self.confirmButton, self.discardButton] + self.editor_components:
            component.setEnabled(value)

    def editor_block_signals(self, value: bool) -> None:
        for component in self.editor_components:
            component.blockSignals(value)

    # ================================ UI Slots and Event Handler ================================

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key.Key_Return or key == QtCore.Qt.Key.Key_Enter:
                if (widget is self.subject) or (widget is self.paraphrase and self.paraphrase.toPlainText() == ""):
                    self.data.set_status(self.cur_cid(), RecordStatus.UNVIEWED)
                    self.selected_changed(query_immediately=True)
                    return True  # discard the return key
            elif key == QtCore.Qt.Key.Key_B and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:  # Ctrl + B
                if widget in [self.paraphrase, self.extension, self.example, self.source]:
                    widget: QtWidgets.QTextEdit
                    cursor = widget.textCursor()
                    fmt = cursor.charFormat()
                    if fmt.fontWeight() == QtGui.QFont.Weight.Bold:
                        fmt.setFontWeight(QtGui.QFont.Weight.Normal)
                    else:
                        fmt.setFontWeight(QtGui.QFont.Weight.Bold)
                    cursor.mergeCharFormat(fmt)
            elif key == QtCore.Qt.Key.Key_I and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:  # Ctrl + I
                if widget in [self.paraphrase, self.extension, self.example, self.source]:
                    widget: QtWidgets.QTextEdit
                    cursor = widget.textCursor()
                    fmt = cursor.charFormat()
                    fmt.setFontItalic(not fmt.fontItalic())
                    cursor.mergeCharFormat(fmt)

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    @QtCore.pyqtSlot()
    def change_to_english_mode(self):
        global THINGS_VOCAB_LIST
        THINGS_VOCAB_LIST = "English Quick List"
        self.pronA.setText("Samantha")
        self.pronB.setText("Daniel")
        QuerySettings["CollinsDirectory"] = "english"
        QuerySettings["TranslateFrom"] = "en"
        QuerySettings["TranslateTo"] = "zh-CN"

    @QtCore.pyqtSlot()
    def change_to_deutsch_mode(self):
        global THINGS_VOCAB_LIST
        THINGS_VOCAB_LIST = "Deutsch schnell Liste"
        self.pronA.setText("Anna")
        self.pronB.setText("Markus")
        QuerySettings["CollinsDirectory"] = "german-english"
        QuerySettings["TranslateFrom"] = "de"
        QuerySettings["TranslateTo"] = "en"

    @QtCore.pyqtSlot()
    def confirm_clicked(self):
        self.data.set_status(self.cur_cid(), RecordStatus.CONFIRMED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def discard_clicked(self):
        self.data.set_status(self.cur_cid(), RecordStatus.DISCARDED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def selected_changed(self, query_immediately: bool = True):
        self.editor_load_entry(self.cur_cid())
        r = self.cur_record()
        if r.subject != "":
            if r.status == RecordStatus.UNVIEWED:
                self.pronA.click()  # including toggling and first-time pronouncing
                self.data.set_status(self.cur_cid(), RecordStatus.TOPROCESS)
            if query_immediately or self.wqv.has_prefetched(r.subject, QueryType.COLLINS, r.cid):
                self.wqv.request(r.subject, QueryType.COLLINS, r.cid)
            else:
                self.wqv.delay_request(r.subject, QueryType.COLLINS, r.cid)

    @QtCore.pyqtSlot()
    def pron_clicked(self):
        sender: QtWidgets.QRadioButton = cast(QtWidgets.QRadioButton, self.sender())
        self.data.pronounce(self.cur_record().subject, sender.text())
        self.cur_record().pronunciation = sender.text()

    @QtCore.pyqtSlot()
    def subject_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)

        # No need to discard wqv queries as all queries associated with the cid will be discarded at once later
        subject = self.subject.toPlainText()
        r.subject = subject
        self.entryList.currentItem().setText(subject)
        # Do not query automatically. Wait for Return key.

    @QtCore.pyqtSlot()
    def suggest_clicked(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)

        suggestion = r.suggestion
        self.subject.setPlainText(suggestion)  # will trigger subject_changed
        self.subjectSuggest.setVisible(False)

        # wqv COLLINS query is correct as the suggestion comes from its URL
        # New GOOGLE_IMAGE query will be issued as paraphrase changes

    @QtCore.pyqtSlot()
    def paraphrase_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)

        r.paraphrase = self.paraphrase.toHtml()
        if self.englishMode.isChecked():
            # Trigger GOOGLE_IMAGE prefetch when paraphrase changes
            self.wqv.prefetch_immediately(r.subject, QueryType.GOOGLE_IMAGE, r.cid)

    @QtCore.pyqtSlot()
    def extension_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        r.extension = self.extension.toHtml()

    @QtCore.pyqtSlot()
    def example_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        r.example = self.example.toHtml()

    @QtCore.pyqtSlot()
    def source_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        r.source = self.source.toHtml()

    @QtCore.pyqtSlot()
    def source_check_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        self.source.setEnabled(self.checkSource.isChecked())
        r.source_enabled = self.checkSource.isChecked()
        self.source.setHtml('<div align="right">' + self.source.toHtml() + '</div>')  # triggers source_changed signal

    @QtCore.pyqtSlot()
    def hint_changed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        r.hint = self.hint.toPlainText()

    @QtCore.pyqtSlot()
    def image_clicked(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            mine_data = app.clipboard().mimeData()
            if mine_data.hasImage():
                r = self.cur_record()
                if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
                    self.data.set_status(r.cid, RecordStatus.TOPROCESS)
                px = QtGui.QPixmap(mine_data.imageData()).scaledToHeight(self.imageLabel.height(),
                                                                         mode=QtCore.Qt.TransformationMode.SmoothTransformation)
                r.image = px
                self.imageLabel.setPixmap(px)
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self.query_google_images_clicked()

    @QtCore.pyqtSlot()
    def image_double_clicked(self, event):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        r.image = None
        self.imageLabel.setText("Click \nto paste \nimage")

    @QtCore.pyqtSlot()
    def load_kindle_clicked(self) -> None:
        if not self.data.reload_kindle_data(KINDLE_DB_FILENAME):
            self.report_error("Failed to find Kindle DB file. Please make sure Kindle has connected.")

    @QtCore.pyqtSlot()
    def load_csv_clicked(self) -> None:
        # options = QtWidgets.QFileDialog.Options
        # options |= QtWidgets.QFileDialog.Options.DontUseNativeDialog
        csv_file, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            "Select the CSV file",
                                                            CSV_DEFAULT_DIRECTORY,
                                                            "CSV Files (*.csv);;All Files (*)")
        if csv_file:
            if not self.data.reload_csv_data(csv_file):
                self.report_error("Failed to load CSV file.")

    @QtCore.pyqtSlot()
    def load_things_clicked(self) -> None:
        self.data.reload_things_list(THINGS_VOCAB_LIST)

    @staticmethod
    def report_error(info: str) -> None:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText(info)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

    @QtCore.pyqtSlot()
    def confirm_and_smart_duplicate_entry(self):
        self.data.set_status(self.cur_cid(), RecordStatus.CONFIRMED)
        self.smart_duplicate_entry()

    @QtCore.pyqtSlot()
    def smart_duplicate_entry(self):
        cursor = self.example.textCursor()
        selection = cursor.selectedText()
        r = self.cur_record()
        self.data.add_new_single_entry(selection,
                                       self.example.toPlainText().replace(selection, '<b>%s</b>' % selection),
                                       r.source_enabled,
                                       r.source)

    @QtCore.pyqtSlot()
    def add_new_entry_clicked(self):
        self.data.add_new_single_entry()

    @QtCore.pyqtSlot()
    def clear_list_clicked(self):
        self.data.clear()

    @QtCore.pyqtSlot()
    def card_type_changed(self):
        self.cur_record().cards = "%s%s%s" % ("R" if self.checkR.isChecked() else "",
                                              "S" if self.checkS.isChecked() else "",
                                              "D" if self.checkD.isChecked() else "")

    @QtCore.pyqtSlot()
    def query_collins_clicked(self):
        self.wqv.request(self.cur_record().subject, QueryType.COLLINS, self.cur_cid())

    @QtCore.pyqtSlot()
    def query_google_images_clicked(self):
        self.wqv.request(self.cur_record().subject, QueryType.GOOGLE_IMAGE, self.cur_cid())

    @QtCore.pyqtSlot()
    def query_google_translate_clicked(self):
        self.wqv.request(self.cur_record().subject, QueryType.GOOGLE_TRANSLATE, self.cur_cid())

    @QtCore.pyqtSlot()
    def query_google_clicked(self):
        self.wqv.request(self.cur_record().subject, QueryType.GOOGLE, self.cur_cid())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    mapleUtility = MapleUtility()
    mapleUtility.showMaximized()

    sys.exit(app.exec())
