import math
import os
import sys
import time

import keyring
import ntplib
import psutil
import pyotp
import requests
import win32gui
import win32process
import wx
import wx.adv


PRODUCT_NAME = "XIVLauncher Automatic OTP"
KEYRING_REALM = "ffxivotp"
CONFIGURE_TEXT = "Configure OTP Secret"
GENERATE_TEXT = "Generate OTP Code"
SEND_TEXT = "Send OTP Code"
YOUR_CODE_IS = "Your OTP Code is: "
CHECK_EVERY_MS = 1 * 1000
SEARCH_PROCESS_NAME = "XIVLauncher.exe"
SEARCH_WINDOW_NAME = "Enter OTP key"
TIMEOUT_TOTP_SEND = 30

# https://stackoverflow.com/a/51061279
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


def get_secret():
    return keyring.get_password(KEYRING_REALM, "secret")


def generate_otp(override=None):
    totp = pyotp.parse_uri(get_secret() or override)
    return totp.now()


def check_clock():
    try:
        client = ntplib.NTPClient()
        res = client.request("pool.ntp.org")

        delta = abs(res.tx_time - time.time())

        if delta >= 5:
            dlg = wx.MessageDialog(
                None,
                "Your PC clock is %.1f seconds out of sync. Generated OTP codes may be incorrect." % delta,
                PRODUCT_NAME,
                style=wx.ICON_ERROR,
            )
            dlg.ShowModal()

    except Exception as e:
        print(e)
        pass


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.check_after = 0
        self.generate_lock = False
        self.closing = False

        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(resource_path("icon.ico"))
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_click)

        self.timer = wx.Timer(self)
        self.timer.Start(CHECK_EVERY_MS)
        self.Bind(wx.EVT_TIMER, self.on_tick)

        self.ShowBalloon(PRODUCT_NAME, PRODUCT_NAME + " started. Right click tray icon to configure.")

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, CONFIGURE_TEXT, self.on_setup)
        create_menu_item(menu, GENERATE_TEXT, self.on_generate)
        create_menu_item(menu, SEND_TEXT, self.on_send)
        menu.AppendSeparator()
        create_menu_item(menu, "Exit", self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, PRODUCT_NAME)

    def on_tick(self, event):
        if self.check_after > time.time():
            return

        active_window = win32gui.GetForegroundWindow()

        if win32gui.GetWindowText(active_window).lower() != SEARCH_WINDOW_NAME.lower():
            return

        _, active_window_pid = win32process.GetWindowThreadProcessId(active_window)
        active_window_pname = psutil.Process(active_window_pid).name().lower()

        if active_window_pname != SEARCH_PROCESS_NAME.lower():
            return

        self.on_send(event, True)

        self.check_after = time.time() + TIMEOUT_TOTP_SEND

    def on_click(self, event):
        if get_secret():
            self.on_generate(event)
        else:
            self.on_setup(event)

    def on_setup(self, event):
        if get_secret():
            erase_config_msg_dialog = wx.MessageDialog(
                None,
                "A OTP secret has already been saved. Would you like to erase it?",
                CONFIGURE_TEXT,
                style=wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.NO_DEFAULT,
            )
            erase_config_msg_modal = erase_config_msg_dialog.ShowModal()

            if erase_config_msg_modal != wx.ID_YES:
                return

            text = ""
            while text.lower() != "confirm":
                erase_config_text_dialog = wx.TextEntryDialog(
                    None,
                    'Are you sure you would like to erase your OTP secret? Type "confirm" to confirm.',
                    CONFIGURE_TEXT,
                    text,
                )
                erase_config_text_modal = erase_config_text_dialog.ShowModal()

                if erase_config_text_modal != wx.ID_OK:
                    return

                text = erase_config_text_dialog.GetValue().lower()

            keyring.delete_password(KEYRING_REALM, "secret")

            erase_confirm_msg_dialog = wx.MessageDialog(None, "OTP secret erased.", CONFIGURE_TEXT)
            erase_confirm_msg_dialog.ShowModal()
            return

        setup_dialog = wx.PasswordEntryDialog(None, "Please enter the OTP secret URL:", CONFIGURE_TEXT)
        rc1 = setup_dialog.ShowModal()

        if rc1 == wx.ID_OK:
            secret = setup_dialog.GetValue()

            if not (secret.startswith("otpauth://")) or not generate_otp(secret):
                invalid_dialog = wx.MessageDialog(None, "Invalid secret.", CONFIGURE_TEXT, style=wx.ICON_ERROR)
                invalid_dialog.ShowModal()
                return self.on_setup(event)

            keyring.set_password(KEYRING_REALM, "secret", secret)

            confirm_dialog = wx.MessageDialog(None, "Secret saved.", CONFIGURE_TEXT)
            confirm_dialog.ShowModal()

    def on_generate(self, event):
        if self.generate_lock:
            return

        self.generate_lock = True

        if not get_secret():
            dialog = wx.MessageDialog(
                None,
                "The OTP secret has not yet been configured. Configure a secret first.",
                GENERATE_TEXT,
                style=wx.ICON_WARNING,
            )
            dialog.ShowModal()

            self.generate_lock = False
            return

        totp = pyotp.parse_uri(get_secret())

        process_dialog = wx.ProgressDialog(GENERATE_TEXT, YOUR_CODE_IS, style=wx.PD_CAN_ABORT)
        running = True

        check_clock()

        while running:
            if self.closing:
                break

            time_remaining = math.floor(totp.interval - time.time() % totp.interval)
            progress = int(time_remaining * 100 / totp.interval)

            running, _ = process_dialog.Update(progress, YOUR_CODE_IS + str(totp.now()))
            time.sleep(0.01)

        self.generate_lock = False

    def on_send(self, event, auto=False):
        if not get_secret():
            if not auto:
                dialog = wx.MessageDialog(
                    None,
                    "The OTP secret has not yet been configured. Configure a secret first.",
                    GENERATE_TEXT,
                    style=wx.ICON_WARNING,
                )
                dialog.ShowModal()

            return

        self.ShowBalloon(PRODUCT_NAME, "Sending OTP code...")

        try:
            response = requests.get(f"http://localhost:4646/ffxivlauncher/{generate_otp()}")
            response.raise_for_status()

            self.ShowBalloon(PRODUCT_NAME, "OTP code sent")
        except Exception as e:
            self.ShowBalloon(PRODUCT_NAME, "Error sending OTP code")
            return

        check_clock()

    def on_exit(self, event):
        self.closing = True
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
