# Hand Tracking Module

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange?style=for-the-badge&logo=google)](https://developers.google.com/mediapipe)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)](LICENSE)

A simple Python module for **hand detection and landmark tracking** using Google’s **MediaPipe** and **OpenCV**.  
The module detects hands in a video stream or image, draws the hand landmarks, and returns their pixel coordinates.

---

## Features

- Detects up to two hands using MediaPipe.
- Draws hand landmarks and connections directly on the image.
- Returns a list of hand landmark coordinates `(id, x, y)` in pixels.
- Works with a live webcam feed or static images.

---

## Installation

Make sure you have Python **3.7 or newer**, then install the dependencies:

```bash
pip install opencv-python mediapipe numpy
```

Clone this repository or copy `HandTrackingModule.py` into your project directory.

---

## Usage Example

```python
import cv2
from HandTrackingModule import handDetector

cap = cv2.VideoCapture(0)
detector = handDetector()

while True:
    success, img = cap.read()
    img = detector.find_hands(img)
    lm_list = detector.find_position(img)

    if len(lm_list) != 0:
        print(lm_list[4])  # Example: print landmark 4 (tip of the thumb)

    cv2.imshow("Image", img)
    cv2.waitKey(1)
```
