# =============================================
# AI VERIFIKASI WAJAH - SISTEM KEAMANAN RUANGAN
# Tkinter + OpenCV + Face Recognition
# =============================================
# Fitur:
# - Kamera CCTV simulasi
# - Deteksi wajah dikenal / tidak dikenal
# - Simpan wajah tidak dikenal
# - Kirim notifikasi Telegram
# - GUI Tkinter
# =============================================

# Install dependency dulu:
# pip install opencv-python
# pip install face-recognition
# pip install pillow
# pip install numpy
# pip install requests

import tkinter as tk
from tkinter import Label, Button
import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageTk
import os
import requests
from datetime import datetime

# =============================
# KONFIGURASI
# =============================

TELEGRAM_TOKEN = "ISI_TOKEN_BOT_KAMU"
TELEGRAM_CHAT_ID = "ISI_CHAT_ID_KAMU"

KNOWN_FACES_DIR = "known_faces"
UNKNOWN_FACES_DIR = "unknown_faces"

# Buat folder jika belum ada
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(UNKNOWN_FACES_DIR, exist_ok=True)

# =============================
# LOAD WAJAH TERDAFTAR
# =============================

known_face_encodings = []
known_face_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    image = face_recognition.load_image_file(f"{KNOWN_FACES_DIR}/{filename}")
    encoding = face_recognition.face_encodings(image)
    
    if len(encoding) > 0:
        known_face_encodings.append(encoding[0])
        known_face_names.append(os.path.splitext(filename)[0])

print("Wajah terdaftar:", known_face_names)

# =============================
# TELEGRAM NOTIFIKASI
# =============================

def send_telegram(image_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    with open(image_path, 'rb') as image:
        requests.post(url, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': '⚠️ Wajah Tidak Dikenal Terdeteksi!'
        }, files={'photo': image})

# =============================
# TKINTER APP
# =============================

class FaceSecurityApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Sistem Keamanan Ruangan - AI Face Recognition")
        self.window.geometry("900x600")

        self.label = Label(window)
        self.label.pack()

        self.start_btn = Button(window, text="Start Kamera", command=self.start_camera)
        self.start_btn.pack()

        self.stop_btn = Button(window, text="Stop Kamera", command=self.stop_camera)
        self.stop_btn.pack()

        self.running = False
        self.cap = None

    # =========================
    # START CAMERA
    # =========================

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.update()

    # =========================
    # STOP CAMERA
    # =========================

    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()

    # =========================
    # UPDATE FRAME
    # =========================

    def update(self):
        if self.running:
            ret, frame = self.cap.read()

            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"

                    if True in matches:
                        match_index = matches.index(True)
                        name = known_face_names[match_index]
                    else:
                        # SIMPAN WAJAH TIDAK DIKENAL
                        now = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{UNKNOWN_FACES_DIR}/unknown_{now}.jpg"
                        
                        face_image = frame[top:bottom, left:right]
                        cv2.imwrite(filename, face_image)

                        # Kirim Telegram
                        send_telegram(filename)

                    # DRAW BOX
                    cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                    cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

                # TAMPILKAN DI TKINTER
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk
                self.label.configure(image=imgtk)

            self.window.after(10, self.update)

# =============================
# MAIN
# =============================

root = tk.Tk()
app = FaceSecurityApp(root)
root.mainloop()

# =============================================
# CARA PAKAI
# =============================================
# 1. Buat folder 'known_faces'
# 2. Masukkan foto wajah terdaftar
#    contoh:
#    known_faces/
#    - budi.jpg
#    - admin.jpg
#
# 3. Jalankan program
# 4. Jika wajah tidak dikenal:
#    - foto tersimpan
#    - notifikasi telegram terkirim
# =============================================
