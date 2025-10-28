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
    print(f'error importing HandTrackingModule: {e}')

def normalize_landmarks(lm_list, bbox, handedness):
    """
    Normalizes the landmarks based on the bounding box and handedness.

    Args:
        lm_list: A list of landmarks for a hand.
        bbox: The bounding box of the hand.
        handedness: The handedness of the hand ('Left' or 'Right').

    Returns:
        A list of normalized landmarks.
    """
    normalized_landmarks = []
    if len(lm_list) != 0 and bbox:
        wrist = lm_list[0]  # Wrist is the first landmark
        for joint in lm_list:
            try:
                # Get relative position to the wrist
                normalized_x = (joint[1] - wrist[1])
                normalized_y = (joint[2] - wrist[2])
                normalized_landmarks.append((normalized_x, normalized_y))
            except (TypeError, IndexError) as e:
                print(f"Error processing joint: {joint}, error: {e}")
    return normalized_landmarks

def main():
    cap = cv2.VideoCapture(0)
    detector = hand_detector()
    pTime = 0

    # main loop
    while True:
        success, img = cap.read()

        if success:
            img = detector.find_hands(img)
            handedness = detector.get_handedness()

            if handedness:
                for i, hand in enumerate(handedness):
                    lm_list, bbox = detector.get_bbox_location(img, hand_no=i)
                    if len(lm_list) != 0 and bbox:
                        normalized_landmarks = normalize_landmarks(lm_list, bbox, hand)
                        if normalized_landmarks:
                            print(f'{hand} normalized landmarks are: {normalized_landmarks}')

            img = cv2.flip(img, 1)
            cv2.imshow('hand capture', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
