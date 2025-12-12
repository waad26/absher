#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التعرف على الوجوه - منصة أبشر
يعمل تلقائياً بعد إضافة بلاغ الشخص المفقود
"""

import cv2
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import threading
from face_recognizer import FaceRecognizer
import sys
import os

class CameraRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("التعرف على الوجوه - منصة أبشر")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f4f4f4")
        
        # ألوان أبشر
        self.color_primary = "#1a7f37"  # أخضر أبشر
        self.color_secondary = "#f4f4f4"
        self.color_white = "#ffffff"
        
        # Initialize face recognizer
        try:
            self.recognizer = FaceRecognizer()
            print("✓ تم تحميل نظام التعرف على الوجوه")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل نظام التعرف: {str(e)}")
            sys.exit(1)
        
        # Camera variables
        self.camera = None
        self.camera_running = False
        self.camera_thread = None
        
        # Create UI
        self.create_ui()
        
        # Camera will be started by a button press
        
    def create_ui(self):
        """Create the user interface"""
        # Header
        header = tk.Frame(self.root, bg=self.color_primary, height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(
            header,
            text="🎥 التعرف على الوجوه - منصة أبشر",
            font=("Arial", 24, "bold"),
            bg=self.color_primary,
            fg="white"
        )
        title.pack(pady=20)
        
        # Create canvas with scrollbar
        canvas_container = tk.Frame(self.root, bg=self.color_secondary)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas
        self.canvas = tk.Canvas(
            canvas_container,
            bg=self.color_secondary,
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # Main content frame inside canvas
        main_frame = tk.Frame(self.canvas, bg=self.color_secondary)
        self.canvas_window = self.canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Configure scroll region
        def configure_scroll_region(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        main_frame.bind("<Configure>", configure_scroll_region)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            # event.delta is typically 120 or -120 on Windows
            # event.num is 4 or 5 on Linux/X11
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")
        
        # Bind to the root window for cross-platform compatibility
        self.root.bind_all("<MouseWheel>", on_mousewheel)
        self.root.bind_all("<Button-4>", on_mousewheel) # Linux scroll up
        self.root.bind_all("<Button-5>", on_mousewheel) # Linux scroll down
        
        # Adjust canvas window width
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        self.canvas.bind("<Configure>", on_canvas_configure)
        
        # Add padding
        content_wrapper = tk.Frame(main_frame, bg=self.color_secondary)
        content_wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Camera frame
        camera_container = tk.Frame(content_wrapper, bg=self.color_white, relief=tk.SOLID, bd=2)
        camera_container.pack(fill=tk.BOTH, expand=True)
        
        # Camera label
        self.camera_label = tk.Label(
            camera_container,
            bg="black",
            text="جاري تشغيل الكاميرا...",
            fg="white",
            font=("Arial", 16)
        )
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status label
        self.status_label = tk.Label(
            content_wrapper,
            text="⏳ جاري البحث عن الوجوه...",
            font=("Arial", 14),
            bg=self.color_secondary,
            fg=self.color_primary
        )
        self.status_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            content_wrapper,
            text="📌 انظر للكاميرا مباشرة • سيتم التعرف عليك تلقائياً",
            font=("Arial", 12),
            bg=self.color_secondary,
            fg="#666"
        )
        instructions.pack(pady=5)
        
        # Control buttons frame
        control_frame = tk.Frame(content_wrapper, bg=self.color_secondary)
        control_frame.pack(pady=10)
        
        # Start button
        start_btn = tk.Button(
            control_frame,
            text="▶ تشغيل الكاميرا",
            command=self.start_camera,
            font=("Arial", 14, "bold"),
            bg=self.color_primary,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        start_btn.pack(side=tk.LEFT, padx=10)
        
        # Stop button
        stop_btn = tk.Button(
            control_frame,
            text="■ إيقاف الكاميرا",
            command=self.stop_camera,
            font=("Arial", 14, "bold"),
            bg="#ffc107", # Yellow/Orange for stop
            fg="black",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(
            control_frame,
            text="✖ إغلاق",
            command=self.close_app,
            font=("Arial", 14, "bold"),
            bg="#dc3545",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        close_btn.pack(side=tk.LEFT, padx=10)
        
    def start_camera(self):
        """Start camera automatically with retry mechanism"""
        if self.camera_running:
            return
        
        # Release any existing camera first
        if self.camera is not None:
            try:
                self.camera.release()
                cv2.destroyAllWindows()
                threading.Event().wait(1)  # Wait 1 second
            except:
                pass
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"محاولة فتح الكاميرا ({attempt + 1}/{max_retries})...")
                
                # Try DirectShow first (Windows)
                self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                
                if not self.camera.isOpened():
                    self.camera.release()
                    threading.Event().wait(0.5)
                    # Fallback to default
                    self.camera = cv2.VideoCapture(0)
                
                # Add a small delay to allow the camera to warm up
                if self.camera.isOpened():
                    threading.Event().wait(1)
                
                if self.camera.isOpened():
                    # Test if we can actually read from camera
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None:
                        print("✓ تم فتح الكاميرا بنجاح!")
                        break
                    else:
                        print("✗ فشل في قراءة الكاميرا")
                        self.camera.release()
                        self.camera = None
                else:
                    print("✗ فشل في فتح الكاميرا")
                    self.camera = None
                
                if attempt < max_retries - 1:
                    threading.Event().wait(1)  # Wait before retry
                    
            except Exception as e:
                print(f"خطأ: {str(e)}")
                if self.camera:
                    self.camera.release()
                self.camera = None
                if attempt < max_retries - 1:
                    threading.Event().wait(1)
        
        if self.camera is None or not self.camera.isOpened():
            error_msg = "فشل في فتح الكاميرا بعد 3 محاولات.\n\nالحلول:\n1. أغلقي جميع البرامج التي تستخدم الكاميرا\n2. أعيدي تشغيل الكمبيوتر\n3. تأكدي من تشغيل الكاميرا في برنامج آخر"
            messagebox.showerror("خطأ", error_msg)
            self.status_label.config(text="✗ فشل في فتح الكاميرا", fg="red")
            self.camera_label.config(text="✗ فشل في فتح الكاميرا\n\nالرجاء إغلاق جميع البرامج التي تستخدم الكاميرا\nأو إعادة تشغيل الكمبيوتر")
            return
        
        # Camera opened successfully, configure it
        try:
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.camera_running = True
            self.status_label.config(text="✓ الكاميرا تعمل - جاري البحث عن الوجوه...")
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
            self.camera_thread.start()
            
            print("✓ تم تشغيل الكاميرا")
            
        except Exception as e:
            print(f"خطأ في تهيئة الكاميرا: {str(e)}")
            messagebox.showerror("خطأ", f"فشل في تشغيل الكاميرا: {str(e)}")
    
    def update_camera(self):
        """Update camera feed"""
        frame_count = 0
        error_count = 0
        max_errors = 10
        
        while self.camera_running:
            try:
                if self.camera is None or not self.camera.isOpened():
                    print("✗ الكاميرا مغلقة")
                    self.status_label.config(text="✗ الكاميرا مغلقة", fg="red")
                    break
                
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    error_count += 1
                    print(f"✗ فشل في قراءة إطار ({error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        print("✗ تجاوز عدد الأخطاء المسموح")
                        self.status_label.config(text="✗ فشل في قراءة الكاميرا", fg="red")
                        break
                    
                    threading.Event().wait(0.1)
                    continue
                
                # Reset error count on successful read
                if error_count > 0:
                    error_count = 0
                
                frame_count += 1
                if frame_count == 1:
                    print(f"✓ بدأ قراءة الإطارات بنجاح! (الحجم: {frame.shape})")
                
                # Recognize faces
                frame = self.recognizer.recognize_faces_in_frame(frame)
                
                # Convert to RGB for Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to fit window
                height, width = frame_rgb.shape[:2]
                max_width = 1160
                max_height = 600
                
                scale = min(max_width/width, max_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Convert to PhotoImage
                img = Image.fromarray(frame_resized)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update label
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk, text="")
                
                # Small delay
                threading.Event().wait(0.03)
                
            except Exception as e:
                error_count += 1
                print(f"خطأ في تحديث الكاميرا: {str(e)}")
                import traceback
                traceback.print_exc()
                
                if error_count >= max_errors:
                    print("✗ تجاوز عدد الأخطاء المسموح")
                    break
                
                threading.Event().wait(0.1)
        
        print("✗ تم إيقاف thread الكاميرا")
    
    def stop_camera(self):
        """Stop the camera feed and release resources"""
        if not self.camera_running:
            return
            
        print("جاري إيقاف الكاميرا...")
        
        # Stop camera thread
        self.camera_running = False
        
        # Wait for thread to finish
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2)
        
        # Release camera
        if self.camera:
            try:
                self.camera.release()
                self.camera = None
                print("✓ تم تحرير الكاميرا")
            except Exception as e:
                print(f"خطأ في تحرير الكاميرا: {e}")
        
        # Update UI
        self.camera_label.configure(image='', text="الكاميرا متوقفة")
        self.status_label.config(text="✗ الكاميرا متوقفة", fg="red")
        
        # Destroy all OpenCV windows
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
        print("✓ تم إيقاف الكاميرا")
    
    def close_app(self):
        """Close the application properly"""
        print("جاري إغلاق النظام...")
        
        self.stop_camera()
        
        # Unbind mousewheel before destroying
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except:
            pass
        
        # Destroy window
        try:
            self.root.quit()
            self.root.destroy()
            print("✓ تم إغلاق النظام بنجاح")
        except:
            pass

def main():
    root = tk.Tk()
    app = CameraRecognitionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()

if __name__ == "__main__":
    main()
