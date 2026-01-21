import face_recognition
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, date
import os

# ================= LOAD KNOWN FACES =================
path = "dataset"
images = []
names = []

for file in os.listdir(path):
    img = face_recognition.load_image_file(f"{path}/{file}")
    images.append(img)
    names.append(os.path.splitext(file)[0].upper())

# ================= ENCODE FACES =================
known_encodings = []
for img in images:
    encoding = face_recognition.face_encodings(img)[0]
    known_encodings.append(encoding)

# ================= CSV SETUP =================
FILE = "attendance.csv"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["Name", "Date", "Time"])
    df.to_csv(FILE, index=False)

# ================= MARK ATTENDANCE =================
def mark_attendance(name):
    df = pd.read_csv(FILE)

    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    # Prevent duplicate attendance (same person, same day)
    already_marked = (
        (df["Name"] == name) & (df["Date"] == today)
    ).any()

    if not already_marked:
        df.loc[len(df)] = [name, today, now]
        df.to_csv(FILE, index=False)

# ================= START CAMERA =================
cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, faces)

    for encoding, face in zip(encodings, faces):
        matches = face_recognition.compare_faces(known_encodings, encoding)
        face_dist = face_recognition.face_distance(known_encodings, encoding)
        match_index = np.argmin(face_dist)

        if matches[match_index]:
            name = names[match_index]
            mark_attendance(name)
        else:
            name = "UNKNOWN"

        top, right, bottom, left = face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(
            frame,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

    cv2.imshow("Auto Attendance Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
