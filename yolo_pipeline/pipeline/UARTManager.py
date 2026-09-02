import serial
import time


try:
    ser = serial.Serial("/dev/serial0", 115200, timeout=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
except Exception as e:
    print(f"Error setting up the serial: {e}")


def sendUART(payload: str):
    encoded_payload = payload.encode('utf-8')
    try:
        ser.write(encoded_payload)
        print("message sent.")
    except Exception as e:
        print(f"Error sending bits: {e}")


def receiveUART():
    if ser.in_waiting > 0:
        print("message received.")
        payload = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"received: {payload}")
        return payload
    return None


def send_demo():
    payload = "test 123 ! :)"
    encoded_payload = payload.encode('utf-8')
    try:
        ser.write(encoded_payload)
        print("message sent.")
    except Exception as e:
        print(f"Error sending bits: {e}")
