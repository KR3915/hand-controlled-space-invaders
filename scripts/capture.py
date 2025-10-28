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

            lm_list, bbox = detector.get_bbox_location(img)
            if len(lm_list) != 0 and bbox:
                x_min, y_min, _, _ = bbox
                for hand in lm_list:
                    for joint in hand:
                        #calculate normalized coordinates
                        normalized_x = (joint[1] - x_min)
                        normalized_y = (joint[2] - y_min)
                        print(f'normalized coordinate is: {(normalized_x, normalized_y)}')
            img = cv2.flip(img, 1)           
            cv2.imshow('hand capture', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
