"""AC remote-telemetry client.

Speaks Assetto Corsa's built-in UDP protocol on port 9996. The client
sends a 12-byte handshake to AC, expects a handshake response, then sends
a SUBSCRIBE_UPDATE to start receiving RTCarInfo packets at ~AC's
framerate. If AC isn't running, the handshake is retried periodically so
the dashboard auto-connects as soon as a session starts.
"""

from __future__ import annotations

import logging
import socket
import time

from PyQt6.QtCore import QThread, pyqtSignal

from ontrack_dashboard.telemetry import (
    AC_UDP_PORT,
    HANDSHAKE_RESPONSE_SIZES,
    OP_DISMISS,
    OP_HANDSHAKE,
    OP_SUBSCRIBE_UPDATE,
    RT_CAR_INFO_SIZE,
    SessionInfo,
    TelemetryError,
    TelemetryPacket,
    build_handshake,
)

logger = logging.getLogger(__name__)

_RECV_TIMEOUT_SEC = 0.5
_RECV_BUFFER_BYTES = 4096
_HANDSHAKE_RETRY_SEC = 2.0


class UDPReceiver(QThread):
    """Foreground thread that maintains an AC telemetry subscription.

    Despite the legacy name, this is an active client now -- AC requires
    a handshake before it sends any data. The thread loop:

      1. Open a UDP socket.
      2. Send HANDSHAKE; if no response within retry interval, resend.
      3. On handshake response, send SUBSCRIBE_UPDATE.
      4. Read RTCarInfo packets (328 bytes), parse, emit TelemetryPacket.
      5. If RTCarInfo packets stop arriving for a while, drop back to
         step 2 to recover from session restarts.
    """

    telemetry_received = pyqtSignal(object)  # TelemetryPacket
    session_info_received = pyqtSignal(object)  # SessionInfo
    connection_status = pyqtSignal(bool)

    def __init__(self, ac_ip: str = "127.0.0.1", ac_port: int = AC_UDP_PORT) -> None:
        super().__init__()
        self.ac_ip = ac_ip
        self.ac_port = ac_port
        self._socket: socket.socket | None = None
        self._running = True
        self._subscribed = False
        self._last_packet_at: float = 0.0

    def run(self) -> None:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(_RECV_TIMEOUT_SEC)
            # Windows surfaces ICMP "port unreachable" responses (sent when
            # we handshake AC but AC isn't in a session) as
            # ConnectionResetError on the next recvfrom. Disable that
            # behaviour so we can poll cleanly until AC comes online.
            if hasattr(socket, "SIO_UDP_CONNRESET"):
                self._socket.ioctl(socket.SIO_UDP_CONNRESET, False)
        except OSError:
            logger.exception("could not create UDP socket")
            self.connection_status.emit(False)
            return

        logger.info("AC client started -- target %s:%s", self.ac_ip, self.ac_port)
        last_handshake_at: float = 0.0

        try:
            while self._running:
                now = time.monotonic()

                if not self._subscribed and now - last_handshake_at >= _HANDSHAKE_RETRY_SEC:
                    self._send(build_handshake(OP_HANDSHAKE))
                    last_handshake_at = now

                # If we've been subscribed but haven't seen a packet for a
                # while, AC's session probably ended. Drop back to
                # handshake retries.
                if (
                    self._subscribed
                    and self._last_packet_at
                    and now - self._last_packet_at > 5.0
                ):
                    logger.info("packet timeout -- re-handshaking")
                    self._subscribed = False
                    self.connection_status.emit(False)

                try:
                    data, _addr = self._socket.recvfrom(_RECV_BUFFER_BYTES)
                except TimeoutError:
                    continue
                except ConnectionResetError:
                    # Belt-and-braces in case SIO_UDP_CONNRESET is
                    # unavailable (non-Windows, frozen runtimes). Just
                    # means the AC port isn't listening yet.
                    continue
                except OSError:
                    if self._running:
                        logger.exception("UDP recv error -- continuing")
                    continue

                self._dispatch(data)
        finally:
            self._dismiss()
            self._close_socket()

    def _dispatch(self, data: bytes) -> None:
        size = len(data)

        if size in HANDSHAKE_RESPONSE_SIZES:
            if not self._subscribed:
                logger.info("handshake response (%d bytes) -- subscribing", size)
                self._send(build_handshake(OP_SUBSCRIBE_UPDATE))
                self._subscribed = True
                self._last_packet_at = time.monotonic()
                self.connection_status.emit(True)
            try:
                session = SessionInfo.from_handshake(data)
            except TelemetryError:
                logger.debug("could not parse session info", exc_info=True)
            else:
                logger.info(
                    "session: %s on %s/%s (driver %s)",
                    session.car_name, session.track_name,
                    session.track_config, session.driver_name,
                )
                self.session_info_received.emit(session)
            return

        if size == RT_CAR_INFO_SIZE:
            try:
                packet = TelemetryPacket.from_bytes(data)
            except TelemetryError as exc:
                logger.debug("dropping malformed RTCarInfo: %s", exc)
                return
            self._last_packet_at = time.monotonic()
            self.telemetry_received.emit(packet)
            return

        logger.debug("ignoring unknown datagram of %d bytes", size)

    def _send(self, payload: bytes) -> None:
        if self._socket is None:
            return
        try:
            self._socket.sendto(payload, (self.ac_ip, self.ac_port))
        except OSError:
            logger.debug("send failed", exc_info=True)

    def _dismiss(self) -> None:
        if self._subscribed:
            self._send(build_handshake(OP_DISMISS))
            self._subscribed = False

    def _close_socket(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        except OSError:
            logger.debug("error closing UDP socket", exc_info=True)
        finally:
            self._socket = None

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait()
