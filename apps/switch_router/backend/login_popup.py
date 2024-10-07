from typing import Callable
from .popup_ui import Ui_login_popup
from PySide6.QtWidgets import QWidget, QMainWindow
from PySide6.QtCore import QObject, QRect, Signal, Qt
from PySide6.QtGui import QShowEvent


class PopupSignals(QObject):
    close = Signal()
    dataEntered = Signal(str, str, str)


class LoginPopup(QWidget):
    def __init__(self, parent: QMainWindow, close_cb, changed_cb):
        QWidget.__init__(self)
        self.ui = Ui_login_popup()
        self.ui.setupUi(self)
        # self.xOffset = (parent.width() - self.width()) // 2
        # self.yOffset = (parent.height() - self.height()) // 2
        # self.basePos = parent.pos()
        self.signals = PopupSignals()
        self.signals.close.connect(close_cb)
        self.signals.dataEntered.connect(changed_cb)
        self.ui.loginButton.clicked.connect(self.dataEntered_cb)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def dataEntered_cb(self):
        ipAddr = self.ui.inp_ipAddress.text().strip()
        username = self.ui.inp_username.text().strip()
        password = self.ui.inp_password.text().strip()

        self.signals.dataEntered.emit(ipAddr, username, password)
        self.signals.close.emit()

    def setPosition(self, parent: QMainWindow) -> None:
        self.setGeometry(
            QRect(
                parent.pos().x() + ((parent.width() - self.width()) // 2),
                parent.pos().y() + ((parent.height() - self.height()) // 2),
                self.width(),
                self.height(),
            )
        )
