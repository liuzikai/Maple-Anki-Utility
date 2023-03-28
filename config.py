import sys
import os
import configparser
import appdirs
from PyQt6 import QtCore, QtWidgets, QtGui

anki_user_dir = None
save_dir = None
csv_default_dir = ""
things_vocab_list_en = None
things_vocab_list_de = None

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
    os.makedirs(config_dir, exist_ok=True)
    with open(config_file, 'w') as f:
        parser.write(f)


def is_config_valid() -> bool:
    global anki_user_dir, save_dir, csv_default_dir
    if anki_user_dir is None or not os.path.exists(anki_user_dir):
        return False
    if save_dir is None or not os.path.exists(save_dir):
        return False
    return True


def load_config(app) -> bool:
    global anki_user_dir, save_dir, csv_default_dir, things_vocab_list_en, things_vocab_list_de

    config_exists = os.path.exists(config_file)

    parser.read(config_file)

    anki_user_dir = parser.get('DEFAULT', 'anki_user_dir', fallback=None)
    save_dir = parser.get('DEFAULT', 'save_dir', fallback=os.path.join(os.path.expanduser("~"), "Desktop"))
    csv_default_dir = parser.get('DEFAULT', 'csv_default_dir', fallback="")
    things_vocab_list_en = parser.get('DEFAULT', 'things_vocab_list_en', fallback="English Quick List")
    things_vocab_list_de = parser.get('DEFAULT', 'things_vocab_list_de', fallback="Deutsch schnell Liste")

    if not config_exists or not is_config_valid():
        if anki_user_dir is None or not os.path.exists(anki_user_dir):
            anki_user_dir = "PLEASE SELECT YOUR ANKI USER DIRECTORY"
        config_window = ConfigWindow(app, initial_setup=True)
        config_window.show()
        app.exec()

    return is_config_valid()  # user may cancel


class ConfigWindow(QtWidgets.QWidget):
    def __init__(self, app, initial_setup=False):
        super().__init__()
        self.app = app
        self.initial_setup = initial_setup

        self.anki_user_dir_valid = False
        self.save_dir_valid = False
        self.csv_default_dir_valid = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Configuration')

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

        # CSV Default Directory row
        csv_default_dir_edit, csv_default_dir_button = create_directory_row(
            2, 'csv_default_dir', 'Default Directory when Opening CSV (Optional)')
        csv_default_dir_edit.textChanged.connect(self.check_csv_default_dir)
        csv_default_dir_button.clicked.connect(
            lambda: self.select_directory('csv_default_dir', 'Select the Default Directory when Opening CSV',
                                          csv_default_dir_edit.text()))

        # Things 3 Project (EN) row
        things3_list_en_label = QtWidgets.QLabel('Things 3 Vocabulary List (EN)')
        things3_list_en_edit = QtWidgets.QLineEdit()
        layout.addWidget(things3_list_en_label, 3, 0)
        layout.addWidget(things3_list_en_edit, 3, 1)
        self.line_edits['things3_list_en'] = things3_list_en_edit

        # Thing 3 Project (DE) row
        things3_list_de_label = QtWidgets.QLabel('Things 3 Vocabulary List (DE)')
        things3_list_de_edit = QtWidgets.QLineEdit()
        layout.addWidget(things3_list_de_label, 4, 0)
        layout.addWidget(things3_list_de_edit, 4, 1)
        self.line_edits['things3_list_de'] = things3_list_de_edit

        # Create Save and Cancel buttons
        self.save_button = QtWidgets.QPushButton('Save')
        self.cancel_button = QtWidgets.QPushButton('Cancel')

        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.close)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout, 5, 1, 1, 2)

        self.load_defaults()

    def load_defaults(self):
        self.line_edits['anki_user_dir'].setText(anki_user_dir)
        self.line_edits['save_dir'].setText(save_dir)
        self.line_edits['csv_default_dir'].setText(csv_default_dir)
        self.line_edits['things3_list_en'].setText(things_vocab_list_en)
        self.line_edits['things3_list_de'].setText(things_vocab_list_de)
        # setText may not trigger textChanged if empty string
        self.check_anki_user_dir()
        self.check_save_dir()
        self.check_csv_default_dir()

    def select_directory(self, option, caption, default_dir):
        selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, caption, default_dir)
        if selected_directory:
            self.line_edits[option].setText(selected_directory)

    def save(self):
        global anki_user_dir, save_dir, csv_default_dir, things_vocab_list_en, things_vocab_list_de

        anki_user_dir = self.line_edits['anki_user_dir'].text()
        save_dir = self.line_edits['save_dir'].text()
        csv_default_dir = self.line_edits['csv_default_dir'].text()
        things_vocab_list_en = self.line_edits['things3_list_en'].text()
        things_vocab_list_de = self.line_edits['things3_list_de'].text()

        save_config_from_variables()
        self.initial_setup = False
        self.close()

    def check_anki_user_dir(self):
        user_dir = self.line_edits['anki_user_dir'].text()
        media_dir = os.path.join(user_dir, "collection.media")
        self.anki_user_dir_valid = os.path.exists(media_dir)

        if self.anki_user_dir_valid:
            self.line_edits['anki_user_dir'].setStyleSheet("")
        else:
            self.line_edits['anki_user_dir'].setStyleSheet("color: red;")

        self.save_button.setEnabled(self.anki_user_dir_valid and self.save_dir_valid and self.csv_default_dir_valid)

    def check_save_dir(self):
        dir_path = self.line_edits['save_dir'].text()
        self.save_dir_valid = os.path.exists(dir_path)

        if self.save_dir_valid:
            self.line_edits['save_dir'].setStyleSheet("")
        else:
            self.line_edits['save_dir'].setStyleSheet("color: red;")

        self.save_button.setEnabled(self.anki_user_dir_valid and self.save_dir_valid and self.csv_default_dir_valid)

    def check_csv_default_dir(self):
        dir_path = self.line_edits['csv_default_dir'].text()
        self.csv_default_dir_valid = (dir_path == "" or os.path.exists(dir_path))

        if self.csv_default_dir_valid:
            self.line_edits['csv_default_dir'].setStyleSheet("")
        else:
            self.line_edits['csv_default_dir'].setStyleSheet("color: red;")

        self.save_button.setEnabled(self.anki_user_dir_valid and self.save_dir_valid and self.csv_default_dir_valid)

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
