from ultralytics import YOLO
import requests
import time
import cv2
import serial
import threading
import sys
from .UARTManager import sendUART, receiveUART, send_demo
from .firebaseManager import read_data, write_data

running = True

# Load your exported NCNN model directory for Pi optimization
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

print("Start stream. Press 'q' in the video window to quit.")

try:
    while running:
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            time.sleep(0.1)
            continue

        results = model(frame, imgsz=320, verbose=False)
        annotated_frame = results[0].plot()

        cv2.imshow("YOLOv8 External Camera Live Feed", annotated_frame)

        ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            try:
                requests.post(SERVER_URL, data=buffer.tobytes(), timeout=2)
            except requests.exceptions.RequestException as e:
                print(f"Upload failed: {e}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

        sendUART(example_msg)

        receiveUART()

        payload=read_data(boat_name, boat_id)
        print(payload)

        write_data(boat_name, boat_id, {"status": "demo"})

        time.sleep(0.03)
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    cap.release()
    cv2.destroyAllWindows()
