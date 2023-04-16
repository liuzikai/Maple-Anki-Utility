import sys
import os
import configparser
import appdirs
from PyQt6 import QtCore, QtWidgets, QtGui
import subprocess
from functools import partial
import bundle_files

anki_user_dir = None
save_dir = None
csv_default_dir = ""
things_vocab_list_en = None
things_vocab_list_de = None
en_voice_1 = None
en_voice_2 = None
de_voice_1 = None
de_voice_2 = None

# ConfigParser setup
config_dir = appdirs.user_config_dir("MapleVocabUtility")
config_file = os.path.join(config_dir, 'config.ini')
print(f'Using config file "{config_file}"')
parser = configparser.ConfigParser()


def save_config_from_variables():
    parser.set('DEFAULT', 'anki_user_dir', anki_user_dir)
    parser.set('DEFAULT', 'save_dir', save_dir)
    parser.set('DEFAULT', 'csv_default_dir', csv_default_dir)
    parser.set('DEFAULT', 'things_vocab_list_en', things_vocab_list_en)
    parser.set('DEFAULT', 'things_vocab_list_de', things_vocab_list_de)
    parser.set('DEFAULT', 'en_voice_1', en_voice_1)
    parser.set('DEFAULT', 'en_voice_2', en_voice_2)
    parser.set('DEFAULT', 'de_voice_1', de_voice_1)
    parser.set('DEFAULT', 'de_voice_2', de_voice_2)
    os.makedirs(config_dir, exist_ok=True)
    with open(config_file, 'w') as f:
        parser.write(f)


def is_config_valid() -> bool:
    global anki_user_dir, save_dir
    if anki_user_dir is None or not os.path.exists(anki_user_dir):
        return False
    if save_dir is None or not os.path.exists(save_dir):
        return False
    return True


def load_config(app) -> bool:
    global anki_user_dir, save_dir, csv_default_dir, things_vocab_list_en, things_vocab_list_de
    global en_voice_1, en_voice_2, de_voice_1, de_voice_2

    config_exists = os.path.exists(config_file)

    parser.read(config_file)

    anki_user_dir = parser.get('DEFAULT', 'anki_user_dir', fallback=None)
    save_dir = parser.get('DEFAULT', 'save_dir', fallback=os.path.join(os.path.expanduser("~"), "Desktop"))
    csv_default_dir = parser.get('DEFAULT', 'csv_default_dir', fallback="")
    things_vocab_list_en = parser.get('DEFAULT', 'things_vocab_list_en', fallback="English Quick List")
    things_vocab_list_de = parser.get('DEFAULT', 'things_vocab_list_de', fallback="Deutsch schnell Liste")
    en_voice_1 = parser.get('DEFAULT', 'en_voice_1', fallback="Samantha")
    en_voice_2 = parser.get('DEFAULT', 'en_voice_2', fallback="Daniel")
    de_voice_1 = parser.get('DEFAULT', 'de_voice_1', fallback="Anna")
    de_voice_2 = parser.get('DEFAULT', 'de_voice_2', fallback="Markus")

    if not config_exists or not is_config_valid():
        if anki_user_dir is None or not os.path.exists(anki_user_dir):
            anki_user_dir = "PLEASE SELECT YOUR ANKI USER DIRECTORY"
        config_window = ConfigWindow(app, initial_setup=True)
        config_window.show()
        app.exec()

    return is_config_valid()  # user may cancel


