# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_popup.ui'
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
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)


class Ui_login_popup(object):
    def setupUi(self, login_popup):
        if not login_popup.objectName():
            login_popup.setObjectName("login_popup")
        login_popup.resize(400, 173)
        self.gridLayout = QGridLayout(login_popup)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QFrame(login_popup)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.loginButton = QPushButton(self.frame)
        self.loginButton.setObjectName("loginButton")

        self.gridLayout_2.addWidget(self.loginButton, 6, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout_2.addItem(self.verticalSpacer, 0, 0, 1, 2)

        self.verticalSpacer_2 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout_2.addItem(self.verticalSpacer_2, 5, 0, 1, 2)

        self.inp_ipAddress = QLineEdit(self.frame)
        self.inp_ipAddress.setObjectName("inp_ipAddress")

        self.gridLayout_2.addWidget(self.inp_ipAddress, 1, 1, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName("label")

        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)

        self.inp_password = QLineEdit(self.frame)
        self.inp_password.setObjectName("inp_password")

        self.gridLayout_2.addWidget(self.inp_password, 3, 1, 1, 1)

        self.label2 = QLabel(self.frame)
        self.label2.setObjectName("label2")

        self.gridLayout_2.addWidget(self.label2, 3, 0, 1, 1)

        self.inp_username = QLineEdit(self.frame)
        self.inp_username.setObjectName("inp_username")

        self.gridLayout_2.addWidget(self.inp_username, 2, 1, 1, 1)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName("label_3")

        self.gridLayout_2.addWidget(self.label_3, 2, 0, 1, 1)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        QWidget.setTabOrder(self.inp_ipAddress, self.inp_username)
        QWidget.setTabOrder(self.inp_username, self.inp_password)
        QWidget.setTabOrder(self.inp_password, self.loginButton)

        self.retranslateUi(login_popup)

        QMetaObject.connectSlotsByName(login_popup)

    # setupUi

    def retranslateUi(self, login_popup):
        login_popup.setWindowTitle(
            QCoreApplication.translate("login_popup", "Form", None)
        )
        self.loginButton.setText(
            QCoreApplication.translate("login_popup", "Login", None)
        )
        self.label.setText(
            QCoreApplication.translate("login_popup", "IP Address", None)
        )
        self.label2.setText(QCoreApplication.translate("login_popup", "Password", None))
        self.label_3.setText(
            QCoreApplication.translate("login_popup", "Username", None)
        )

    # retranslateUi
