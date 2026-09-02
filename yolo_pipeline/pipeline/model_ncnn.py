
from ultralytics import YOLO

model=YOLO("../model_weights_and_props/best.pt")
ncnn_model = model.export(format="ncnn", quantize=16)
