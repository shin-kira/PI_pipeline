from ultralytics import YOLO


def export_ncnn():
    model = YOLO("../model_weights_and_props/best.pt")
    ncnn_model = model.export(format="ncnn", quantize=16)
    print(f"Exported NCNN model: {ncnn_model}")


if __name__ == "__main__":
    export_ncnn()
