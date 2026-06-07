"""System tray/control surface.

KDE Plasma supports StatusNotifierItem via DBus, but the common
AyatanaAppIndicator3 bindings expect GTK3 menu widgets. The GTK4-safe fallback
is a small control window that exposes the same commands.
"""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

from doubao_murmur.app_state import AppState, LoginStatus

logger = logging.getLogger(__name__)

# Try AyatanaAppIndicator3
_HAS_APPINDICATOR = False
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3

    _HAS_APPINDICATOR = True
except (ImportError, ValueError):
    pass

_CAN_USE_APPINDICATOR = _HAS_APPINDICATOR and hasattr(Gtk, "Menu")


class TrayIcon:
    """System tray icon with status menu."""

    def __init__(
        self,
        app_state: AppState,
        on_login_clicked,
        on_logout_clicked,
        on_quit_clicked,
        on_help_clicked=None,
    ) -> None:
        self.app_state = app_state
        self._on_login_clicked = on_login_clicked
        self._on_logout_clicked = on_logout_clicked
        self._on_quit_clicked = on_quit_clicked
        self._on_help_clicked = on_help_clicked
        self._indicator = None
        self._menu = None
        self._window: Gtk.Window | None = None
        self._status_label: Gtk.Label | None = None
        self._primary_button: Gtk.Button | None = None

    def start(self) -> None:
        """Create the tray icon or GTK4 fallback control window."""
        if _CAN_USE_APPINDICATOR:
            self._start_appindicator()
        else:
            logger.warning(
                "GTK4-compatible tray backend unavailable; using control window"
            )
            self._start_control_window()

        # Watch for state changes
        self.app_state.connect(
            "login-status-changed", lambda *_: self._rebuild_menu()
        )

    def _start_appindicator(self) -> None:
        self._indicator = AyatanaAppIndicator3.Indicator.new(
            "doubao-murmur",
            "audio-input-microphone-symbolic",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(
            AyatanaAppIndicator3.IndicatorStatus.ACTIVE
        )

        self._menu = Gtk.Menu()
        self._rebuild_menu()
        self._indicator.set_menu(self._menu)

    def _start_control_window(self) -> None:
        self._window = Gtk.Window()
        self._window.set_title("Doubao Murmur")
        self._window.set_default_size(320, 180)
        self._window.set_resizable(False)
        self._window.connect("close-request", self._on_control_close)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        self._status_label = Gtk.Label()
        self._status_label.set_xalign(0)
        box.append(self._status_label)

        self._primary_button = Gtk.Button()
        self._primary_button.connect("clicked", self._on_primary_clicked)
        box.append(self._primary_button)

        if self._on_help_clicked:
            help_button = Gtk.Button(label="使用帮助")
            help_button.connect("clicked", lambda _: self._on_help_clicked())
            box.append(help_button)

        quit_button = Gtk.Button(label="退出")
        quit_button.connect("clicked", lambda _: self._on_quit_clicked())
        box.append(quit_button)

        self._window.set_child(box)
        self._rebuild_menu()
        # Start minimized: only pop up when user action is required
        # (not logged in). Re-activating the app (launching it again)
        # presents the window via show_window().
        if self.app_state.login_status != LoginStatus.LOGGED_IN:
            self._window.present()

    def _rebuild_menu(self, *_args) -> None:
        """Rebuild the tray menu or refresh the control window."""
        if self._window:
            self._refresh_control_window()
            return

        if not self._menu:
            return

        # Clear existing items
        for child in self._menu.get_children():
            self._menu.remove(child)

        # Status label
        status_map = {
            LoginStatus.CHECKING: "⏳ 检查中...",
            LoginStatus.LOGGED_IN: "✅ 已登录",
            LoginStatus.NOT_LOGGED_IN: "❌ 未登录",
        }
        status = status_map.get(self.app_state.login_status, "⏳")
        item = Gtk.MenuItem(label=status)
        item.set_sensitive(False)
        self._menu.append(item)
        self._menu.append(Gtk.SeparatorMenuItem())

        if self.app_state.login_status != LoginStatus.LOGGED_IN:
            item = Gtk.MenuItem(label="登录豆包")
            item.connect("activate", lambda _: self._on_login_clicked())
            self._menu.append(item)
        else:
            item = Gtk.MenuItem(label="退出登录")
            item.connect("activate", lambda _: self._on_logout_clicked())
            self._menu.append(item)

        if self._on_help_clicked:
            item = Gtk.MenuItem(label="使用帮助")
            item.connect("activate", lambda _: self._on_help_clicked())
            self._menu.append(item)

        self._menu.append(Gtk.SeparatorMenuItem())

        item = Gtk.MenuItem(label="退出")
        item.connect("activate", lambda _: self._on_quit_clicked())
        self._menu.append(item)

        self._menu.show_all()

    def _refresh_control_window(self) -> None:
        status_map = {
            LoginStatus.CHECKING: "状态：检查中...",
            LoginStatus.LOGGED_IN: "状态：已登录",
            LoginStatus.NOT_LOGGED_IN: "状态：未登录",
        }
        if self._status_label:
            self._status_label.set_text(
                status_map.get(self.app_state.login_status, "状态：检查中...")
            )
        if self._primary_button:
            if self.app_state.login_status == LoginStatus.LOGGED_IN:
                self._primary_button.set_label("退出登录")
            else:
                self._primary_button.set_label("登录豆包")

    def _on_primary_clicked(self, _button) -> None:
        if self.app_state.login_status == LoginStatus.LOGGED_IN:
            self._on_logout_clicked()
        else:
            self._on_login_clicked()

    def show_window(self) -> None:
        """Present the control window (e.g. on app re-activation)."""
        if self._window:
            self._window.present()

    def _on_control_close(self, _window) -> bool:
        # Hide instead of quit — the app keeps running for the hotkey.
        # Quit via the window's 退出 button.
        self._window.set_visible(False)
        return True
