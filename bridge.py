#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bridge between HTML form and Python camera app
Saves uploaded image and launches camera recognition
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
from datetime import datetime
import subprocess
import sys

app = Flask(__name__)
CORS(app)

# Ensure data directory exists
os.makedirs("data/photos", exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    """
    Receive report data including photo
    Save photo and launch camera recognition
    """
    try:
        data = request.json
        
        # Get person data
        name = data.get('name', 'Unknown')
        photo_data = data.get('photo', '')
        
        if not photo_data:
            return jsonify({'success': False, 'error': 'لم يتم رفع صورة'}), 400
        
        # Decode base64 image
        if ',' in photo_data:
            photo_data = photo_data.split(',')[1]
        
        image_bytes = base64.b64decode(photo_data)
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join("data/photos", filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        print(f"✓ تم حفظ صورة: {filepath}")
        
        # Add person to database using face_recognizer
        from face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        success, message = recognizer.add_person_from_image(name, filepath)
        
        if not success:
            return jsonify({'success': False, 'error': message}), 400
        
        print(f"✓ تم إضافة الشخص: {name}")
        
        # Launch camera recognition in a new process
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['python', 'camera_recognition.py'], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['python3', 'camera_recognition.py'])
            
            print("✓ تم تشغيل نظام التعرف على الوجوه")
        except Exception as e:
            print(f"تحذير: فشل في تشغيل الكاميرا تلقائياً: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال البلاغ بنجاح وتشغيل نظام التعرف على الوجوه',
            'name': name
        })
        
    except Exception as e:
        print(f"خطأ: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 تشغيل خادم منصة أبشر...")
    print("=" * 60)
    print("📍 افتح المتصفح على: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')
