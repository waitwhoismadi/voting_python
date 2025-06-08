import sys
import os
import shutil
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def backup_database():
    db_path = 'voting_system.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'backups/voting_system_backup_{timestamp}.db'
    
    # Create backups directory if it doesn't exist
    os.makedirs('backups', exist_ok=True)
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Database backed up to: {backup_path}")
    print(f"📁 Backup size: {os.path.getsize(backup_path)} bytes")

if __name__ == '__main__':
    backup_database()
