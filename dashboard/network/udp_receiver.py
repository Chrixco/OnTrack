import socket
import json
from PyQt6.QtCore import QThread, pyqtSignal

class UDPReceiver(QThread):
    telemetry_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)

    def __init__(self, ip='0.0.0.0', port=20777):
        super().__init__()
        self.ip = ip
        self.port = port
        self._socket = None
        self._running = True

    def run(self):
        """Run UDP listener on background thread."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.ip, self.port))
            self._socket.settimeout(0.5)

            self.connection_status.emit(True)

            while self._running:
                try:
                    data, addr = self._socket.recvfrom(4096)
                    try:
                        telemetry = json.loads(data.decode('utf-8'))
                        if isinstance(telemetry, dict) and 'v' in telemetry:
                            self.telemetry_received.emit(telemetry)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        pass
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        print("UDP receive error: {0}".format(str(e)))
                    break

        except Exception as e:
            print("UDP socket error: {0}".format(str(e)))
            self.connection_status.emit(False)
        finally:
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass

    def stop(self):
        """Stop the UDP receiver thread."""
        self._running = False
        self.quit()
        self.wait()
