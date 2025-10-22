"""
Data Management Module
Handles storage and retrieval of health data
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class HealthDataManager:
    """Health Data Manager"""
    
    def __init__(self, db_path: str = "health_assistant.db"):
        self.db_path = db_path
        self.init_database()
        logger.info("Health data manager initialized successfully")
    
    def init_database(self):
        """Initialize database table structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User information table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                health_conditions TEXT,
                emergency_contact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Medication information table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                time_slots TEXT,
                start_date DATE,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Health records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                record_type TEXT NOT NULL,
                content TEXT,
                value REAL,
                unit TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                scheduled_time TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Doctor appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                doctor_name TEXT,
                department TEXT,
                appointment_time TIMESTAMP,
                reason TEXT,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, name: str, age: int = None, health_conditions: List[str] = None, 
                 emergency_contact: str = None) -> int:
        """Add user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (name, age, health_conditions, emergency_contact)
            VALUES (?, ?, ?, ?)
        ''', (name, age, json.dumps(health_conditions or []), emergency_contact))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added user: {name}, ID: {user_id}")
        return user_id
    
    def add_medication(self, user_id: int, name: str, dosage: str, frequency: str, 
                      time_slots: List[str], start_date: str = None, end_date: str = None) -> int:
        """Add medication information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO medications (user_id, name, dosage, frequency, time_slots, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, dosage, frequency, json.dumps(time_slots), start_date, end_date))
        
        med_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added medication: {name}, User ID: {user_id}")
        return med_id
    
    def add_health_record(self, user_id: int, record_type: str, content: str, 
                         value: float = None, unit: str = None) -> int:
        """Add health record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_records (user_id, record_type, content, value, unit)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, record_type, content, value, unit))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added health record: {record_type}, User ID: {user_id}")
        return record_id
    
    def add_reminder(self, user_id: int, reminder_type: str, title: str, 
                    content: str = None, scheduled_time: str = None) -> int:
        """Add reminder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, title, content, scheduled_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, reminder_type, title, content, scheduled_time))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added reminder: {title}, User ID: {user_id}")
        return reminder_id
    
    def get_user_medications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user medication information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM medications WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        medications = []
        for row in cursor.fetchall():
            medications.append({
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'dosage': row[3],
                'frequency': row[4],
                'time_slots': json.loads(row[5]) if row[5] else [],
                'start_date': row[6],
                'end_date': row[7],
                'is_active': bool(row[8])
            })
        
        conn.close()
        return medications
    
    def get_today_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get today's reminders"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE user_id = ? AND DATE(scheduled_time) = ? AND is_completed = 0
            ORDER BY scheduled_time
        ''', (user_id, today))
        
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'id': row[0],
                'user_id': row[1],
                'reminder_type': row[2],
                'title': row[3],
                'content': row[4],
                'scheduled_time': row[5],
                'is_completed': bool(row[6]),
                'created_at': row[7]
            })
        
        conn.close()
        return reminders
    
    def get_recent_health_records(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent health records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).date()
        cursor.execute('''
            SELECT * FROM health_records 
            WHERE user_id = ? AND DATE(timestamp) >= ?
            ORDER BY timestamp DESC
        ''', (user_id, start_date))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'user_id': row[1],
                'record_type': row[2],
                'content': row[3],
                'value': row[4],
                'unit': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        return records
    
    def complete_reminder(self, reminder_id: int):
        """Mark reminder as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reminders SET is_completed = 1 WHERE id = ?
        ''', (reminder_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Completed reminder: {reminder_id}")
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            profile = {
                'id': row[0],
                'name': row[1],
                'age': row[2],
                'health_conditions': json.loads(row[3]) if row[3] else [],
                'emergency_contact': row[4],
                'created_at': row[5]
            }
            conn.close()
            return profile
        
        conn.close()
        return None
