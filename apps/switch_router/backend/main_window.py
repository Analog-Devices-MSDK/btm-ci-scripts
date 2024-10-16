import sys

# pylint: disable=no-name-in-module,c-extension-no-member
from PySide6.QtCore import QMutex, QSettings, QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from .ui_main import Ui_MainWindow
from .login_popup import LoginPopup
import PySide6
import paramiko
from paramiko.channel import ChannelFile
import json


class MainWindow(QMainWindow):
    # pylint: disable=too-many-instance-attributes
    """
    App Main Window
    """

    RX_DEFAULT_UPDATE_RATE = 10  # 1 second slider is only int
    VERSION = "1.0.0"

    MODEL_IN = "USB-1SP16T-83H"
    MODEL_OUT = "USB-1SP8T-63H"

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()

        self.settings = QSettings(".login")
        self.ui.setupUi(self)

        self.popup = None
        self.ssh = None
        self.resource_inputs = None
        self.resource_outputs = None
        self.ip = ""
        self.user = ""
        self.password = ""

        self.ui.btn_login.clicked.connect(self.showLoginPopup)
        self.ui.switchConnect.clicked.connect(self._connect_switch)

        self._attempt_login()

    def _connect_switch(self):
        if (
            self.ssh is None
            or self.resource_inputs is None
            or self.resource_outputs is None
        ):
            self._show_basic_msg_box("Cannot set switches!")
            return

        input = self.ui.list_inputOptions.currentItem().text()
        output = self.ui.list_outputOptions.currentItem().text()

        set_in_cmd = f"mcrfsw {self.MODEL_IN} -s {self.resource_inputs[input]}"
        set_out_cmd = f"mcrfsw {self.MODEL_OUT} -s {self.resource_outputs[output]}"

        try:
            _, _, _ = self.ssh.exec_command(f"{set_in_cmd} && {set_out_cmd}")
            self._read_switches()
        except:
            self._show_basic_msg_box("Cannot read switches!")

    def _read_switches(self):
        if (
            self.ssh is None
            or self.resource_inputs is None
            or self.resource_outputs is None
        ):
            self._show_basic_msg_box("Cannot read switches!")
            return

        get_in_cmd = f"mcrfsw {self.MODEL_IN} -g "
        get_out_cmd = f"mcrfsw {self.MODEL_OUT} -g"

        try:
            _, stdout, _ = self.ssh.exec_command(get_in_cmd)

            input_read = int(stdout.read().decode("utf-8"))

            self.ui.currentInput.setText(f"Input: Unknown")
            for resource, state in self.resource_inputs.items():
                if int(state) == input_read:
                    self.ui.currentInput.setText(f"Input: {resource}")

            _, stdout, _ = self.ssh.exec_command(get_out_cmd)
            output_read = int(stdout.read().decode("utf-8"))

            self.ui.currentOutput.setText(f"Output: Unknown")
            for resource, state in self.resource_outputs.items():
                if int(state) == output_read:
                    self.ui.currentOutput.setText(f"Input: {resource}")

        except:
            self._show_basic_msg_box("Failed to read switch state from remote!")

    def _attempt_login(self):
        self.ip = self.settings.value("ip", "")
        self.user = self.settings.value("user", "")
        self.password = self.settings.value("password", "")

        try:
            self.login(self.ip, self.user, self.password)
            self._read_switches()
        except:
            self.showLoginPopup()

    def showEvent(self, event: PySide6.QtGui.QShowEvent) -> None:
        super().showEvent(event)

    def showLoginPopup(self) -> None:
        if self.ssh is not None:
            self.ssh.close()

        self.popup = LoginPopup(self, self.closePopup, self.login)

        self.popup.ui.inp_ipAddress.setText(self.ip)
        self.popup.ui.inp_username.setText(self.user)
        self.popup.ui.inp_password.setText(self.password)

        self.popup.show()
        self.popup.activateWindow()

    def closePopup(self) -> None:
        self.popup.hide()
        self.popup = None

    def get_switch_resources(self):
        stdout: ChannelFile
        _, stdout, _ = self.ssh.exec_command("cat $CI_BOARD_CONFIG")

        resources = json.loads(stdout.read())

        output = {}
        input = {}

        for resource, values in resources.items():
            if ("sw_model" in values and values["sw_model"] is not None) and (
                "sw_state" in values and values["sw_state"] is not None
            ):
                model = values["sw_model"]
                state = values["sw_state"]
                if model == self.MODEL_OUT:
                    output[resource] = state
                elif model == self.MODEL_IN:
                    input[resource] = state

        return input, output

    def login(self, ipAddr: str, username: str, password: str) -> None:
        self.ssh = paramiko.SSHClient()

        self.ssh.load_system_host_keys()
        self.ssh.connect(ipAddr, username=username, password=password)

        self.settings.setValue("ip", ipAddr)
        self.settings.setValue("user", username)
        self.settings.setValue("password", password)

        input, output = self.get_switch_resources()

        self.resource_inputs = input
        self.resource_outputs = output

        self.ui.list_inputOptions.addItems(input.keys())
        self.ui.list_outputOptions.addItems(output.keys())

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        if self.ssh is not None:
            self.ssh.close()
        return super().closeEvent(event)

    def _show_basic_msg_box(self, msg):
        """
        Display a basic message box with a given message
        """
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.exec()
