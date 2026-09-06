import serial
import threading
import queue
import time

running = True
ser = None
send_queue = queue.Queue()
recv_queue = queue.Queue()
uart_lock = threading.Lock()

try:
    ser = serial.Serial("/dev/serial0", 115200, timeout=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
except Exception as e:
    print(f"Error setting up the serial: {e}")


def _uart_send_worker():
    while running:
        try:
            msg = send_queue.get(timeout=0.1)
            if msg is None:
                break
            encoded_payload = msg.encode('utf-8')
            with uart_lock:
                ser.write(encoded_payload)
            print("message sent.")
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error sending bits: {e}")


def _uart_recv_worker():
    while running:
        try:
            if ser and ser.in_waiting > 0:
                with uart_lock:
                    payload = ser.readline().decode('utf-8', errors='ignore').strip()
                if payload:
                    recv_queue.put(payload)
                    print(f"received: {payload}")
        except Exception as e:
            print(f"Error receiving bits: {e}")
        time.sleep(0.01)


threading.Thread(target=_uart_send_worker, daemon=True).start()
threading.Thread(target=_uart_recv_worker, daemon=True).start()


def sendUART(payload: str):
    send_queue.put(payload)


def receiveUART():
    try:
        return recv_queue.get_nowait()
    except queue.Empty:
        return None


def send_demo():
    sendUART("test 123 ! :)")


def stop():
    global running
    running = False
    send_queue.put(None)
