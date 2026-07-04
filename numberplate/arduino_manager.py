import serial
import threading
import time

class ArduinoManager:
    def __init__(self, port="/dev/cu.usbserial-120", baud=115200, socket_client=None):
        self.port = port
        self.baud = baud
        self.sio = socket_client
        self.serial = None
        self.running = False
        self.thread = None

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            print(f"🔌 Arduino Nano connected successfully on {self.port}!")
            time.sleep(2)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            print(f"⚠️ Arduino Nano not connected on {self.port}: {e}")
            return False

    def send_command(self, cmd: str):
        if self.serial and self.serial.is_open:
            try:
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.write(f"{cmd}\n".encode("utf-8"))
                print(f"⚡ Command sent to Arduino: {cmd}")
            except Exception as e:
                print(f"⚠️ Arduino send failed: {e}")
        else:
            print(f"⚠️ Arduino not connected. Command ignored: {cmd}")

    def _read_loop(self):
        while self.running:
            if self.serial and self.serial.is_open:
                try:
                    line = self.serial.readline().decode("utf-8").strip()
                    if line:
                        print(f"⚙️ Hardware Log: {line}")
                        self._parse_hardware_log(line)
                except Exception as e:
                    print(f"⚠️ Arduino read error: {e}")
                    time.sleep(1)
            else:
                time.sleep(1)

    def _parse_hardware_log(self, log_line: str):
        log_line_upper = log_line.upper()
        state = None

        # Parse states based on standard ACKs or cycle completions
        if "OPENING" in log_line_upper:
            state = "OPENING"
        elif "OPENED" in log_line_upper or "GATE OPEN" in log_line_upper:
            state = "OPENED"
        elif "CLOSING" in log_line_upper:
            state = "CLOSING"
        elif "CLOSED" in log_line_upper or "FINISHED" in log_line_upper or "CLEANLY" in log_line_upper:
            state = "CLOSED"
        elif "ERROR" in log_line_upper:
            state = "ERROR"

        if state and self.sio and self.sio.connected:
            try:
                self.sio.emit("arduino_ack", {"state": state})
                print(f"📡 Forwarded Arduino ACK to backend: {state}")
            except Exception as e:
                print(f"⚠️ Failed to forward ACK: {e}")

    def close(self):
        self.running = False
        if self.serial:
            self.serial.close()
