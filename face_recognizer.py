import cv2
import numpy as np
import os
import pickle
from database import Database
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

class FaceRecognizer:
    def __init__(self):
        """Initialize face recognizer using OpenCV"""
        self.db = Database()
        
        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Create LBPH Face Recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load known faces
        self.known_face_ids = []
        self.known_face_names = {}
        self.is_trained = False
        
        self.load_known_faces()
    
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
                    # Load image robustly to handle Arabic file paths
                    # Read file as raw bytes
                    with open(photo_path, 'rb') as f:
                        file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                    # Decode image from bytes
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    
                    # Detect face
                    faces_detected = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30)
                    )
                    
                    if len(faces_detected) > 0:
                        # Use the first detected face
                        (x, y, w, h) = faces_detected[0]
                        face_roi = gray[y:y+h, x:x+w]
                        
                        # Resize to standard size
                        face_roi = cv2.resize(face_roi, (200, 200))
                        
                        faces.append(face_roi)
                        labels.append(person_id)
                        self.known_face_names[person_id] = name
                        
                        print(f"✓ تم تحميل وجه: {name}")
                    else:
                        print(f"✗ لم يتم العثور على وجه في صورة: {name}")
                        
                except Exception as e:
                    print(f"✗ خطأ في تحميل صورة {name}: {str(e)}")
        
        # Train the recognizer if we have faces
        if faces:
            self.recognizer.train(faces, np.array(labels))
            self.is_trained = True
            print(f"\n" + "="*60)
            print(f"✓ تم تدريب النظام على {len(faces)} وجه مسجل")
            print(f"✓ النظام جاهز للتعرف على الوجوه!")
            print("="*60 + "\n")
        else:
            self.is_trained = False
            print("\n" + "="*60)
            print("⚠ لا توجد وجوه صالحة للتدريب")
            print("📌 ارفعي صورة واضحة للوجه من الموقع")
            print("="*60 + "\n")
    
    def draw_arabic_text(self, frame, text, position, color):
        """
        Draw Arabic text on frame using PIL
        """
        try:
            # Convert frame to PIL Image
            frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(frame_pil)
            
            # Try to use Arial font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Reshape and reverse Arabic text for proper display
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            
            # Get text size
            bbox = draw.textbbox((0, 0), bidi_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x, y = position
            
            # Draw background rectangle
            bg_color = tuple(reversed(color))  # BGR to RGB
            draw.rectangle(
                [(x, y), (x + text_width + 12, y + text_height + 12)],
                fill=bg_color
            )
            
            # Draw text
            draw.text((x + 6, y + 6), bidi_text, font=font, fill=(255, 255, 255))
            
            # Convert back to OpenCV format
            frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            # Fallback to English text if Arabic fails
            print(f"Error drawing Arabic text: {e}")
            cv2.rectangle(frame, (position[0], position[1]), (position[0]+150, position[1]+35), color, cv2.FILLED)
            cv2.putText(frame, text, (position[0]+6, position[1]+25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def recognize_faces_in_frame(self, frame):
        """
        Recognize faces in a video frame
        Returns: frame with boxes and names drawn
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        for (x, y, w, h) in faces:
            # Extract face ROI
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            name = "غير معروف"
            confidence = 0
            
            # Recognize face if trained
            if self.is_trained:
                try:
                    label, conf = self.recognizer.predict(face_roi)
                    
                    # Lower confidence value means better match
                    # Threshold: 100 (more lenient for better recognition)
                    if conf < 100:
                        name = self.known_face_names.get(label, "غير معروف")
                        confidence = 100 - conf
                        print(f"✓ تم التعرف على: {name} (ثقة: {conf:.1f})")
                    
                except Exception as e:
                    print(f"خطأ في التعرف: {str(e)}")
            
            # Draw rectangle around face
            color = (0, 255, 0) if name != "غير معروف" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            # Draw label with Arabic support using PIL
            frame = self.draw_arabic_text(frame, name, (x, y-40), color)
        
        return frame
    
    def add_person_from_image(self, name, image_path):
        """
        Add a new person from an image file
        Returns: (success, message)
        """
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                return False, "الملف غير موجود"
            
            # Load image robustly to handle Arabic file paths
            # Read file as raw bytes
            with open(image_path, 'rb') as f:
                file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
            # Decode image from bytes
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                return False, "فشل في قراءة الصورة"
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return False, "لم يتم العثور على وجه في الصورة"
            
            if len(faces) > 1:
                return False, "تم العثور على أكثر من وجه في الصورة. الرجاء استخدام صورة تحتوي على وجه واحد فقط"
            
            # Save image to data/photos (use UUID to avoid Arabic encoding issues)
            import shutil
            from datetime import datetime
            import uuid
            
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{unique_id}.jpg"
            save_path = os.path.join("data/photos", filename)
            
            # Copy the image if it's not already in the correct location
            if os.path.abspath(image_path) != os.path.abspath(save_path):
                shutil.copy(image_path, save_path)
            
            # Add to database
            person_id = self.db.add_person(name, save_path)
            
            # Reload and retrain
            self.load_known_faces()
            
            return True, f"تم إضافة {name} بنجاح"
            
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def delete_person(self, person_id):
        """Delete a person by ID"""
        success = self.db.delete_person(person_id)
        if success:
            self.load_known_faces()
        return success
