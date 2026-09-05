from ultralytics import YOLO
import requests
import time
import cv2
import serial
import threading
import sys
from UARTManager import sendUART, receiveUART
from firebaseManager import read_data, write_data

running = True

try:
    model = YOLO("../model_weights_and_props/best_ncnn_model")
except Exception as e:
    print(f"Failed to load NCNN model: {e}. Falling back to standard model...")
    model = YOLO("../model_weights_and_props/best.pt")

example_msg = "{'drive':1,'relay':0,'switch':0,'motor_a':10,'motor_b':10}"
SERVER_URL = 'https://your-flask-website.com/upload'

boat_name = "scuba"
boat_id = 9999

cam_index = 0
cap = cv2.VideoCapture(cam_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Load capture failed")
    sys.exit(1)

print("Start stream. Press Ctrl+C to quit.")

upload_lock = threading.Lock()
latest_jpeg = None

def upload_worker():
    global latest_jpeg
    while running:
        with upload_lock:
            buf = latest_jpeg
        if buf is not None:
            try:
                requests.post(SERVER_URL, data=buf.tobytes(), timeout=2)
            except requests.exceptions.RequestException as e:
                print(f"Upload failed: {e}")
            latest_jpeg = None
        time.sleep(0.01)


def sendToEsp():
    while running:
        data = read_data(boat_name, boat_id)
        if data:
            esp_message = str(data)
            sendUART(esp_message)
            print(f"data from firebase: {data}")
        time.sleep(0.5)


def reciveFromEsp():
    while running:
        payload = receiveUART()
        if payload:
            print(f"data received from esp: {payload}")
            write_data(boat_name, boat_id, {"status": payload})
        time.sleep(0.1)



threading.Thread(target=upload_worker, daemon=True).start()

threading.Thread(target=sendToEsp, daemon=True).start()
threading.Thread(target=reciveFromEsp, daemon=True).start()

try:
    while running:
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            time.sleep(0.1)
            continue

        results = model(frame, imgsz=320, verbose=False)
        annotated_frame = results[0].plot()

        ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            with upload_lock:
                latest_jpeg = buffer

except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    running = False
    cap.release()
