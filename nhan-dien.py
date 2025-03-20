import time
import threading
import pygame
import cv2
import sqlite3
import os

# Khởi tạo pygame mixer
pygame.mixer.init()

def play_sound(file_path):
    """ Phát âm thanh nếu không có âm thanh nào đang phát """
    if os.path.exists(file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"🔊 Đang phát: {file_path}")
    else:
        print(f"⚠️ Lỗi: Không tìm thấy file âm thanh {file_path}")

# Load bộ nhận diện khuôn mặt
face_cascade = cv2.CascadeClassifier('khuonMat.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/face-trainner.yml")

def getProfile(Id):
    """ Lấy thông tin từ database """
    conn = sqlite3.connect("FaceBase.db")
    cursor = conn.execute("SELECT * FROM People WHERE ID=?", (Id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

# Khởi tạo camera
# camera_url = "http://172.16.12.24:8080/video"
# cap = cv2.VideoCapture(camera_url)
# cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_COMPLEX

# Biến theo dõi thời gian
last_known_id = None  # Lưu ID gần nhất
stop_greeting = False  # Dừng chào hỏi khi gặp unknown

def greeting_thread():
    """ Luồng chạy liên tục để phát âm thanh chào người quen mỗi 4 giây """
    global last_known_id, stop_greeting
    while True:
        if last_known_id and not stop_greeting:
            play_sound("_hello.mp3")
        time.sleep(4)

# Bắt đầu luồng phát âm thanh chào
threading.Thread(target=greeting_thread, daemon=True).start()

while True:
    ret, img = cap.read()
    if not ret:
        print("❌ Không thể lấy khung hình từ camera")
        break
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    found_known = False  # Biến kiểm tra có người quen không

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        
        nbr_predicted, conf = recognizer.predict(roi_gray)
        print(f"Nhận diện: ID={nbr_predicted}, Độ chính xác={conf}(Càng thấp càng chính xác)")

        if conf < 50:  # Nhận diện chính xác
            profile = getProfile(nbr_predicted)
            if profile:
                name = profile[1]
                cv2.putText(img, name, (x + 10, y), font, 1, (0, 255, 0), 1)
                
                last_known_id = nbr_predicted
                found_known = True  # Đánh dấu đã nhận diện người quen
                stop_greeting = False  # Cho phép phát âm thanh chào tiếp tục

        else:  # Người lạ
            cv2.putText(img, "Unknown", (x, y + h + 30), font, 0.6, (0, 0, 255), 2)
            
            # Nếu phát hiện người lạ, dừng phát âm thanh chào
            stop_greeting = True

            # Phát âm thanh cảnh báo mỗi 9 giây
            if time.time() - last_known_id >= 9:
                print("🚨 Phát âm thanh cảnh báo người lạ")
                play_sound("_alert.mp3")
                last_known_id = time.time()

    # Nếu không tìm thấy người quen trong khung hình, dừng phát âm thanh chào
    if not found_known:
        stop_greeting = True

    cv2.imshow('Nhận diện khuôn mặt', img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
