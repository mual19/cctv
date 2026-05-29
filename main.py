import os
import sys
import cv2
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import numpy as np
from datetime import datetime
import face_recognition
import threading
import winsound

# --- KONFIGURASI PATH ---
base_dir = r"C:\Proyek_CCTV"
venv_site_packages = os.path.join(base_dir, "venv", "Lib", "site-packages")

if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

class SmartCCTV:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("900x750")
        self.window.configure(bg="#2c3e50")

        self.known_face_encodings = []
        self.known_face_names = []

        self.load_known_faces()

        # UI Components
        self.label_title = tk.Label(window, text="SISTEM KEAMANAN - FACE RECOGNITION",
                                    font=("Helvetica", 20, "bold"), bg="#2c3e50", fg="white", pady=20)
        self.label_title.pack()

        self.canvas = tk.Canvas(window, width=640, height=480, bg="black")
        self.canvas.pack(pady=10)

        self.status_var = tk.StringVar(value="Status: Monitoring Aktif")
        self.label_status = tk.Label(window, textvariable=self.status_var, font=("Helvetica", 12),
                                     bg="#2c3e50", fg="#ecf0f1")
        self.label_status.pack()

        self.btn_register = tk.Button(window, text="DAFTARKAN WAJAH", width=20, command=self.register_face,
                                      bg="#27ae60", fg="white", font=("Helvetica", 10, "bold"))
        self.btn_register.pack(pady=5)

        self.btn_quit = tk.Button(window, text="NONAKTIFKAN SISTEM", width=20, command=self.quit_app,
                                  bg="#e74c3c", fg="white", font=("Helvetica", 10, "bold"))
        self.btn_quit.pack(pady=20)

        self.vid = cv2.VideoCapture(0)
        self.alert_active = False
        
        # Jalankan loop update
        self.update()
        self.window.mainloop()

    def load_known_faces(self):
        known_path = "known_face"
        if not os.path.exists(known_path):
            os.makedirs(known_path)
            return

        # Membersihkan list lama sebelum reload
        self.known_face_encodings = []
        self.known_face_names = []

        for filename in os.listdir(known_path):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                path = os.path.join(known_path, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)

                if len(encodings) > 0:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(filename)[0])

    def register_face(self):
        ret, frame = self.vid.read()
        if not ret:
            messagebox.showerror("Error", "Kamera tidak tersedia")
            return

        name = simpledialog.askstring("Input", "Masukkan Nama Pemilik Wajah:")
        if not name:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) == 0:
            messagebox.showerror("Error", "Wajah tidak jelas. Pastikan pencahayaan cukup.")
            return

        # Simpan file dan update data encoding
        path = f"known_face/{name}.jpg"
        cv2.imwrite(path, frame)
        
        # Encoding wajah baru
        new_encoding = face_recognition.face_encodings(rgb_frame)[0]
        self.known_face_encodings.append(new_encoding)
        self.known_face_names.append(name)

        messagebox.showinfo("Sukses", f"Wajah {name} berhasil didaftarkan!")

    def alarm(self):
        # Bunyi beep singkat saat penyusup terdeteksi
        winsound.Beep(1000, 300)

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            # Optimasi: kecilkan gambar untuk pemrosesan AI yang lebih ringan
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            current_alert = False

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = "PENYUSUP"
                color = (0, 0, 255) # Default merah (B-G-R)
                confidence = 0

                if len(self.known_face_encodings) > 0:
                    # Menghitung jarak (distance). Semakin kecil = semakin mirip.
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    
                    # TOLERANSI: 0.45 (Angka ini membuat deteksi sangat ketat/akurat)
                    if face_distances[best_match_index] < 0.45:
                        name = self.known_face_names[best_match_index]
                        color = (0, 255, 0) # Hijau jika dikenal
                        confidence = round((1 - face_distances[best_match_index]) * 100, 1)
                    else:
                        current_alert = True
                else:
                    current_alert = True

                # Kembalikan skala koordinat ke ukuran asli (x4)
                top *= 4; right *= 4; bottom *= 4; left *= 4

                # Gambar kotak dan teks
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                label = f"{name} ({confidence}%)" if name != "PENYUSUP" else name
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Logika Alarm & Status
            if current_alert:
                self.status_var.set("⚠️ PERINGATAN: PENYUSUP TERDETEKSI!")
                self.label_status.config(fg="#e74c3c")
                if not self.alert_active: # Cegah spam thread
                    self.alert_active = True
                    threading.Thread(target=self.alarm, daemon=True).start()
                    # Reset alert active setelah jeda singkat
                    self.window.after(1000, self.reset_alert)
            else:
                self.status_var.set("Status: Monitoring Aktif (Aman)")
                self.label_status.config(fg="#2ecc71")

            # Tampilkan ke Canvas Tkinter
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(10, self.update)

    def reset_alert(self):
        self.alert_active = False

    def quit_app(self):
        self.vid.release()
        self.window.destroy()

if __name__ == "__main__":
    SmartCCTV(tk.Tk(), "Smart CCTV System - V1.0")