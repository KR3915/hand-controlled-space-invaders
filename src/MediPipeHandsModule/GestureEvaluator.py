import joblib
import numpy as np

def normalize_landmarks(lm_list, bbox):
    normalized_landmarks = []
    if len(lm_list) != 0 and bbox:
        wrist = lm_list[0]  # Wrist is the first landmark
        bbox_width = bbox[2]
        bbox_height = bbox[3]
        for joint in lm_list:
            try:
                # Get relative position to the wrist and scale by bbox dimensions
                normalized_x = (joint[1] - wrist[1]) / bbox_width
                normalized_y = (joint[2] - wrist[2]) / bbox_height
                normalized_landmarks.append((normalized_x, normalized_y))
            except (TypeError, IndexError, ZeroDivisionError) as e:
                print(f"Error processing joint: {joint}, error: {e}")
    return normalized_landmarks

def evaluate(landmarks, handedness, bbox):
    """
    Evaluates hand landmarks to determine a gesture.
    """
    # Load the gesture recognition model
    model = joblib.load("models/gesture_model.pkl")

    # Encode handedness: 'Left' to 0, 'Right' to 1 (consistent with training)
    encoded_handedness = 0
    if handedness == 'Right':
        encoded_handedness = 1

    # Normalize landmarks
    normalized_lms = normalize_landmarks(landmarks, bbox)
    
    # Flatten normalized landmarks
    landmark_features = [item for sublist in normalized_lms for item in sublist]

    # Combine handedness and normalized landmarks
    features = [encoded_handedness] + landmark_features
    
    landmarks = np.array(features).reshape(1, -1)

    # Predict gesture
    gesture = model.predict(landmarks)

    return gesture
