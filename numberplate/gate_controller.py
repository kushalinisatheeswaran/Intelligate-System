import serial
import time
import logging

# Configure basic logging to see updates in your console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GateController")

SERIAL_PORT = "/dev/cu.usbserial-120"
BAUD_RATE = 115200

def trigger_physical_gate():
    """
    Establishes a connection to the Arduino Nano over USB Serial
    and sends the hardware ignition command.
    """
    try:
        logger.info(f"Opening Serial Port: {SERIAL_PORT}...")
        # Open connection with a short timeout constraint
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=3)
        
        # CRITICAL: Arduino resets on serial connect. Wait for it to boot!
        time.sleep(2) 
        
        logger.info("Sending 'OPEN' instruction sequence to Nano...")
        ser.write(b"OPEN\n")
        
        # Read the immediate acknowledgment string from the Nano
        response = ser.readline().decode('utf-8').strip()
        logger.info(f"Hardware Response: {response}")
        
        ser.close()
        return True
    except Exception as e:
        logger.error(f"Failed to communicate with Nano hardware: {e}")
        return False

# Quick hardware sanity execution test
if __name__ == "__main__":
    print("Testing connection to Nano...")
    trigger_physical_gate()