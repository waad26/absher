import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="data/face_recognition.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create people table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                photo_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_person(self, name, photo_path):
        """Add a new person to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO people (name, photo_path)
            VALUES (?, ?)
        """, (name, photo_path))
        
        person_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return person_id
    
    def get_all_people(self):
        """Get all people from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, photo_path, created_at
            FROM people
            ORDER BY created_at DESC
        """)
        
        people = cursor.fetchall()
        conn.close()
        
        return people
    
    def delete_person(self, person_id):
        """Delete a person from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get photo path before deleting
        cursor.execute("SELECT photo_path FROM people WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        
        if result:
            photo_path = result[0]
            
            # Delete from database
            cursor.execute("DELETE FROM people WHERE id = ?", (person_id,))
            conn.commit()
            
            # Delete photo file
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        conn.close()
        return result is not None
    
    def get_person_by_id(self, person_id):
        """Get a specific person by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, photo_path, created_at
            FROM people
            WHERE id = ?
        """, (person_id,))
        
        person = cursor.fetchone()
        conn.close()
        
        return person
