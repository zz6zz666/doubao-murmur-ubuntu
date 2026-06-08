"""A single on-screen key widget.

Wraps a non-focusable :class:`Gtk.Button`. Tapping dispatches to
``controller.press_key(keydef)``; the widget never takes focus so the target
window keeps it.

Keys flagged ``repeat`` (backspace, arrows) auto-repeat while held. The
repeat loop is leak-proof by construction — earlier it could run forever
when a touchscreen dropped the gesture's release event. Now each tick both
(a) checks the pointer button is still down (``x11_button1_down``) and
(b) honours an absolute max duration, so it always stops even if the
release/cancel signal never arrives.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

from doubao_murmur.keyboard.layouts import KIND_CHAR, KIND_LAYER, KIND_MOD, KeyDef
from doubao_murmur.keyboard.state import ModState
from doubao_murmur.ui.windowing import x11_button1_down

# Auto-repeat timing (ms): initial delay, steady rate, and a hard backstop
# that caps a single hold no matter what (defence against a lost release on
# a device where the button-state query is unreliable).
_REPEAT_DELAY_MS = 400
_REPEAT_INTERVAL_MS = 80
_REPEAT_MAX_MS = 4000


class KeyButton:
    def __init__(self, keydef: KeyDef, controller) -> None:
        self.keydef = keydef
        self._controller = controller
        self._repeat_source: int | None = None
        self._repeat_elapsed = 0

        button = Gtk.Button()
        button.set_focusable(False)
        button.set_can_focus(False)
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.add_css_class("key")
        if keydef.kind == KIND_MOD:
            button.add_css_class("key-mod")
        elif keydef.kind == KIND_LAYER:
            button.add_css_class("key-layer")
        elif keydef.keysym in ("space",):
            button.add_css_class("key-space")
        button.set_label(self._display_label())

        if keydef.repeat:
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self._on_press)
            gesture.connect("released", self._on_release)
            gesture.connect("cancel", self._on_cancel)
            button.add_controller(gesture)
        else:
            button.connect("clicked", self._on_clicked)

        self.widget = button

    # -- layout ------------------------------------------------------------

    @property
    def width(self) -> float:
        return self.keydef.width

    # -- events ------------------------------------------------------------

    def _on_clicked(self, _button) -> None:
        self._controller.press_key(self.keydef)

    def _on_press(self, _gesture, _n, _x, _y) -> None:
        self._controller.press_key(self.keydef)
        self._stop_repeat()
        self._repeat_elapsed = 0
        self._repeat_source = GLib.timeout_add(
            _REPEAT_DELAY_MS, self._begin_repeat
        )

    def _begin_repeat(self) -> bool:
        if not self._repeat_should_continue():
            self._repeat_source = None
            return GLib.SOURCE_REMOVE
        self._controller.press_key(self.keydef)
        self._repeat_elapsed = _REPEAT_DELAY_MS
        self._repeat_source = GLib.timeout_add(
            _REPEAT_INTERVAL_MS, self._tick_repeat
        )
        return GLib.SOURCE_REMOVE

    def _tick_repeat(self) -> bool:
        self._repeat_elapsed += _REPEAT_INTERVAL_MS
        if not self._repeat_should_continue():
            self._repeat_source = None
            return GLib.SOURCE_REMOVE
        self._controller.press_key(self.keydef)
        return GLib.SOURCE_CONTINUE

    def _repeat_should_continue(self) -> bool:
        return self._repeat_elapsed <= _REPEAT_MAX_MS and x11_button1_down()

    def _on_release(self, _gesture, _n, _x, _y) -> None:
        self._stop_repeat()

    def _on_cancel(self, _gesture, _sequence) -> None:
        self._stop_repeat()

    def _stop_repeat(self) -> None:
        if self._repeat_source is not None:
            GLib.source_remove(self._repeat_source)
            self._repeat_source = None

    # -- display -----------------------------------------------------------

    def refresh(self) -> None:
        """Re-render label + active state from the keyboard state."""
        self.widget.set_label(self._display_label())
        if self.keydef.kind == KIND_MOD:
            st = self._controller.state.mod_state(self.keydef.mod)
            for cls in ("armed", "locked"):
                self.widget.remove_css_class(cls)
            if st == ModState.ARMED:
                self.widget.add_css_class("armed")
            elif st == ModState.LOCKED:
                self.widget.add_css_class("locked")

    def _display_label(self) -> str:
        kd = self.keydef
        if kd.kind != KIND_CHAR:
            return kd.label
        shifted = self._controller.state.is_shifted()
        if kd.is_letter:
            return kd.label.upper() if shifted else kd.label.lower()
        if shifted and kd.shift_label:
            return kd.shift_label
        return kd.label
