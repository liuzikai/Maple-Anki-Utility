# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'maple_utility.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MapleUtility(object):
    def setupUi(self, MapleUtility):
        MapleUtility.setObjectName("MapleUtility")
        MapleUtility.resize(1403, 730)
        self.mainWidget = QtWidgets.QWidget(MapleUtility)
        self.mainWidget.setGeometry(QtCore.QRect(20, 22, 1305, 846))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainWidget.sizePolicy().hasHeightForWidth())
        self.mainWidget.setSizePolicy(sizePolicy)
        self.mainWidget.setObjectName("mainWidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.mainWidget)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.widget_2 = QtWidgets.QWidget(self.mainWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
        self.widget_2.setSizePolicy(sizePolicy)
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_7 = QtWidgets.QLabel(self.widget_2)
        self.label_7.setObjectName("label_7")
        self.verticalLayout.addWidget(self.label_7)
        spacerItem = QtWidgets.QSpacerItem(20, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.groupBox_2 = QtWidgets.QGroupBox(self.widget_2)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.loadKindle = QtWidgets.QPushButton(self.groupBox_2)
        self.loadKindle.setObjectName("loadKindle")
        self.verticalLayout_4.addWidget(self.loadKindle)
        self.loadCSV = QtWidgets.QPushButton(self.groupBox_2)
        self.loadCSV.setObjectName("loadCSV")
        self.verticalLayout_4.addWidget(self.loadCSV)
        self.newEntry = QtWidgets.QPushButton(self.groupBox_2)
        self.newEntry.setObjectName("newEntry")
        self.verticalLayout_4.addWidget(self.newEntry)
        self.clearList = QtWidgets.QPushButton(self.groupBox_2)
        self.clearList.setObjectName("clearList")
        self.verticalLayout_4.addWidget(self.clearList)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.entryList = QtWidgets.QListWidget(self.widget_2)
        self.entryList.setEnabled(True)
        self.entryList.setMaximumSize(QtCore.QSize(180, 16777215))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.entryList.setFont(font)
        self.entryList.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.entryList.setObjectName("entryList")
        self.verticalLayout.addWidget(self.entryList)
        self.groupBox = QtWidgets.QGroupBox(self.widget_2)
        self.groupBox.setMaximumSize(QtCore.QSize(180, 16777215))
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.unreadBar = QtWidgets.QProgressBar(self.groupBox)
        self.unreadBar.setMinimumSize(QtCore.QSize(0, 6))
        self.unreadBar.setMaximumSize(QtCore.QSize(130, 6))
        self.unreadBar.setStyleSheet("QProgressBar {\n"
"    text-align: center;\n"
"    background-color: rgba(0, 0, 0, 25);\n"
"    border-radius: 3px;\n"
"    height: 6px;\n"
"}\n"
"\n"
"QProgressBar::chunk {\n"
"     background-color: rgb(10, 95, 255);\n"
"     border-radius: 3px\n"
" }")
        self.unreadBar.setProperty("value", 24)
        self.unreadBar.setTextVisible(False)
        self.unreadBar.setObjectName("unreadBar")
        self.gridLayout_3.addWidget(self.unreadBar, 0, 1, 1, 1)
        self.confirmedBar = QtWidgets.QProgressBar(self.groupBox)
        self.confirmedBar.setMaximumSize(QtCore.QSize(16777215, 6))
        self.confirmedBar.setStyleSheet("QProgressBar {\n"
"    text-align: center;\n"
"    background-color: rgba(0, 0, 0, 25);\n"
"    border-radius: 3px;\n"
"    height: 6px;\n"
"}\n"
"\n"
"QProgressBar::chunk {\n"
"     background-color: rgb(41, 200, 50);\n"
"     border-radius: 3px\n"
" }")
        self.confirmedBar.setProperty("value", 24)
        self.confirmedBar.setTextVisible(False)
        self.confirmedBar.setObjectName("confirmedBar")
        self.gridLayout_3.addWidget(self.confirmedBar, 1, 1, 1, 1)
        self.discardBar = QtWidgets.QProgressBar(self.groupBox)
        self.discardBar.setMinimumSize(QtCore.QSize(0, 6))
        self.discardBar.setMaximumSize(QtCore.QSize(16777215, 6))
        self.discardBar.setStyleSheet("QProgressBar {\n"
"    text-align: center;\n"
"    background-color: rgba(0, 0, 0, 25);\n"
"    border-radius: 3px;\n"
"    height: 6px;\n"
"}\n"
"\n"
"QProgressBar::chunk {\n"
"     background-color: rgb(253, 130, 8);\n"
"     border-radius: 3px\n"
" }")
        self.discardBar.setProperty("value", 24)
        self.discardBar.setTextVisible(False)
        self.discardBar.setObjectName("discardBar")
        self.gridLayout_3.addWidget(self.discardBar, 2, 1, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox)
        self.label_8.setObjectName("label_8")
        self.gridLayout_3.addWidget(self.label_8, 0, 0, 1, 1)
        self.label_9 = QtWidgets.QLabel(self.groupBox)
        self.label_9.setObjectName("label_9")
        self.gridLayout_3.addWidget(self.label_9, 1, 0, 1, 1)
        self.label_10 = QtWidgets.QLabel(self.groupBox)
        self.label_10.setObjectName("label_10")
        self.gridLayout_3.addWidget(self.label_10, 2, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.horizontalLayout_3.addWidget(self.widget_2)
        self.editWidget = QtWidgets.QWidget(self.mainWidget)
        self.editWidget.setObjectName("editWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.editWidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.editWidget)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.widget_4 = QtWidgets.QWidget(self.editWidget)
        self.widget_4.setObjectName("widget_4")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.widget_4)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.subject = QtWidgets.QPlainTextEdit(self.widget_4)
        self.subject.setMinimumSize(QtCore.QSize(0, 47))
        self.subject.setMaximumSize(QtCore.QSize(16777215, 47))
        font = QtGui.QFont()
        font.setPointSize(30)
        self.subject.setFont(font)
        self.subject.setObjectName("subject")
        self.horizontalLayout_5.addWidget(self.subject)
        self.freqBar = QtWidgets.QProgressBar(self.widget_4)
        self.freqBar.setMaximumSize(QtCore.QSize(16777215, 47))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.freqBar.setFont(font)
        self.freqBar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.freqBar.setStyleSheet("QProgressBar {\n"
"    text-align: center;\n"
"    background-color: rgba(0, 0, 0, 25);\n"
"    border-radius: 3px;\n"
"    height: 6px;\n"
"}\n"
"\n"
"QProgressBar::chunk {\n"
"     background-color: rgb(10, 95, 255);\n"
"     border-radius: 3px;\n"
" }")
        self.freqBar.setMaximum(5)
        self.freqBar.setProperty("value", 2)
        self.freqBar.setOrientation(QtCore.Qt.Vertical)
        self.freqBar.setObjectName("freqBar")
        self.horizontalLayout_5.addWidget(self.freqBar)
        self.cardType = QtWidgets.QComboBox(self.widget_4)
        self.cardType.setMaximumSize(QtCore.QSize(75, 16777215))
        self.cardType.setObjectName("cardType")
        self.cardType.addItem("")
        self.cardType.addItem("")
        self.horizontalLayout_5.addWidget(self.cardType)
        self.verticalLayout_3.addWidget(self.widget_4)
        self.label_2 = QtWidgets.QLabel(self.editWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        self.pronFrame = QtWidgets.QFrame(self.editWidget)
        self.pronFrame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.pronFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.pronFrame.setObjectName("pronFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.pronFrame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pronSamantha = QtWidgets.QRadioButton(self.pronFrame)
        self.pronSamantha.setObjectName("pronSamantha")
        self.horizontalLayout.addWidget(self.pronSamantha)
        self.pronDaniel = QtWidgets.QRadioButton(self.pronFrame)
        self.pronDaniel.setObjectName("pronDaniel")
        self.horizontalLayout.addWidget(self.pronDaniel)
        self.verticalLayout_3.addWidget(self.pronFrame)
        self.label_3 = QtWidgets.QLabel(self.editWidget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.widget_3 = QtWidgets.QWidget(self.editWidget)
        self.widget_3.setObjectName("widget_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.paraphrase = QtWidgets.QTextEdit(self.widget_3)
        self.paraphrase.setMinimumSize(QtCore.QSize(0, 150))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.paraphrase.setFont(font)
        self.paraphrase.setObjectName("paraphrase")
        self.horizontalLayout_4.addWidget(self.paraphrase)
        self.imageLabel = QtWidgets.QLabel(self.widget_3)
        self.imageLabel.setMinimumSize(QtCore.QSize(0, 150))
        self.imageLabel.setMaximumSize(QtCore.QSize(16777215, 150))
        self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.imageLabel.setObjectName("imageLabel")
        self.horizontalLayout_4.addWidget(self.imageLabel)
        self.verticalLayout_3.addWidget(self.widget_3)
        self.label_4 = QtWidgets.QLabel(self.editWidget)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        self.extension = QtWidgets.QPlainTextEdit(self.editWidget)
        self.extension.setMaximumSize(QtCore.QSize(16777215, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.extension.setFont(font)
        self.extension.setObjectName("extension")
        self.verticalLayout_3.addWidget(self.extension)
        self.label_5 = QtWidgets.QLabel(self.editWidget)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_3.addWidget(self.label_5)
        self.example = QtWidgets.QTextEdit(self.editWidget)
        self.example.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.example.setFont(font)
        self.example.setObjectName("example")
        self.verticalLayout_3.addWidget(self.example)
        self.source = QtWidgets.QTextEdit(self.editWidget)
        self.source.setMinimumSize(QtCore.QSize(0, 22))
        self.source.setMaximumSize(QtCore.QSize(16777215, 22))
        self.source.setStyleSheet("QTextEdit {\n"
"    background-color: rgba(0, 0, 0, 0);\n"
"}")
        self.source.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.source.setReadOnly(True)
        self.source.setObjectName("source")
        self.verticalLayout_3.addWidget(self.source)
        self.label_6 = QtWidgets.QLabel(self.editWidget)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_3.addWidget(self.label_6)
        self.hint = QtWidgets.QPlainTextEdit(self.editWidget)
        self.hint.setMinimumSize(QtCore.QSize(0, 23))
        self.hint.setMaximumSize(QtCore.QSize(16777215, 23))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.hint.setFont(font)
        self.hint.setObjectName("hint")
        self.verticalLayout_3.addWidget(self.hint)
        self.widget = QtWidgets.QWidget(self.editWidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.saveAllButton = QtWidgets.QPushButton(self.widget)
        self.saveAllButton.setObjectName("saveAllButton")
        self.horizontalLayout_2.addWidget(self.saveAllButton)
        self.saveBar = QtWidgets.QProgressBar(self.widget)
        self.saveBar.setProperty("value", 24)
        self.saveBar.setObjectName("saveBar")
        self.horizontalLayout_2.addWidget(self.saveBar)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.discardButton = QtWidgets.QPushButton(self.widget)
        self.discardButton.setObjectName("discardButton")
        self.horizontalLayout_2.addWidget(self.discardButton)
        self.nextButton = QtWidgets.QPushButton(self.widget)
        self.nextButton.setAcceptDrops(True)
        self.nextButton.setObjectName("nextButton")
        self.horizontalLayout_2.addWidget(self.nextButton)
        self.verticalLayout_3.addWidget(self.widget)
        self.horizontalLayout_3.addWidget(self.editWidget)
        self.widget_5 = QtWidgets.QWidget(self.mainWidget)
        self.widget_5.setObjectName("widget_5")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget_5)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.webView = QtWebEngineWidgets.QWebEngineView(self.widget_5)
        self.webView.setMinimumSize(QtCore.QSize(600, 0))
        self.webView.setMaximumSize(QtCore.QSize(600, 16777215))
        self.webView.setObjectName("webView")
        self.verticalLayout_2.addWidget(self.webView)
        self.horizontalLayout_3.addWidget(self.widget_5)

        self.retranslateUi(MapleUtility)
        QtCore.QMetaObject.connectSlotsByName(MapleUtility)

    def retranslateUi(self, MapleUtility):
        _translate = QtCore.QCoreApplication.translate
        MapleUtility.setWindowTitle(_translate("MapleUtility", "Maple Utility"))
        self.label_7.setText(_translate("MapleUtility", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Stay Hungry, Stay Foolish.</span></p></body></html>"))
        self.groupBox_2.setTitle(_translate("MapleUtility", "Load Data"))
        self.loadKindle.setText(_translate("MapleUtility", "Kindle Database"))
        self.loadCSV.setText(_translate("MapleUtility", "CSV List"))
        self.newEntry.setText(_translate("MapleUtility", "New Single Entry"))
        self.clearList.setText(_translate("MapleUtility", "Clear List"))
        self.groupBox.setTitle(_translate("MapleUtility", "Progress"))
        self.label_8.setText(_translate("MapleUtility", "Unread"))
        self.label_9.setText(_translate("MapleUtility", "Confirmed"))
        self.label_10.setText(_translate("MapleUtility", "Discarded"))
        self.label.setText(_translate("MapleUtility", "Subject"))
        self.subject.setPlainText(_translate("MapleUtility", "Subject"))
        self.freqBar.setFormat(_translate("MapleUtility", "%v"))
        self.cardType.setCurrentText(_translate("MapleUtility", "R"))
        self.cardType.setItemText(0, _translate("MapleUtility", "R"))
        self.cardType.setItemText(1, _translate("MapleUtility", "RD"))
        self.label_2.setText(_translate("MapleUtility", "Pronunciation"))
        self.pronSamantha.setText(_translate("MapleUtility", "Samantha"))
        self.pronDaniel.setText(_translate("MapleUtility", "Daniel"))
        self.label_3.setText(_translate("MapleUtility", "Paraphrase"))
        self.paraphrase.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:20pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Paraphrase</p></body></html>"))
        self.imageLabel.setToolTip(_translate("MapleUtility", "Right click to search image on Google Image"))
        self.imageLabel.setText(_translate("MapleUtility", "Image"))
        self.label_4.setText(_translate("MapleUtility", "Extension"))
        self.extension.setPlainText(_translate("MapleUtility", "Extension\n"
""))
        self.label_5.setText(_translate("MapleUtility", "Example"))
        self.example.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:16pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.source.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt;\">Source</span></p></body></html>"))
        self.label_6.setText(_translate("MapleUtility", "Hint"))
        self.hint.setPlainText(_translate("MapleUtility", "Hint"))
        self.saveAllButton.setText(_translate("MapleUtility", "Save All"))
        self.discardButton.setText(_translate("MapleUtility", "Discard"))
        self.nextButton.setText(_translate("MapleUtility", "Confirm"))

from PyQt5 import QtWebEngineWidgets
