"""
Data Management Module
Handles storage and retrieval of health data
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

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
                email TEXT,
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
        
        # Chat conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                chat_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES chat_conversations (id)
            )
        ''')
        
        # 检查是否需要添加email字段（数据库迁移）
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'email' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
            logger.info("Added email column to users table")
        
        conn.commit()
        conn.close()
    
    def add_user(self, name: str, email: str = None, age: int = None, health_conditions: List[str] = None, 
                 emergency_contact: str = None) -> int:
        """Add user information with smart ID management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user already exists by name
        existing_user = self.get_user_by_name(name)
        if existing_user:
            logger.info(f"User {name} already exists with ID: {existing_user['id']}")
            conn.close()
            return existing_user['id']
        
        # Try to reuse deleted user IDs first
        cursor.execute('''
            SELECT id FROM users WHERE id NOT IN (
                SELECT DISTINCT user_id FROM medications WHERE user_id IS NOT NULL
                UNION
                SELECT DISTINCT user_id FROM health_records WHERE user_id IS NOT NULL
                UNION
                SELECT DISTINCT user_id FROM reminders WHERE user_id IS NOT NULL
                UNION
                SELECT DISTINCT user_id FROM appointments WHERE user_id IS NOT NULL
                UNION
                SELECT DISTINCT user_id FROM chat_conversations WHERE user_id IS NOT NULL
            ) ORDER BY id LIMIT 1
        ''')
        reusable_id = cursor.fetchone()
        
        if reusable_id:
            # Reuse an existing ID
            user_id = reusable_id[0]
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, name, email, age, health_conditions, emergency_contact)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, email, age, json.dumps(health_conditions or []), emergency_contact))
            logger.info(f"Reused user ID {user_id} for user: {name}")
        else:
            # Create new user with next available ID
            cursor.execute('''
                INSERT INTO users (name, email, age, health_conditions, emergency_contact)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, age, json.dumps(health_conditions or []), emergency_contact))
            user_id = cursor.lastrowid
            logger.info(f"Created new user: {name}, ID: {user_id}")
        
        conn.commit()
        conn.close()
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
                'created_at': row[5],
                'email': row[6]
            }
            conn.close()
            return profile
        
        conn.close()
        return None
    
    def get_or_create_user(self, user_identifier: str) -> int:
        """Get existing user or create new one based on identifier (name or ID)"""
        # First try to parse as integer (user ID)
        try:
            user_id = int(user_identifier)
            existing_user = self.get_user_profile(user_id)
            if existing_user:
                return user_id
        except ValueError:
            pass
        
        # Try to find by name
        existing_user = self.get_user_by_name(user_identifier)
        if existing_user:
            return existing_user['id']
        
        # Create new user with the identifier as name
        logger.info(f"Creating new user with identifier: {user_identifier}")
        return self.add_user(
            name=user_identifier,
            email=f"{user_identifier}@example.com",
            age=30,
            health_conditions=[],
            emergency_contact=""
        )
    
    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get user profile by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            profile = {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'age': row[3],
                'health_conditions': json.loads(row[4]) if row[4] else [],
                'emergency_contact': row[5],
                'created_at': row[6]
            }
            conn.close()
            return profile
        
        conn.close()
        return None
    
    # Chat conversation management methods
    def create_chat_conversation(self, user_id: int, chat_id: str, title: str) -> int:
        """Create a new chat conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_conversations (user_id, chat_id, title)
            VALUES (?, ?, ?)
        ''', (user_id, chat_id, title))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created chat conversation: {chat_id}, User: {user_id}")
        return conversation_id
    
    def get_chat_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all chat conversations for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, chat_id, title, created_at, updated_at
            FROM chat_conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row[0],
                'chat_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return conversations
    
    def cleanup_orphaned_data(self):
        """Clean up orphaned data from deleted users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all existing user IDs
        cursor.execute('SELECT id FROM users')
        existing_user_ids = {row[0] for row in cursor.fetchall()}
        
        if not existing_user_ids:
            logger.warning("No users found in database")
            conn.close()
            return
        
        # Clean up orphaned data in each table
        tables_to_clean = [
            'medications', 'health_records', 'reminders', 
            'appointments', 'chat_conversations', 'chat_messages'
        ]
        
        total_cleaned = 0
        for table in tables_to_clean:
            # Check if table has user_id column
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' in columns:
                # Delete records with non-existent user_ids
                placeholders = ','.join('?' * len(existing_user_ids))
                cursor.execute(f'''
                    DELETE FROM {table} 
                    WHERE user_id NOT IN ({placeholders})
                ''', list(existing_user_ids))
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    logger.info(f"Cleaned {deleted_count} orphaned records from {table}")
                    total_cleaned += deleted_count
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database cleanup completed. Total orphaned records removed: {total_cleaned}")
        return total_cleaned
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count users
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0]
        
        # Count records in each table
        tables = ['medications', 'health_records', 'reminders', 'appointments', 'chat_conversations', 'chat_messages']
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[f'{table}_count'] = 0
        
        # Get user ID range
        cursor.execute('SELECT MIN(id), MAX(id) FROM users')
        min_id, max_id = cursor.fetchone()
        stats['user_id_range'] = {'min': min_id, 'max': max_id}
        
        conn.close()
        return stats
    
    def update_chat_title(self, chat_id: str, new_title: str) -> bool:
        """Update chat conversation title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_conversations
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        ''', (new_title, chat_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Updated chat title: {chat_id} -> {new_title}")
        
        return updated
    
    def delete_chat_conversation(self, chat_id: str) -> bool:
        """Delete a chat conversation and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First delete all messages
        cursor.execute('DELETE FROM chat_messages WHERE chat_id = ?', (chat_id,))
        
        # Then delete the conversation
        cursor.execute('DELETE FROM chat_conversations WHERE chat_id = ?', (chat_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            logger.info(f"Deleted chat conversation: {chat_id}")
        
        return deleted
    
    def add_chat_message(self, chat_id: str, message_type: str, content: str) -> int:
        """Add a message to a chat conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get conversation_id
        cursor.execute('SELECT id FROM chat_conversations WHERE chat_id = ?', (chat_id,))
        conversation_row = cursor.fetchone()
        
        if not conversation_row:
            conn.close()
            raise ValueError(f"Chat conversation {chat_id} not found")
        
        conversation_id = conversation_row[0]
        
        # Insert message
        cursor.execute('''
            INSERT INTO chat_messages (conversation_id, chat_id, message_type, content)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, chat_id, message_type, content))
        
        message_id = cursor.lastrowid
        
        # Update conversation timestamp
        cursor.execute('''
            UPDATE chat_conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        ''', (chat_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added message to chat: {chat_id}")
        return message_id
    
    def get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a chat conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_type, content, timestamp
            FROM chat_messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
        ''', (chat_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'type': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages
