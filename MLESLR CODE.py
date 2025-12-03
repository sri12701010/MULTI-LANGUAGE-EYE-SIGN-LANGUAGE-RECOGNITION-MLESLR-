import threading
import webbrowser
import server  # Import  server script
import cv2
import mediapipe as mp
import time
import numpy as np
from collections import deque
from deep_translator import GoogleTranslator

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
translator = GoogleTranslator()

# Function to translate text
def translate_text(text, lang):
    if text:
        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(text)
            return translated
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Fallback to English if translation fails
    return ""

# Language selection menu 
def choose_language():
    print("Choose a language:")
    print("1. English")
    print("2. Telugu")
    print("3. Hindi")
    choice = input("Enter choice (1/2/3): ")
    if choice == "1":
        return "en"
    elif choice == "2":
        return "te"
    elif choice == "3":
        return "hi"
    else:
        print("Invalid choice, defaulting to English.")
        return "en"

selected_language = choose_language()
print(f"Selected Language: {selected_language}")
# Replace with your actual laptop's IP address
#webbrowser.open(f"http://192.168.1.166:5000/?lang={selected_language}")


# Eye aspect ratio calculation for blink detection
def eye_aspect_ratio(eye_landmarks, facial_landmarks):
    left = np.linalg.norm(np.array(facial_landmarks[eye_landmarks[1]]) - np.array(facial_landmarks[eye_landmarks[5]]))
    right = np.linalg.norm(np.array(facial_landmarks[eye_landmarks[2]]) - np.array(facial_landmarks[eye_landmarks[4]]))
    center = np.linalg.norm(np.array(facial_landmarks[eye_landmarks[0]]) - np.array(facial_landmarks[eye_landmarks[3]]))
    return (left + right) / (2.0 * center)

# Define eye landmark indexes
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Blink pattern mappings
BLINK_PATTERNS = {
    "1": "Yes",
    "2": "No",
    "3": "I’m okay",
    "4": "I’m not okay",
    "1-2": "Thank you",
    "2-1": "I’m sorry",
    "1-1-2": "I need a hug",
    "2-2-1": "Let’s talk",
    "1-1-1": "I want to go home",
    "2-2-2": "Call doctor"
}

# Capture video
cap = cv2.VideoCapture(0)
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

blink_sequence = deque(maxlen=3)
time_ref = time.time()
eyes_closed_start = None
last_message_time = time.time()
BLINK_THRESHOLD = 0.2  # Adjust based on calibration
CLOSE_EYES_EXIT_TIME = 5.0  # Exit if eyes are closed for 5 seconds
blink_count = 0
blinking = False
#change
threading.Thread(target=server.run_server, daemon=True).start()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            facial_landmarks = {i: (lm.x, lm.y) for i, lm in enumerate(face_landmarks.landmark)}
            left_ear = eye_aspect_ratio(LEFT_EYE, facial_landmarks)
            right_ear = eye_aspect_ratio(RIGHT_EYE, facial_landmarks)
            ear = (left_ear + right_ear) / 2.0
            
            if ear < BLINK_THRESHOLD:
                if not blinking:
                    blink_count += 1
                    blinking = True
                if eyes_closed_start is None:
                    eyes_closed_start = time.time()
                elif time.time() - eyes_closed_start >= CLOSE_EYES_EXIT_TIME:
                    print("Eyes closed for 5 seconds. Exiting program.")
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()
            else:
                blinking = False
                eyes_closed_start = None
                
            if time.time() - time_ref > 1.5:
                if blink_count > 0:
                    blink_sequence.append(str(blink_count))
                    #print(f"Detected blink sequence: {blink_sequence}")  # Debugging blink pattern detection
                blink_count = 0
                time_ref = time.time()
                
            pattern_str = "-".join(blink_sequence)
            detected_command = BLINK_PATTERNS.get(pattern_str, "")
            if detected_command:
                translated_command = translate_text(detected_command, selected_language)
                #change
                #print(f"Translated Output: {translated_command}")
                server.update_output(translated_command)
                cv2.putText(frame, f"Command: {translated_command}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                blink_sequence.clear()
            elif time.time() - last_message_time > 15:  # Show this message only every 15 seconds
                #print("No valid blink pattern detected yet. Keep trying.")
                last_message_time = time.time()
            
    cv2.imshow("Blink to Speak", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