class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, app, initial_setup=False):
        super().__init__()
        self.app = app
        self.initial_setup = initial_setup

        self.anki_user_dir_valid = False
        self.save_dir_valid = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Preferences')

        self.setMinimumWidth(800)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowMinMaxButtonsHint)

        layout = QtWidgets.QGridLayout(self)

        self.line_edits = {}
        self.select_buttons = {}

        def create_directory_row(row, option_name, label_text):
            label = QtWidgets.QLabel(label_text)
            line_edit = QtWidgets.QLineEdit()
            button = QtWidgets.QPushButton('Select...')

            layout.addWidget(label, row, 0)
            layout.addWidget(line_edit, row, 1)
            layout.addWidget(button, row, 2)

            self.line_edits[option_name] = line_edit
            self.select_buttons[option_name] = button

            return line_edit, button

        # Anki User Directory row
        anki_user_dir_edit, anki_user_dir_button = create_directory_row(
            0, 'anki_user_dir', 'Anki User Directory (Named With Your Anki Username)')
        anki_user_dir_edit.textChanged.connect(self.check_anki_user_dir)
        anki_user_dir_button.clicked.connect(
            lambda: self.select_directory('anki_user_dir', "Select Anki User Directory (Your Anki Username)",
                                          os.path.join(appdirs.user_data_dir(), "Anki2")))

        # Save Directory row
        save_dir_edit, save_dir_button = create_directory_row(
            1, 'save_dir', 'Save Directory')
        save_dir_edit.textChanged.connect(self.check_save_dir)
        save_dir_button.clicked.connect(
            lambda: self.select_directory('save_dir', "Select a Directory to Save",
                                          save_dir_edit.text()))

        # Things 3 Project (EN) row
        things3_list_en_label = QtWidgets.QLabel('Things 3 Vocabulary List (EN)')
        things3_list_en_edit = QtWidgets.QLineEdit()
        layout.addWidget(things3_list_en_label, 2, 0)
        layout.addWidget(things3_list_en_edit, 2, 1)
        self.line_edits['things3_list_en'] = things3_list_en_edit

        # Thing 3 Project (DE) row
        things3_list_de_label = QtWidgets.QLabel('Things 3 Vocabulary List (DE)')
        things3_list_de_edit = QtWidgets.QLineEdit()
        layout.addWidget(things3_list_de_label, 3, 0)
        layout.addWidget(things3_list_de_edit, 3, 1)
        self.line_edits['things3_list_de'] = things3_list_de_edit

        # Vertical spacer
        spacer = QtWidgets.QSpacerItem(0, 16, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addItem(spacer, 5, 0, 1, 3)

        # Voice Setting GroupBox
        voice_setting_group = QtWidgets.QGroupBox("Voice Settings")
        voice_setting_layout = QtWidgets.QGridLayout()

        # Create a QHBoxLayout for help_label and help_button
        help_layout = QtWidgets.QHBoxLayout()

        self.help_label = QtWidgets.QLabel("Install more voices in macOS System Settings")
        self.help_button = QtWidgets.QPushButton("?")
        self.help_button.setFixedSize(30, 30)
        self.help_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: blue;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: darkblue;
            }
        """)
        self.help_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("https://github.com/liuzikai/Maple-Anki-Utility/blob/main/resource/user-manual.md#add-voices")))

        help_layout.addWidget(self.help_label)
        help_layout.addWidget(self.help_button)

        # Add a spacer to expand the layout
        help_layout.addStretch()

        # Add the help_layout to the voice_setting_layout
        voice_setting_layout.addLayout(help_layout, 0, 0, 1, 8)

        self.voice_labels = ["EN Voice 1", "EN Voice 2", "DE Voice 1", "DE Voice 2"]
        self.voice_dropdowns = []
        self.voice_test_buttons = []

        for i, label_text in enumerate(self.voice_labels):
            label = QtWidgets.QLabel(label_text)
            dropdown = QtWidgets.QComboBox()
            self.voice_dropdowns.append(dropdown)
            test_button = QtWidgets.QPushButton("Test")
            self.voice_test_buttons.append(test_button)

            row, col = divmod(i, 2)
            voice_setting_layout.addWidget(label, row + 1, col * 4)
            voice_setting_layout.addWidget(dropdown, row + 1, col * 4 + 1)
            voice_setting_layout.addWidget(test_button, row + 1, col * 4 + 2)

            if col == 0:
                spacer = QtWidgets.QSpacerItem(30, 0, QtWidgets.QSizePolicy.Policy.Fixed,
                                               QtWidgets.QSizePolicy.Policy.Fixed)
                voice_setting_layout.addItem(spacer, row + 1, 3)

        self.populate_voice_comboboxes()
        self.connect_test_buttons()

        voice_setting_group.setLayout(voice_setting_layout)
        layout.addWidget(voice_setting_group, 6, 0, 1, 3)

        # Create Save and Cancel buttons
        self.save_button = QtWidgets.QPushButton('Save')
        self.cancel_button = QtWidgets.QPushButton('Cancel')

        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout, 7, 1, 1, 2)

        self.load_ui_from_variables()

    def populate_voice_comboboxes(self):
        p = subprocess.Popen(f'"{bundle_files.lame_filename}" --version', shell=True, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)
        exit_code = p.wait()
        if exit_code != 0:
            self.help_label.setText("Please install lame (for example, with Homebrew, run 'brew install lame'), "
                                    "or the pronunciation functionality will not work.")
            self.help_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl("https://github.com/liuzikai/Maple-Anki-Utility#getting-started")))
            self.disable_voice_settings()
            return

        p = subprocess.Popen("say -v '?'", shell=True, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)
        voices_output, _ = p.communicate()
        exit_code = p.wait()
        if exit_code != 0:
            self.help_label.setText("Failed to run 'say -v \"?\"'. Pronunciation functionality will not work.")
            self.help_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl("https://github.com/liuzikai/Maple-Anki-Utility#getting-started")))
            self.disable_voice_settings()
            return

        lines = voices_output.split("\n")
        for line in lines:
            if not line:
                continue
            voice_language, sample = line.split("# ", 1)
            voice_language = voice_language.rstrip()

            if any(lang in voice_language for lang in ["en_US", "en_GB", "de_DE"]):
                voice, language = voice_language.rsplit(" ", 1)
                voice = voice.rstrip()

                if language in ["en_US", "en_GB"]:
                    for i in [0, 1]:
                        item = f"{voice} [{language}]"
                        self.voice_dropdowns[i].addItem(item, userData={"voice": voice, "sample": sample})
                elif language == "de_DE":
                    for i in [2, 3]:
                        item = f"{voice} [{language}]"
                        self.voice_dropdowns[i].addItem(item, userData={"voice": voice, "sample": sample})
            else:
                continue

    def disable_voice_settings(self):
        for dropdown in self.voice_dropdowns:
            dropdown.setEnabled(False)
        for test_button in self.voice_test_buttons:
            test_button.setEnabled(False)

    def connect_test_buttons(self):
        for i, test_button in enumerate(self.voice_test_buttons):
            test_button.clicked.connect(partial(self.test_voice, i))

    def test_voice(self, index):
        dropdown = self.voice_dropdowns[index]
        voice_data = dropdown.currentData()
        if voice_data:
            voice = voice_data["voice"]
            sample = voice_data["sample"]
            command = f'say -v "{voice}" "{sample}"'
            subprocess.Popen(command, shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def load_ui_from_variables(self):
        self.line_edits['anki_user_dir'].setText(anki_user_dir)
        self.line_edits['save_dir'].setText(save_dir)
        self.line_edits['things3_list_en'].setText(things_vocab_list_en)
        self.line_edits['things3_list_de'].setText(things_vocab_list_de)
        # setText may not trigger textChanged if empty string
        self.check_anki_user_dir()
        self.check_save_dir()

        voice_settings = [en_voice_1, en_voice_2, de_voice_1, de_voice_2]
        for i, voice_setting in enumerate(voice_settings):
            if voice_setting:
                for j in range(self.voice_dropdowns[i].count()):
                    item_data = self.voice_dropdowns[i].itemData(j)
                    if item_data and item_data["voice"] == voice_setting:
                        self.voice_dropdowns[i].setCurrentIndex(j)
                        break

    def select_directory(self, option, caption, default_dir):
        selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, caption, default_dir)
        if selected_directory:
            self.line_edits[option].setText(selected_directory)

    def save(self):
        global anki_user_dir, save_dir, things_vocab_list_en, things_vocab_list_de
        global en_voice_1, en_voice_2, de_voice_1, de_voice_2

        anki_user_dir = self.line_edits['anki_user_dir'].text()
        save_dir = self.line_edits['save_dir'].text()
        things_vocab_list_en = self.line_edits['things3_list_en'].text()
        things_vocab_list_de = self.line_edits['things3_list_de'].text()

        en_voice_1 = self.voice_dropdowns[0].currentData()["voice"]
        en_voice_2 = self.voice_dropdowns[1].currentData()["voice"]
        de_voice_1 = self.voice_dropdowns[2].currentData()["voice"]
        de_voice_2 = self.voice_dropdowns[3].currentData()["voice"]

        save_config_from_variables()
        self.initial_setup = False
        self.accept()

    def check_anki_user_dir(self):
        user_dir = self.line_edits['anki_user_dir'].text()
        media_dir = os.path.join(user_dir, "collection.media")
        self.anki_user_dir_valid = os.path.exists(media_dir)

        if self.anki_user_dir_valid:
            self.line_edits['anki_user_dir'].setStyleSheet("")
        else:
            self.line_edits['anki_user_dir'].setStyleSheet("color: red;")

        self.save_button.setEnabled(self.anki_user_dir_valid and self.save_dir_valid)

    def check_save_dir(self):
        dir_path = self.line_edits['save_dir'].text()
        self.save_dir_valid = os.path.exists(dir_path)

        if self.save_dir_valid:
            self.line_edits['save_dir'].setStyleSheet("")
        else:
            self.line_edits['save_dir'].setStyleSheet("color: red;")

        self.save_button.setEnabled(self.anki_user_dir_valid and self.save_dir_valid)

    def closeEvent(self, event):
        if self.initial_setup:
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Exit",
                "Configuration has not completed yet. Closing this window will exit the program.",
                QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
                QtWidgets.QMessageBox.StandardButton.Cancel
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Ok:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    if not load_config(app):
        sys.exit(0)
    config_window = ConfigWindow(app)
    config_window.show()
    sys.exit(app.exec())
