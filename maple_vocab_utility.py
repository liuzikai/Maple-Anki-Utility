# -*- coding: utf-8 -*-

# To compile pyqt: pyuic5 maple_utility.ui > maple_utility.py

import sys
import os
from typing import Optional, Dict, cast
from PyQt6 import QtCore, QtWidgets, QtGui
from data_manager import DataManager, Record, RecordStatus
from maple_utility import Ui_MapleUtility
from web_query_view import WebQueryView, QueryType, QuerySettings
import config
import webbrowser

# KINDLE_DB_FILENAME = "resource/test_vocab.db"
KINDLE_DB_FILENAME = "/Volumes/Kindle/system/vocabulary/vocab.db"


class MapleUtility(QtWidgets.QMainWindow, Ui_MapleUtility):
    """MapleVocabUtility MainWindow."""

    BASIC_CARDS = "R"
    MORE_CARDS_THRESHOLD_EN = 4
    MORE_CARDS_EN = "RD"
    MORE_CARDS_THRESHOLD_DE = 5
    MORE_CARDS_DE = "RS"

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
        self.subjectSuggest.clicked.connect(self.subject_suggest_clicked)
        self.cardTypeSuggest.setVisible(False)
        self.cardTypeSuggest.clicked.connect(self.card_type_suggest_clicked)
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
        self.confirmButton.setToolTip("Shortcut: Cmd + Return\nConfirm and smart duplicate: Cmd + Shift + Return")
        self.discard_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+Return"), self)
        self.discard_shortcut.activated.connect(self.discard_clicked)
        self.discardButton.setToolTip("Shortcut: Cmd + Opt + Return")
        self.new_entry_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.new_entry_shortcut.activated.connect(self.add_new_entry_clicked)
        self.smart_duplicate_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+N"), self)
        self.smart_duplicate_shortcut.activated.connect(self.smart_duplicate_entry)
        self.newEntry.setToolTip("Shortcut: Cmd + N\nSmart Duplicate: Cmd + Shift + N")
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
        self.kindleToThings.setVisible(False)
        self.kindleToThings.clicked.connect(self.kindle_to_things_clicked)
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

        # Create the menu bar
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("Settings")

        # Add "Settings..." item to the menu
        settings_action = QtGui.QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(settings_action)

        # Create the Help menu
        help_menu = menu_bar.addMenu("Help")

        # Add "User Manual" item to the Help menu
        help_action = QtGui.QAction("User Manual...", self)
        help_action.triggered.connect(lambda: webbrowser.open('https://github.com/liuzikai/Maple-Anki-Utility/blob/main/resource/user-manual.md'))
        help_menu.addAction(help_action)

        # Add "Visit GitHub Page" item to the Help menu
        help_action = QtGui.QAction("Visit GitHub Page...", self)
        help_action.triggered.connect(lambda: webbrowser.open('https://github.com/liuzikai/Maple-Anki-Utility'))
        help_menu.addAction(help_action)

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
        self.data = DataManager(config.save_dir, os.path.join(config.anki_user_dir, "collection.media"))
        self.data.record_inserted.connect(self.handle_record_insertion)  # cid, batch_loading(True) / add_single(False)
        self.data.record_status_changed.connect(self.handle_record_status_changed)  # cid, old_status, new_status
        self.data.record_cleared.connect(self.handle_record_clear)
        self.data.record_count_changed.connect(self.update_ui_after_record_count_changed)
        self.data.batch_load_finished.connect(self.handle_record_batch_load_finished)

        # QListWidgetItem can only be deleted when records are cleared
        self.cid_to_item: Dict[int, QtWidgets.QListWidgetItem] = {}

        # Setup initial UI
        self.change_to_english_mode()
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
        r.freq_note = freq_note
        if self.cur_cid() == cid:
            self.editor_load_entry(self.cur_cid())

    @QtCore.pyqtSlot(int, str)
    def handle_collins_suggestion(self, cid: int, suggestion: str):
        subject = self.data.get(cid).subject
        if self.deutschMode.isChecked():
            subject = self.deutsch_mode_preprocess_subject(subject)

        # Space will be replace by '-' in url, but there are cases that subject itself contains '-'
        subject_with_dashes = subject.replace(' ', '-')
        if suggestion == subject_with_dashes:
            return

        if self.deutschMode.isChecked():
            if i := suggestion.find('_') != -1:
                suggestion = suggestion[:i]
            if suggestion.lower() == subject_with_dashes.lower():
                return

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

    @QtCore.pyqtSlot(bool)
    def handle_record_batch_load_finished(self, is_kindle_db: bool):
        if self.data.count() > 0:
            QtCore.QCoreApplication.processEvents()
            self.entryList.setCurrentRow(0)
            self.paraphrase.setFocus()
        self.kindleToThings.setVisible(is_kindle_db)

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
            r = self.data.get(cid)
            if r.pronunciation == "Unknown":
                if self.englishMode.isChecked():
                    r.pronunciation = config.en_voice_1
                elif self.deutschMode.isChecked():
                    r.pronunciation = config.de_voice_1
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

        if r.pronunciation == config.en_voice_1 or r.pronunciation == config.de_voice_1:
            self.pronA.toggle()  # only change UI display but not triggering pronunciation
        elif r.pronunciation == config.en_voice_2 or r.pronunciation == config.de_voice_2:
            self.pronB.toggle()  # only change UI display but not triggering pronunciation

        self.freqBar.setValue(r.freq)
        self.freqBar.setToolTip(r.freq_note)
        self.checkR.setChecked("R" in r.cards)
        self.checkS.setChecked("S" in r.cards)
        self.checkD.setChecked("D" in r.cards)

        if self.englishMode.isChecked() and r.freq >= self.MORE_CARDS_THRESHOLD_EN:
            suggested_cards = self.MORE_CARDS_EN
        elif self.deutschMode.isChecked() and r.freq >= self.MORE_CARDS_THRESHOLD_DE:
            suggested_cards = self.MORE_CARDS_DE
        else:
            suggested_cards = self.BASIC_CARDS
        if r.cards != suggested_cards:
            self.cardTypeSuggest.setText(suggested_cards + "?")
            self.cardTypeSuggest.setVisible(True)
        else:
            self.cardTypeSuggest.setVisible(False)

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
            self.subjectSuggest.setText(r.suggestion + "?")
            self.subjectSuggest.setVisible(True)
        else:
            self.subjectSuggest.setVisible(False)

        self.editor_block_signals(False)  # <-------- main editor signals unblocked --------

    def move_to_next(self) -> None:
        # Discard by cid will be performed by record_status_changed signal
        if self.entryList.currentRow() < self.entryList.count() - 1:
            self.entryList.selectionModel().blockSignals(True)  # --------- entryList signals blocked -------->
            self.entryList.setCurrentRow(self.entryList.currentRow() + 1)
            self.selected_changed(manually_requested_query=False, query_immediately=False)  # delay query
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

    def show_settings_dialog(self):
        # Create and show the ConfigWindow
        config_window = config.ConfigWindow(self)
        config_window.finished.connect(self.set_pronunciation_captions)
        config_window.show()

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key.Key_Return or key == QtCore.Qt.Key.Key_Enter:
                if (widget is self.subject) or (widget is self.paraphrase and self.paraphrase.toPlainText() == ""):
                    self.data.set_status(self.cur_cid(), RecordStatus.UNVIEWED)
                    self.selected_changed(manually_requested_query=True, query_immediately=True)
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
    def set_pronunciation_captions(self):
        if self.englishMode.isChecked():
            self.pronA.setText(config.en_voice_1)
            self.pronB.setText(config.en_voice_2)
        elif self.deutschMode.isChecked():
            self.pronA.setText(config.de_voice_1)
            self.pronB.setText(config.de_voice_2)
    @QtCore.pyqtSlot()
    def change_to_english_mode(self):
        self.set_pronunciation_captions()
        QuerySettings["CollinsDirectory"] = "english"
        QuerySettings["TranslateFrom"] = "en"
        QuerySettings["TranslateTo"] = "zh-CN"
        QuerySettings["PreprocessSubject"] = None
        self.data.clear()

    @staticmethod
    def deutsch_mode_preprocess_subject(s: str) -> str:
        s = s.replace('ä', 'a').replace('Ä', 'A') \
            .replace('ü', 'u').replace('Ü', 'U') \
            .replace('ö', 'o').replace('Ö', 'O') \
            .replace('ê', 'e').replace('Ê', 'E') \
            .replace('ß', "ss")
        if s.startswith("der ") or s.startswith("die ") or s.startswith("das "):
            s = s[4:]
        return s

    @QtCore.pyqtSlot()
    def change_to_deutsch_mode(self):
        self.set_pronunciation_captions()
        QuerySettings["CollinsDirectory"] = "german-english"
        QuerySettings["TranslateFrom"] = "de"
        QuerySettings["TranslateTo"] = "en"
        QuerySettings["PreprocessSubject"] = self.deutsch_mode_preprocess_subject
        self.data.clear()

    @QtCore.pyqtSlot()
    def confirm_clicked(self):
        self.data.set_status(self.cur_cid(), RecordStatus.CONFIRMED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def discard_clicked(self):
        self.data.set_status(self.cur_cid(), RecordStatus.DISCARDED)
        self.move_to_next()

    @QtCore.pyqtSlot()
    def selected_changed(self, manually_requested_query: bool = False, query_immediately: bool = True):
        self.editor_load_entry(self.cur_cid())
        r = self.cur_record()
        if r.subject != "":
            if r.status == RecordStatus.UNVIEWED:
                self.pronA.click()  # including toggling and first-time pronouncing
                self.data.set_status(self.cur_cid(), RecordStatus.TOPROCESS)
            if manually_requested_query or self.autoQueryCheck.isChecked():
                if query_immediately or self.wqv.has_prefetched(r.subject, QueryType.COLLINS, r.cid):
                    self.wqv.request(r.subject, QueryType.COLLINS, r.cid)
                elif self.autoQueryCheck.isChecked():
                    self.wqv.delay_request(r.subject, QueryType.COLLINS, r.cid)

    def get_cur_record_and_revert_save_if_needed(self):
        r = self.cur_record()
        if r.status in [RecordStatus.CONFIRMED, RecordStatus.DISCARDED]:
            self.data.set_status(r.cid, RecordStatus.TOPROCESS)
        return r

    @QtCore.pyqtSlot()
    def pron_clicked(self):
        sender: QtWidgets.QRadioButton = cast(QtWidgets.QRadioButton, self.sender())
        self.data.pronounce(self.cur_record().subject, sender.text())
        r = self.get_cur_record_and_revert_save_if_needed()
        r.pronunciation = sender.text()

    @QtCore.pyqtSlot()
    def subject_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()

        # No need to discard wqv queries as all queries associated with the cid will be discarded at once later
        subject = self.subject.toPlainText()
        r.subject = subject
        self.entryList.currentItem().setText(subject)
        # Do not query automatically. Wait for Return key.

    @QtCore.pyqtSlot()
    def subject_suggest_clicked(self):
        r = self.get_cur_record_and_revert_save_if_needed()

        suggestion = r.suggestion
        self.subject.setPlainText(suggestion)  # will trigger subject_changed
        self.subjectSuggest.setVisible(False)

        # wqv COLLINS query is correct as the suggestion comes from its URL
        # New GOOGLE_IMAGE query will be issued as paraphrase changes

    @QtCore.pyqtSlot()
    def card_type_suggest_clicked(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.cards = self.cardTypeSuggest.text()[:-1]
        self.editor_load_entry(r.cid)

    @QtCore.pyqtSlot()
    def paraphrase_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()

        r.paraphrase = self.paraphrase.toHtml()
        if self.autoQueryCheck.isChecked() and self.englishMode.isChecked():
            # Trigger GOOGLE_IMAGE prefetch when paraphrase changes
            self.wqv.prefetch_immediately(r.subject, QueryType.GOOGLE_IMAGE, r.cid)

    @QtCore.pyqtSlot()
    def extension_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.extension = self.extension.toHtml()

    @QtCore.pyqtSlot()
    def example_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.example = self.example.toHtml()

    @QtCore.pyqtSlot()
    def source_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.source = self.source.toHtml()

    @QtCore.pyqtSlot()
    def source_check_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        self.source.setEnabled(self.checkSource.isChecked())
        r.source_enabled = self.checkSource.isChecked()
        self.source.setHtml('<div align="right">' + self.source.toHtml() + '</div>')  # triggers source_changed signal

    @QtCore.pyqtSlot()
    def hint_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.hint = self.hint.toPlainText()

    @QtCore.pyqtSlot()
    def image_clicked(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            mine_data = app.clipboard().mimeData()
            if mine_data.hasImage():
                r = self.get_cur_record_and_revert_save_if_needed()
                px = QtGui.QPixmap(mine_data.imageData()).scaledToHeight(self.imageLabel.height(),
                                                                         mode=QtCore.Qt.TransformationMode.SmoothTransformation)
                r.image = px
                self.imageLabel.setPixmap(px)
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self.query_google_images_clicked()

    @QtCore.pyqtSlot()
    def image_double_clicked(self, event):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.image = None
        self.imageLabel.setText("Click \nto paste \nimage")

    @QtCore.pyqtSlot()
    def load_kindle_clicked(self) -> None:
        try:
            self.data.reload_kindle_data(KINDLE_DB_FILENAME)
        except RuntimeError as e:
            self.report_error(str(e))

    @QtCore.pyqtSlot()
    def load_csv_clicked(self) -> None:
        # options = QtWidgets.QFileDialog.Options
        # options |= QtWidgets.QFileDialog.Options.DontUseNativeDialog
        csv_file, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            "Select the CSV file",
                                                            config.csv_default_dir,
                                                            "CSV Files (*.csv);;All Files (*)")
        if csv_file:
            try:
                self.data.reload_csv_data(csv_file)
                csv_dir = os.path.dirname(csv_file)
                if csv_dir != config.csv_default_dir:
                    config.csv_default_dir = csv_dir
                    config.save_config_from_variables()
            except RuntimeError as e:
                self.report_error(str(e))

    @QtCore.pyqtSlot()
    def load_things_clicked(self) -> None:
        things_list = config.things_vocab_list_en if self.englishMode.isChecked() else config.things_vocab_list_de
        try:
            self.data.reload_things_list(things_list)
        except RuntimeError as e:
            self.report_error(str(e))

    @staticmethod
    def report_error(info: str) -> None:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText(info)
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg_box.exec()

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
    def kindle_to_things_clicked(self):
        things_list = config.things_vocab_list_en if self.englishMode.isChecked() else config.things_vocab_list_de
        self.data.transfer_all_unsaved_to_things(things_list)

    @QtCore.pyqtSlot()
    def card_type_changed(self):
        r = self.get_cur_record_and_revert_save_if_needed()
        r.cards = "%s%s%s" % ("R" if self.checkR.isChecked() else "",
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
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    # app.setWindowIcon(QtGui.QIcon(script_dir + os.path.sep + 'resource/1024.png'))

    if config.load_config(app):
        mapleUtility = MapleUtility()
        mapleUtility.showMaximized()

        sys.exit(app.exec())
