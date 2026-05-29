import face_recognition
import cv2

try:
    print("Sistem sedang membaca 'otak' wajah...")
    # Pastikan file dzacky.jpg ada di folder Proyek_CCTV
    image = face_recognition.load_image_file("dzacky.jpg")
    locations = face_recognition.face_locations(image)
    print(f"HASIL: Terdeteksi {len(locations)} wajah.")
    print("STATUS: AKHIRNYA BERHASIL! Library sudah aktif.")
except Exception as e:
    print(f"Masih ada kendala: {e}")