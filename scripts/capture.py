import cv2
import time 
import os
import sys

#get path to src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
data_path = os.path.join(project_root, 'data')


if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from MediPipeHandsModule.HandTrackingModule import hand_detector

except ImportError as e:
    print(f'error importing HandTracker module {e}')
    
def main():
    cap = cv2.VideoCapture(0)
    detector = hand_detector()
    pTime = 0
    #main loop
    while True:
        success, img = cap.read()
        if success:
            img = detector.find_hands(img)
            lm_list = detector.find_position(img)
            if len(lm_list) != 0:
                for hand in lm_list:
                    for joint in hand:
                        pass
            cv2.imshow('hand capture', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
