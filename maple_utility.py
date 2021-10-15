# Form implementation generated from reading ui file 'maple_utility.ui'
#
# Created by: PyQt6 UI code generator 6.2.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MapleUtility(object):
    def setupUi(self, MapleUtility):
        MapleUtility.setObjectName("MapleUtility")
        MapleUtility.resize(1421, 888)
        self.mainWidget = QtWidgets.QWidget(MapleUtility)
        self.mainWidget.setGeometry(QtCore.QRect(20, 22, 1297, 874))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainWidget.sizePolicy().hasHeightForWidth())
        self.mainWidget.setSizePolicy(sizePolicy)
        self.mainWidget.setObjectName("mainWidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.mainWidget)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.widget_2 = QtWidgets.QWidget(self.mainWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
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
        self.groupBox_2 = QtWidgets.QGroupBox(self.widget_2)
        self.groupBox_2.setTitle("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.loadCSV = QtWidgets.QPushButton(self.groupBox_2)
        self.loadCSV.setObjectName("loadCSV")
        self.gridLayout.addWidget(self.loadCSV, 3, 1, 1, 1)
        self.loadKindle = QtWidgets.QPushButton(self.groupBox_2)
        self.loadKindle.setObjectName("loadKindle")
        self.gridLayout.addWidget(self.loadKindle, 3, 0, 1, 1)
        self.englishMode = QtWidgets.QRadioButton(self.groupBox_2)
        self.englishMode.setChecked(True)
        self.englishMode.setObjectName("englishMode")
        self.gridLayout.addWidget(self.englishMode, 0, 0, 1, 1)
        self.deutschMode = QtWidgets.QRadioButton(self.groupBox_2)
        self.deutschMode.setObjectName("deutschMode")
        self.gridLayout.addWidget(self.deutschMode, 0, 1, 1, 1)
        self.loadThings = QtWidgets.QPushButton(self.groupBox_2)
        self.loadThings.setObjectName("loadThings")
        self.gridLayout.addWidget(self.loadThings, 5, 0, 1, 1)
        self.newEntry = QtWidgets.QPushButton(self.groupBox_2)
        self.newEntry.setObjectName("newEntry")
        self.gridLayout.addWidget(self.newEntry, 5, 1, 1, 1)
        self.clearList = QtWidgets.QPushButton(self.groupBox_2)
        self.clearList.setObjectName("clearList")
        self.gridLayout.addWidget(self.clearList, 6, 0, 1, 2)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.entryList = QtWidgets.QListWidget(self.widget_2)
        self.entryList.setEnabled(True)
        self.entryList.setMaximumSize(QtCore.QSize(180, 16777215))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.entryList.setFont(font)
        self.entryList.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
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
"     border-radius: 3px;\n"
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
"     border-radius: 3px;\n"
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
"     border-radius: 3px;\n"
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
        self.subjectSuggest = QtWidgets.QPushButton(self.widget_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.subjectSuggest.sizePolicy().hasHeightForWidth())
        self.subjectSuggest.setSizePolicy(sizePolicy)
        self.subjectSuggest.setObjectName("subjectSuggest")
        self.horizontalLayout_5.addWidget(self.subjectSuggest)
        self.freqBar = QtWidgets.QProgressBar(self.widget_4)
        self.freqBar.setMaximumSize(QtCore.QSize(16777215, 47))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.freqBar.setFont(font)
        self.freqBar.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
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
        self.freqBar.setProperty("value", 0)
        self.freqBar.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.freqBar.setObjectName("freqBar")
        self.horizontalLayout_5.addWidget(self.freqBar)
        self.widget_6 = QtWidgets.QWidget(self.widget_4)
        self.widget_6.setObjectName("widget_6")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget_6)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.checkR = QtWidgets.QCheckBox(self.widget_6)
        self.checkR.setObjectName("checkR")
        self.verticalLayout_5.addWidget(self.checkR)
        self.checkS = QtWidgets.QCheckBox(self.widget_6)
        self.checkS.setObjectName("checkS")
        self.verticalLayout_5.addWidget(self.checkS)
        self.checkD = QtWidgets.QCheckBox(self.widget_6)
        self.checkD.setObjectName("checkD")
        self.verticalLayout_5.addWidget(self.checkD)
        self.horizontalLayout_5.addWidget(self.widget_6)
        self.verticalLayout_3.addWidget(self.widget_4)
        self.label_2 = QtWidgets.QLabel(self.editWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        self.pronFrame = QtWidgets.QFrame(self.editWidget)
        self.pronFrame.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.pronFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.pronFrame.setObjectName("pronFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.pronFrame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pronA = QtWidgets.QRadioButton(self.pronFrame)
        self.pronA.setObjectName("pronA")
        self.horizontalLayout.addWidget(self.pronA)
        self.pronB = QtWidgets.QRadioButton(self.pronFrame)
        self.pronB.setObjectName("pronB")
        self.horizontalLayout.addWidget(self.pronB)
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
        self.paraphrase.setAcceptRichText(False)
        self.paraphrase.setObjectName("paraphrase")
        self.horizontalLayout_4.addWidget(self.paraphrase)
        self.imageLabel = QtWidgets.QLabel(self.widget_3)
        self.imageLabel.setMinimumSize(QtCore.QSize(0, 150))
        self.imageLabel.setMaximumSize(QtCore.QSize(16777215, 150))
        self.imageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setObjectName("imageLabel")
        self.horizontalLayout_4.addWidget(self.imageLabel)
        self.verticalLayout_3.addWidget(self.widget_3)
        self.label_4 = QtWidgets.QLabel(self.editWidget)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        self.extension = QtWidgets.QTextEdit(self.editWidget)
        self.extension.setMaximumSize(QtCore.QSize(16777215, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.extension.setFont(font)
        self.extension.setAcceptRichText(False)
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
        self.example.setAcceptRichText(False)
        self.example.setObjectName("example")
        self.verticalLayout_3.addWidget(self.example)
        self.widget_7 = QtWidgets.QWidget(self.editWidget)
        self.widget_7.setObjectName("widget_7")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.widget_7)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.checkSource = QtWidgets.QCheckBox(self.widget_7)
        self.checkSource.setText("")
        self.checkSource.setObjectName("checkSource")
        self.horizontalLayout_6.addWidget(self.checkSource)
        self.source = QtWidgets.QTextEdit(self.widget_7)
        self.source.setMinimumSize(QtCore.QSize(0, 22))
        self.source.setMaximumSize(QtCore.QSize(16777215, 22))
        font = QtGui.QFont()
        font.setKerning(True)
        self.source.setFont(font)
        self.source.setStyleSheet("")
        self.source.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.source.setReadOnly(False)
        self.source.setAcceptRichText(False)
        self.source.setObjectName("source")
        self.horizontalLayout_6.addWidget(self.source)
        self.verticalLayout_3.addWidget(self.widget_7)
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
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.discardButton = QtWidgets.QPushButton(self.widget)
        self.discardButton.setObjectName("discardButton")
        self.horizontalLayout_2.addWidget(self.discardButton)
        self.confirmButton = QtWidgets.QPushButton(self.widget)
        self.confirmButton.setAcceptDrops(True)
        self.confirmButton.setObjectName("confirmButton")
        self.horizontalLayout_2.addWidget(self.confirmButton)
        self.verticalLayout_3.addWidget(self.widget)
        self.horizontalLayout_3.addWidget(self.editWidget)
        self.widget_5 = QtWidgets.QWidget(self.mainWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_5.sizePolicy().hasHeightForWidth())
        self.widget_5.setSizePolicy(sizePolicy)
        self.widget_5.setObjectName("widget_5")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget_5)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_3 = QtWidgets.QGroupBox(self.widget_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.queryStatusLabel = QtWidgets.QLabel(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.queryStatusLabel.sizePolicy().hasHeightForWidth())
        self.queryStatusLabel.setSizePolicy(sizePolicy)
        self.queryStatusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.queryStatusLabel.setObjectName("queryStatusLabel")
        self.horizontalLayout_7.addWidget(self.queryStatusLabel)
        self.queryCollins = QtWidgets.QPushButton(self.groupBox_3)
        self.queryCollins.setObjectName("queryCollins")
        self.horizontalLayout_7.addWidget(self.queryCollins)
        self.queryGoogle = QtWidgets.QPushButton(self.groupBox_3)
        self.queryGoogle.setObjectName("queryGoogle")
        self.horizontalLayout_7.addWidget(self.queryGoogle)
        self.queryGoogleImage = QtWidgets.QPushButton(self.groupBox_3)
        self.queryGoogleImage.setObjectName("queryGoogleImage")
        self.horizontalLayout_7.addWidget(self.queryGoogleImage)
        self.queryGoogleTranslate = QtWidgets.QPushButton(self.groupBox_3)
        self.queryGoogleTranslate.setObjectName("queryGoogleTranslate")
        self.horizontalLayout_7.addWidget(self.queryGoogleTranslate)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.webViewFrame = QtWidgets.QWidget(self.widget_5)
        self.webViewFrame.setMinimumSize(QtCore.QSize(600, 0))
        self.webViewFrame.setMaximumSize(QtCore.QSize(600, 16777215))
        self.webViewFrame.setObjectName("webViewFrame")
        self.webViewVerticalLayout = QtWidgets.QVBoxLayout(self.webViewFrame)
        self.webViewVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.webViewVerticalLayout.setObjectName("webViewVerticalLayout")
        self.webLoadingView = QtWidgets.QWidget(self.webViewFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webLoadingView.sizePolicy().hasHeightForWidth())
        self.webLoadingView.setSizePolicy(sizePolicy)
        self.webLoadingView.setObjectName("webLoadingView")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.webLoadingView)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.webLoadingBar = QtWidgets.QProgressBar(self.webLoadingView)
        self.webLoadingBar.setProperty("value", 24)
        self.webLoadingBar.setObjectName("webLoadingBar")
        self.horizontalLayout_8.addWidget(self.webLoadingBar)
        self.forceStopQuery = QtWidgets.QPushButton(self.webLoadingView)
        self.forceStopQuery.setObjectName("forceStopQuery")
        self.horizontalLayout_8.addWidget(self.forceStopQuery)
        self.webViewVerticalLayout.addWidget(self.webLoadingView)
        self.verticalLayout_2.addWidget(self.webViewFrame)
        self.horizontalLayout_3.addWidget(self.widget_5)

        self.retranslateUi(MapleUtility)
        QtCore.QMetaObject.connectSlotsByName(MapleUtility)

    def retranslateUi(self, MapleUtility):
        _translate = QtCore.QCoreApplication.translate
        MapleUtility.setWindowTitle(_translate("MapleUtility", "Maple Utility"))
        self.label_7.setText(_translate("MapleUtility", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Stay hungry.&nbsp;Stay foolish.</span></p></body></html>"))
        self.loadCSV.setText(_translate("MapleUtility", "CSV"))
        self.loadKindle.setText(_translate("MapleUtility", "Kindle"))
        self.englishMode.setText(_translate("MapleUtility", "English"))
        self.deutschMode.setText(_translate("MapleUtility", "Deutsch"))
        self.loadThings.setText(_translate("MapleUtility", "Things"))
        self.newEntry.setText(_translate("MapleUtility", "New"))
        self.clearList.setText(_translate("MapleUtility", "Clear "))
        self.groupBox.setTitle(_translate("MapleUtility", "Progress"))
        self.label_8.setText(_translate("MapleUtility", "?"))
        self.label_9.setText(_translate("MapleUtility", "✓"))
        self.label_10.setText(_translate("MapleUtility", "✗"))
        self.label.setText(_translate("MapleUtility", "Subject"))
        self.subject.setPlainText(_translate("MapleUtility", "Subject"))
        self.subjectSuggest.setText(_translate("MapleUtility", "Suggest"))
        self.freqBar.setFormat(_translate("MapleUtility", "%v"))
        self.checkR.setText(_translate("MapleUtility", "R"))
        self.checkS.setText(_translate("MapleUtility", "S"))
        self.checkD.setText(_translate("MapleUtility", "D"))
        self.label_2.setText(_translate("MapleUtility", "Pronunciation"))
        self.pronA.setText(_translate("MapleUtility", "Samantha"))
        self.pronB.setText(_translate("MapleUtility", "Daniel"))
        self.label_3.setText(_translate("MapleUtility", "Paraphrase"))
        self.paraphrase.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:20pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.imageLabel.setToolTip(_translate("MapleUtility", "Right click to search image on Google Image"))
        self.imageLabel.setText(_translate("MapleUtility", "Image"))
        self.label_4.setText(_translate("MapleUtility", "Extension"))
        self.label_5.setText(_translate("MapleUtility", "Example"))
        self.example.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:16pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.source.setHtml(_translate("MapleUtility", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.label_6.setText(_translate("MapleUtility", "Hint"))
        self.hint.setPlainText(_translate("MapleUtility", "Hint"))
        self.discardButton.setText(_translate("MapleUtility", "Discard"))
        self.confirmButton.setText(_translate("MapleUtility", "Confirm"))
        self.groupBox_3.setTitle(_translate("MapleUtility", "Web Query"))
        self.queryStatusLabel.setToolTip(_translate("MapleUtility", "Finished/Working/Free"))
        self.queryStatusLabel.setText(_translate("MapleUtility", "0/0/0"))
        self.queryCollins.setText(_translate("MapleUtility", "Collins"))
        self.queryGoogle.setText(_translate("MapleUtility", "Google"))
        self.queryGoogleImage.setText(_translate("MapleUtility", "Image"))
        self.queryGoogleTranslate.setText(_translate("MapleUtility", "Translate"))
        self.forceStopQuery.setText(_translate("MapleUtility", "Force Stop"))
