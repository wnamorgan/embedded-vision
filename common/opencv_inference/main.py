# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from __future__ import annotations

import argparse

from util import img_inference

import numpy as np

import time

import os
os.environ["QT_QPA_PLATFORM"] = "xcb"


def main(model,image):
    img_inference(model,image)

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--model", default="yolov8n.onnx", help="Input your ONNX model.")
    # parser.add_argument("--img", default=str(ASSETS / "bus.jpg"), help="Path to input image.")
    # args = parser.parse_args()
    # main(args.model, args.img)


    path = os.path.realpath(__file__).rsplit('/', 1)[0]
    main(path + '/yolov8n.onnx', path + '/zidane.jpg')