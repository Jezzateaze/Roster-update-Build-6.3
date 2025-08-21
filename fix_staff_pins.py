#!/usr/bin/env python3
"""
Fix missing PIN data for staff users to populate login dropdown
"""

from pymongo import MongoClient
import os
import hashlib

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def hash_pin(pin):
    """Hash PIN for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()

def fix_staff_user_pins():
    """Add missing PIN data for staff users so they appear in login dropdown"""
    
    print("🔧 Fixing missing PIN data for staff users...")
    
    # Default PINs for staff users (in a real system, these would be set by admin)
    default_pins = {
        'rose': '888888',
        'angela': '111111', 
        'chanelle': '222222',
        'caroline': '333333',
        'nox': '444444',
        'elina': '555555',
        'kayla': '666666',
        'rhet': '777777',
        'nikita': '888888',
        'molly': '999999',
        'felicity': '111222',
        'issey': '222333',
        'haylee': '333444',
        'johnsmith': '123456',
        'alicejohnson': '654321'
    }
    
    # Get all users missing PIN data
    users_without_pins = list(db.users.find({'role': 'staff'}))
    
    print(f"Found {len(users_without_pins)} staff users to check...")
    
    updated_count = 0
    
    for user in users_without_pins:
        username = user.get('username', '')
        current_pin = user.get('pin')
        
        # Assign default PIN if missing
        if not current_pin and username in default_pins:
            new_pin = default_pins[username]
            pin_hash = hash_pin(new_pin)
            
            # Update user with PIN
            result = db.users.update_one(
                {'id': user['id']},
                {
                    '$set': {
                        'pin': new_pin,  # Store plain text for display (in production, would only store hash)
                        'pin_hash': pin_hash,  # Store hash for authentication
                        'is_active': True
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"  ✅ Updated {username} with PIN {new_pin}")
            else:
                print(f"  ❌ Failed to update {username}")
                
        elif current_pin:
            print(f"  ℹ️  {username} already has PIN")
        else:
            print(f"  ⚠️  {username} not in default PIN list")
    
    print(f"\n📊 Summary:")
    print(f"  - Staff users updated: {updated_count}")
    
    # Verify the fix
    users_with_pins = list(db.users.find({'role': 'staff', 'pin': {'$exists': True, '$ne': None}}))
    print(f"  - Staff users with PINs: {len(users_with_pins)}")
    
    # Show sample of fixed users
    print(f"\n👥 Staff users now available for login:")
    for user in users_with_pins[:10]:  # Show first 10
        print(f"  - {user.get('username')} (PIN: {user.get('pin')})")
    
    if len(users_with_pins) > 10:
        print(f"  ... and {len(users_with_pins) - 10} more")
    
    return updated_count > 0

def verify_admin_user():
    """Ensure Admin user has proper PIN"""
    print(f"\n🔍 Verifying Admin user...")
    
    admin_user = db.users.find_one({'username': 'Admin'})
    if admin_user:
        if not admin_user.get('pin'):
            # Add PIN to Admin user
            admin_pin = '0000'
            admin_pin_hash = hash_pin(admin_pin)
            
            db.users.update_one(
                {'username': 'Admin'},
                {
                    '$set': {
                        'pin': admin_pin,
                        'pin_hash': admin_pin_hash,
                        'is_active': True
                    }
                }
            )
            print(f"  ✅ Updated Admin user with PIN 0000")
        else:
            print(f"  ℹ️  Admin user already has PIN: {admin_user.get('pin')}")
    else:
        print(f"  ❌ Admin user not found")

if __name__ == "__main__":
    print("🔧 Fixing staff user login credentials...")
    print("=" * 50)
    
    verify_admin_user()
    success = fix_staff_user_pins()
    
    if success:
        print(f"\n✅ Staff user PINs fixed! Login dropdown should now show all staff users.")
    else:
        print(f"\n⚠️  No updates needed or some issues occurred.")
        
    print(f"\n🔄 Please refresh the frontend to see updated login dropdown.")