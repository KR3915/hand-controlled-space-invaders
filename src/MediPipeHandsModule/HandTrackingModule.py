import cv2
import mediapipe as mp 
import time
import numpy as np
#init camera on camera 0 (inbuilt)

class hand_detector():
    def __init__(self, mode=False, max_hands=2, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.mpDraw = mp.solutions.drawing_utils

    def find_hands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0, draw=True):

        lm_list = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            for handLms in self.results.multi_hand_landmarks: #get landmarks of each hand
                for id, lm in enumerate(handLms.landmark):  
                    h, w, c = img.shape # get shape of image (height, width, color channel)
                    cx, cy = int(lm.x*w), int(lm.y*h) #get x and y of landmark in pixels
                    lm_list.append([id, cx, cy])
                    #draws on the landmark 0

                self.mpDraw.draw_landmarks(img, my_hand, self.mp_hands.HAND_CONNECTIONS) 
        return lm_list 
    
    def get_bbox_location(self, img, hand_no=0, draw=True):

        lm_list = []
        x_list = []
        y_list = []

        bbox = None
        
        if self.results.multi_hand_landmarks:
            for hand_index, my_hand in enumerate(self.results.multi_hand_landmarks):
                if hand_index == hand_no:
                    for id, lm in enumerate(my_hand.landmark):
                        h,w,c = img.shape
                        cx, cy = int(lm.x*w), int(lm.y*h)

                        x_list.append(cx)
                        y_list.append(cy)
                        lm_list.append([id, cx, cy])

                #calculate bbox
                    x_min, x_max = min(x_list), max(x_list)
                    y_min, y_max = min(y_list), max(y_list)

                #add paddingmin 
                    buffer = 20
                    x_min = max(0, x_min - buffer)
                    y_min = max(0, y_min - buffer)
                    x_max = max(0, x_max + buffer)
                    y_max = max(0, y_max + buffer)
                   
                    x_min_coord = min(x_list)
                    x_max_coord = max(x_list)
                    y_min_coord = min(y_list)
                    y_max_coord = max(y_list)

                    lm_min_x = next(lm for lm in lm_list if lm[1] == x_min_coord)
                    lm_max_x = next(lm for lm in lm_list if lm[1] == x_max_coord)

                    lm_min_y = next(lm for lm in lm_list if lm[2] == y_min_coord)
                    lm_max_y = next(lm for lm in lm_list if lm[2] == y_max_coord)
                    
                    idd, minxx, minxy = lm_min_x
                    idd, minyx, minyy = lm_min_y
                    idd, maxxx, maxxy = lm_max_x
                    idd, maxyx, maxyy = lm_max_y






                    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                    if draw:
                        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                        cv2.line(img, (minxx, minxy), (maxxx, maxxy), (255,0,255), 2)
                        cv2.line(img, (minyx, minyy), (maxyx, maxyy), (255,0,255), 2)

                    return lm_list, bbox
        return lm_list, bbox


def main():
    cap = cv2.VideoCapture(0)
    pTime = 0
    cTime = 0
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.find_hands(img)    # count fps
        lm_list = detector.find_position(img)
        if len(lm_list) != 0:
            print(lm_list[4])
        cv2.imshow("Image", img)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()
