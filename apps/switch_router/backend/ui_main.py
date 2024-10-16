# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.refreshButton = QPushButton(self.frame)
        self.refreshButton.setObjectName("refreshButton")

        self.gridLayout_2.addWidget(self.refreshButton, 3, 1, 1, 1)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName("label_2")

        self.gridLayout_2.addWidget(self.label_2, 0, 2, 1, 1)

        self.list_inputOptions = QListWidget(self.frame)
        self.list_inputOptions.setObjectName("list_inputOptions")

        self.gridLayout_2.addWidget(self.list_inputOptions, 1, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(
            25, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.gridLayout_2.addItem(self.horizontalSpacer, 1, 1, 1, 1)

        self.list_outputOptions = QListWidget(self.frame)
        self.list_outputOptions.setObjectName("list_outputOptions")

        self.gridLayout_2.addWidget(self.list_outputOptions, 1, 2, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName("label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)

        self.widget = QWidget(self.frame)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_login = QPushButton(self.widget)
        self.btn_login.setObjectName("btn_login")

        self.horizontalLayout.addWidget(self.btn_login)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.gridLayout_2.addWidget(self.widget, 3, 0, 1, 1)

        self.switchConnect = QPushButton(self.frame)
        self.switchConnect.setObjectName("switchConnect")

        self.gridLayout_2.addWidget(self.switchConnect, 2, 1, 1, 1)

        self.currentInput = QLabel(self.frame)
        self.currentInput.setObjectName("currentInput")

        self.gridLayout_2.addWidget(self.currentInput, 2, 2, 1, 1)

        self.currentOutput = QLabel(self.frame)
        self.currentOutput.setObjectName("currentOutput")

        self.gridLayout_2.addWidget(self.currentOutput, 3, 2, 1, 1)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "RF Route", None)
        )
        self.refreshButton.setText(
            QCoreApplication.translate("MainWindow", "Refresh", None)
        )
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Output", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Input", None))
        self.btn_login.setText(QCoreApplication.translate("MainWindow", "Login", None))
        self.switchConnect.setText(
            QCoreApplication.translate("MainWindow", "Connect", None)
        )
        self.currentInput.setText(
            QCoreApplication.translate("MainWindow", "Input:", None)
        )
        self.currentOutput.setText(
            QCoreApplication.translate("MainWindow", "Output:", None)
        )

    # retranslateUi
