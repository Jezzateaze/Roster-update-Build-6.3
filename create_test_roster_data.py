#!/usr/bin/env python3
"""
Create test roster data for Rose in August 2025 for export functionality testing
"""

from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import uuid

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def create_august_2025_roster_data():
    """Create roster data for August 2025 for testing export functionality"""
    
    rose_id = 'dca1cc94-e541-4263-aa03-8f4188729adf'
    
    print("🔧 Creating August 2025 roster data for Rose...")
    
    # Check existing August 2025 data
    existing_count = db.roster.count_documents({
        'staff_id': rose_id,
        'date': {'$gte': '2025-08-01', '$lt': '2025-09-01'}
    })
    
    print(f"Existing August 2025 shifts for Rose: {existing_count}")
    
    # Create roster entries for August 2025
    august_dates = [
        '2025-08-01', '2025-08-02', '2025-08-05', '2025-08-06', '2025-08-07',
        '2025-08-08', '2025-08-09', '2025-08-12', '2025-08-13', '2025-08-14',
        '2025-08-15', '2025-08-16', '2025-08-19', '2025-08-20', '2025-08-21'
    ]
    
    shifts_created = 0
    shifts_updated = 0
    
    for date in august_dates:
        # Check if shift already exists for this date and time
        existing_shift = db.roster.find_one({
            'date': date,
            'start_time': '07:30'
        })
        
        if existing_shift:
            # Update existing shift to assign to Rose
            result = db.roster.update_one(
                {'_id': existing_shift['_id']},
                {'$set': {
                    'staff_id': rose_id,
                    'staff_name': 'Rose',
                    'hours_worked': 8.0,
                    'base_pay': 336.0,
                    'total_pay': 336.0,
                    'shift_type': 'weekday_day',
                    'client_name': 'Jeremy James Tomlinson',
                    'location': 'Client Home',
                    'notes': 'Regular day shift'
                }}
            )
            if result.modified_count > 0:
                shifts_updated += 1
                print(f"  ✅ Updated shift for {date}")
        else:
            # Create new shift
            new_shift = {
                'id': str(uuid.uuid4()),
                'date': date,
                'start_time': '07:30',
                'end_time': '15:30',
                'staff_id': rose_id,
                'staff_name': 'Rose',
                'hours_worked': 8.0,
                'base_pay': 336.0,
                'total_pay': 336.0,
                'shift_type': 'weekday_day',
                'is_sleepover': False,
                'client_name': 'Jeremy James Tomlinson',
                'location': 'Client Home',
                'notes': 'Regular day shift',
                'created_at': datetime.utcnow(),
                'hourly_rate': 42.0
            }
            
            db.roster.insert_one(new_shift)
            shifts_created += 1
            print(f"  ✅ Created shift for {date}")
    
    print(f"\n📊 Summary:")
    print(f"  - Shifts created: {shifts_created}")
    print(f"  - Shifts updated: {shifts_updated}")
    
    # Verify total August 2025 data for Rose
    final_count = db.roster.count_documents({
        'staff_id': rose_id,
        'date': {'$gte': '2025-08-01', '$lt': '2025-09-01'}
    })
    
    print(f"  - Total August 2025 shifts for Rose: {final_count}")
    
    if final_count > 0:
        print("\n🎉 Export functionality should now work for August 2025!")
        
        # Show sample data
        sample_shifts = list(db.roster.find(
            {'staff_id': rose_id, 'date': {'$gte': '2025-08-01', '$lt': '2025-09-01'}},
            {'_id': 0, 'date': 1, 'start_time': 1, 'hours_worked': 1, 'total_pay': 1}
        ).limit(5))
        
        print("\nSample August 2025 shifts for Rose:")
        for shift in sample_shifts:
            print(f"  - {shift['date']} at {shift['start_time']}: {shift['hours_worked']}h, ${shift['total_pay']}")
    
    return final_count > 0

if __name__ == "__main__":
    success = create_august_2025_roster_data()
    if success:
        print("\n✅ Test roster data created successfully!")
    else:
        print("\n❌ Failed to create test roster data")