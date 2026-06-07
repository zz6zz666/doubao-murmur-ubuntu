"""X11 global key listener via the XRecord extension.

Sees BOTH physical keyboard events and XTEST-injected ones — Steam Input's
desktop layout injects controller-mapped keys (e.g. R3 -> Alt_R) via XTEST,
which never appears in /dev/input, so the evdev listener cannot see it.

Passive: does not grab keys or interfere with other clients.

Semantics mirror EvdevListener:
- Right Alt press-and-release with no other key in between -> toggle
- ESC press -> cancel
"""

from __future__ import annotations

import logging
import os
import threading

logger = logging.getLogger(__name__)


class X11KeyListener:
    """Global X11 key listener using the XRecord extension."""

    def __init__(self, on_toggle, on_escape) -> None:
        self.on_toggle = on_toggle
        self.on_escape = on_escape
        self._thread: threading.Thread | None = None
        self._running = False
        self._record_dpy = None
        self._ctrl_dpy = None
        self._context = None
        self._right_alt_down = False
        self._other_key_pressed = False
        self._kc_alt_r = 0
        self._kc_escape = 0

    @staticmethod
    def is_available() -> bool:
        """X11 session with the RECORD extension present."""
        if not os.environ.get("DISPLAY"):
            return False
        try:
            from Xlib.display import Display

            d = Display()
            try:
                return d.has_extension("RECORD")
            finally:
                d.close()
        except Exception:
            return False

    def start(self) -> bool:
        """Start listening. Returns False if setup fails."""
        try:
            from Xlib import XK
            from Xlib.display import Display
            from Xlib.ext import record

            self._record_dpy = Display()
            self._ctrl_dpy = Display()

            self._kc_alt_r = self._ctrl_dpy.keysym_to_keycode(XK.XK_Alt_R)
            self._kc_escape = self._ctrl_dpy.keysym_to_keycode(XK.XK_Escape)

            from Xlib import X

            self._context = self._record_dpy.record_create_context(
                0,
                [record.AllClients],
                [
                    {
                        "core_requests": (0, 0),
                        "core_replies": (0, 0),
                        "ext_requests": (0, 0, 0, 0),
                        "ext_replies": (0, 0, 0, 0),
                        "delivered_events": (0, 0),
                        "device_events": (X.KeyPress, X.KeyRelease),
                        "errors": (0, 0),
                        "client_started": False,
                        "client_died": False,
                    }
                ],
            )
        except Exception as e:
            logger.warning("XRecord setup failed: %s", e)
            self._cleanup()
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop, daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._ctrl_dpy and self._context:
            try:
                self._ctrl_dpy.record_disable_context(self._context)
                self._ctrl_dpy.flush()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)
        self._cleanup()

    def _cleanup(self) -> None:
        for dpy in (self._record_dpy, self._ctrl_dpy):
            if dpy:
                try:
                    dpy.close()
                except Exception:
                    pass
        self._record_dpy = None
        self._ctrl_dpy = None
        self._context = None

    def _listen_loop(self) -> None:
        try:
            # Blocks until record_disable_context is called
            self._record_dpy.record_enable_context(
                self._context, self._on_record_reply
            )
            self._record_dpy.record_free_context(self._context)
        except Exception as e:
            if self._running:
                logger.warning("XRecord loop ended: %s", e)

    def _on_record_reply(self, reply) -> None:
        from Xlib import X
        from Xlib.ext import record
        from Xlib.protocol import rq

        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            return
        if not reply.data or reply.data[0] < 2:
            return

        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, self._record_dpy.display, None, None
            )
            if event.type == X.KeyPress:
                self._handle_key(event.detail, pressed=True)
            elif event.type == X.KeyRelease:
                self._handle_key(event.detail, pressed=False)

    def _handle_key(self, keycode: int, pressed: bool) -> None:
        if keycode == self._kc_alt_r:
            if pressed:
                self._right_alt_down = True
                self._other_key_pressed = False
            else:
                if self._right_alt_down and not self._other_key_pressed:
                    self.on_toggle()
                self._right_alt_down = False
        elif pressed:
            if self._right_alt_down:
                self._other_key_pressed = True
            if keycode == self._kc_escape:
                self.on_escape()
