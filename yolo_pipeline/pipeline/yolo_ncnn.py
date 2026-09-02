from ultralytics import YOLO
import ncnn
import requests
import time
import cv2
import serial


model=YOLO("../model_weights_and_props/best.pt")

example_msg="{'drive':1,'relay':0,'switch':0,'motor_a':10,'motor_b':10}"

SERVER_URL = 'https://your-flask-website.com/upload'

boat_name="scuba"
boat_id=9999

try:
    ser=serial.Serial("/dev/ttyS0",115200)
except:
    print("error configuring the serial connection")


cam_index=0
cap=cv2.VideoCapture(cam_index)
if not cap.isOpened():
    print("Load captiour failed")
    exit()

print("start stream press 'q' to quit")

def cam_read():
    while True:
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            break

        results = model(frame, verbose=False)

        annotated_frame = results[0].plot()

        cv2.imshow("YOLOv8 External Camera Live Feed", annotated_frame)
        ret,buffer=cv2.imencode('.jpg',annotated_frame,[cv2.IMWRITE_JPEG_QUALITY,80])
        if not ret:
            continue
        try:
            response = requests.post(SERVER_URL, data=buffer.tobytes(), timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"Upload failed: {e}")
            time.sleep(2)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.05)
    cap.release()
    cv2.destroyAllWindows()


def write_UART():
    try:
        payload=ser.write(example_msg.encode())
    except:
        print("error sending mesage")


def read_UART():
    while True:
        if ser.in_waiting>0:
            payload=ser.read_all()
            decoded_payload=payload.decode(errors="ignore").strip()

            if decoded_payload:
                print(decoded_payload)
        time.sleep(0.05)
    