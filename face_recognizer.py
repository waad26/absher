import cv2
import numpy as np
import os
import pickle
from database import Database
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import uuid
import shutil


class FaceRecognizer:
    def __init__(self):
        """Initialize face recognizer using OpenCV"""
        self.db = Database()

        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Create LBPH Face Recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()

        # Known faces
        self.known_face_ids = []
        self.known_face_names = {}
        self.is_trained = False

        self.load_known_faces()

    # -----------------------------------------------------
    # تحميل الصور وتدريب النظام
    # -----------------------------------------------------
    def load_known_faces(self):
        """Load all known faces from database and train the recognizer"""
        self.known_face_ids = []
        self.known_face_names = {}

        people = self.db.get_all_people()

        if not people:
            print("لا توجد وجوه مسجلة")
            self.is_trained = False
            return

        faces = []
        labels = []

        for person in people:
            person_id, name, photo_path, created_at = person

            if os.path.exists(photo_path):
                try:
                    with open(photo_path, 'rb') as f:
                        file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)

                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if image is None:
                        print(f"✗ فشل فتح الصورة: {photo_path}")
                        continue

                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    faces_detected = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30)
                    )

                    if len(faces_detected) > 0:
                        (x, y, w, h) = faces_detected[0]
                        face_roi = gray[y:y + h, x:x + w]
                        face_roi = cv2.resize(face_roi, (200, 200))

                        faces.append(face_roi)
                        labels.append(person_id)
                        self.known_face_names[person_id] = name

                        print(f"✓ تم تحميل وجه: {name}")
                    else:
                        print(f"✗ لا يوجد وجه في الصورة: {name}")

                except Exception as e:
                    print(f"✗ خطأ في تحميل {name}: {str(e)}")

        if faces:
            self.recognizer.train(faces, np.array(labels))
            self.is_trained = True
            print("\n" + "=" * 60)
            print(f"✓ تم تدريب النظام على {len(faces)} وجه")
            print("=" * 60 + "\n")
        else:
            self.is_trained = False
            print("\n⚠ لا توجد وجوه صالحة للتدريب")

    # -----------------------------------------------------
    # كتابة نص عربي على الفيديو باستخدام PIL
    # -----------------------------------------------------
    def draw_arabic_text(self, frame, text, position, color):
        try:
            frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(frame_pil)

            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)

            bbox = draw.textbbox((0, 0), bidi_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x, y = position
            bg_color = tuple(reversed(color))

            draw.rectangle(
                [(x, y), (x + text_width + 12, y + text_height + 12)],
                fill=bg_color
            )

            draw.text((x + 6, y + 6), bidi_text, font=font, fill=(255, 255, 255))

            frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
            return frame

        except Exception:
            cv2.putText(frame, text, (position[0], position[1]), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2)
            return frame

    # -----------------------------------------------------
    # التعرف على الوجوه
    # -----------------------------------------------------
    def recognize_faces_in_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(30, 30)
        )

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            face_roi = cv2.resize(face_roi, (200, 200))

            name = "غير معروف"
            confidence = 0

            if self.is_trained:
                try:
                    label, conf = self.recognizer.predict(face_roi)

                    if conf < 100:
                        name = self.known_face_names.get(label, "غير معروف")
                        confidence = 100 - conf
                        print(f"✓ تم التعرف على: {name} (ثقة: {conf:.1f})")

                except Exception as e:
                    print(f"خطأ في التعرف: {str(e)}")

            color = (0, 255, 0) if name != "غير معروف" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            frame = self.draw_arabic_text(frame, name, (x, y - 40), color)

        return frame

    # -----------------------------------------------------
    # إضافة شخص جديد
    # -----------------------------------------------------
    def add_person_from_image(self, name, image_path):
        try:
            if not os.path.exists(image_path):
                return False, "الملف غير موجود"

            with open(image_path, 'rb') as f:
                file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)

            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if image is None:
                return False, "فشل قراءة الصورة"

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=8,
                minSize=(30, 30)
            )

            if len(faces) == 0:
                return False, "لم يتم العثور على وجه"

            if len(faces) > 1:
                return False, "الصورة تحتوي على أكثر من وجه"

            unique_id = str(uuid.uuid4())[:8] + ".jpg"
            save_path = os.path.join("data/photos", unique_id)

            shutil.copy(image_path, save_path)

            person_id = self.db.add_person(name, save_path)

            self.load_known_faces()
            return True, f"تم إضافة {name} بنجاح"

        except Exception as e:
            return False, f"خطأ: {str(e)}"

    # -----------------------------------------------------
    # حذف شخص
    # -----------------------------------------------------
    def delete_person(self, person_id):
        success = self.db.delete_person(person_id)
        if success:
            self.load_known_faces()
        return success
