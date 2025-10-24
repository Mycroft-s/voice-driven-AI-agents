#!/usr/bin/env python3
"""
Database Management Tool
Provides utilities for managing the health assistant database
"""

import sys
import argparse
from data_manager import HealthDataManager

def show_stats():
    """Show database statistics"""
    data_manager = HealthDataManager()
    stats = data_manager.get_database_stats()
    
    print("=== Database Statistics ===")
    print(f"Total Users: {stats['total_users']}")
    print(f"User ID Range: {stats['user_id_range']['min']} - {stats['user_id_range']['max']}")
    print("\nRecord Counts:")
    for key, value in stats.items():
        if key.endswith('_count'):
            table_name = key.replace('_count', '')
            print(f"  {table_name}: {value}")

def cleanup_database():
    """Clean up orphaned data"""
    data_manager = HealthDataManager()
    print("Cleaning up orphaned data...")
    cleaned_count = data_manager.cleanup_orphaned_data()
    print(f"Cleaned {cleaned_count} orphaned records")

def list_users():
    """List all users"""
    data_manager = HealthDataManager()
    
    print("=== All Users ===")
    conn = data_manager.db_path
    import sqlite3
    conn = sqlite3.connect(data_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, email, created_at FROM users ORDER BY id')
    users = cursor.fetchall()
    
    for user in users:
        print(f"ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Created: {user[3]}")
    
    conn.close()

def create_user(name, email=None):
    """Create a new user"""
    data_manager = HealthDataManager()
    user_id = data_manager.get_or_create_user(name)
    print(f"User '{name}' created/found with ID: {user_id}")

def main():
    parser = argparse.ArgumentParser(description='Database Management Tool')
    parser.add_argument('command', choices=['stats', 'cleanup', 'list', 'create'], 
                       help='Command to execute')
    parser.add_argument('--name', help='User name for create command')
    parser.add_argument('--email', help='User email for create command')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        show_stats()
    elif args.command == 'cleanup':
        cleanup_database()
    elif args.command == 'list':
        list_users()
    elif args.command == 'create':
        if not args.name:
            print("Error: --name is required for create command")
            sys.exit(1)
        create_user(args.name, args.email)

if __name__ == "__main__":
    main()
