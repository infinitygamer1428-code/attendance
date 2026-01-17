import face_recognition
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os

# Load known faces
path = "dataset"
images = []
names = []

for file in os.listdir(path):
    img = face_recognition.load_image_file(f"{path}/{file}")
    images.append(img)
    names.append(os.path.splitext(file)[0])

# Encode faces
known_encodings = []
for img in images:
    encoding = face_recognition.face_encodings(img)[0]
    known_encodings.append(encoding)

# Create attendance file if not exists
if not os.path.exists("attendance.csv"):
    df = pd.DataFrame(columns=["Name", "Time"])
    df.to_csv("attendance.csv", index=False)

def mark_attendance(name):
    df = pd.read_csv("attendance.csv")
    if name not in df["Name"].values:
        time = datetime.now().strftime("%H:%M:%S")
        df.loc[len(df)] = [name, time]
        df.to_csv("attendance.csv", index=False)

# Start camera
cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, faces)

    for encoding, face in zip(encodings, faces):
        matches = face_recognition.compare_faces(known_encodings, encoding)
        face_dist = face_recognition.face_distance(known_encodings, encoding)
        match_index = np.argmin(face_dist)

        if matches[match_index]:
            name = names[match_index].upper()
            mark_attendance(name)
        else:
            name = "UNKNOWN"

        top, right, bottom, left = face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    cv2.imshow("Auto Attendance Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
