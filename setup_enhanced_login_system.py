#!/usr/bin/env python3
"""
Setup enhanced login system with default PINs and user management
"""

from pymongo import MongoClient
import os
import hashlib
from datetime import datetime

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def hash_pin(pin):
    """Hash PIN for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()

def setup_enhanced_login_system():
    """Setup enhanced login system with new default PINs"""
    
    print("🔧 Setting up enhanced login system...")
    
    # Default PINs as requested
    ADMIN_DEFAULT_PIN = "1234"
    STAFF_DEFAULT_PIN = "888888"
    
    # Update Admin user
    print("\n👑 Updating Admin user...")
    admin_user = db.users.find_one({"username": "Admin"})
    
    if admin_user:
        admin_pin_hash = hash_pin(ADMIN_DEFAULT_PIN)
        
        result = db.users.update_one(
            {"username": "Admin"},
            {"$set": {
                "pin": ADMIN_DEFAULT_PIN,
                "pin_hash": admin_pin_hash,
                "is_first_login": True,  # Force PIN change on first login
                "role": "admin",
                "is_active": True,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            print(f"   ✅ Admin user updated with default PIN: {ADMIN_DEFAULT_PIN}")
        else:
            print("   ℹ️  Admin user already up to date")
    else:
        # Create Admin user if not exists
        new_admin = {
            "id": "admin-enhanced-login",
            "username": "Admin",
            "pin": ADMIN_DEFAULT_PIN,
            "pin_hash": hash_pin(ADMIN_DEFAULT_PIN),
            "role": "admin",
            "email": "admin@workcare.com",
            "first_name": "System",
            "last_name": "Administrator",
            "phone": "0490821919",
            "address": "System Address",
            "is_first_login": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db.users.insert_one(new_admin)
        print(f"   ✅ Created new Admin user with default PIN: {ADMIN_DEFAULT_PIN}")
    
    # Update all Staff users
    print(f"\n👥 Updating Staff users with default PIN: {STAFF_DEFAULT_PIN}...")
    
    # Get all staff users
    staff_users = list(db.users.find({"role": "staff"}))
    print(f"Found {len(staff_users)} staff users")
    
    updated_count = 0
    for staff in staff_users:
        staff_pin_hash = hash_pin(STAFF_DEFAULT_PIN)
        
        result = db.users.update_one(
            {"id": staff["id"]},
            {"$set": {
                "pin": STAFF_DEFAULT_PIN,
                "pin_hash": staff_pin_hash,
                "is_first_login": True,  # Force PIN change on first login
                "is_active": True,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            print(f"   ✅ Updated {staff.get('username', 'Unknown')} with default PIN")
    
    print(f"\n📊 Summary:")
    print(f"   - Admin users: 1 (PIN: {ADMIN_DEFAULT_PIN})")
    print(f"   - Staff users updated: {updated_count} (PIN: {STAFF_DEFAULT_PIN})")
    
    # Verify the setup
    print(f"\n🔍 Verification:")
    
    # Check Admin
    admin = db.users.find_one({"username": "Admin"})
    if admin and admin.get("pin") == ADMIN_DEFAULT_PIN:
        print(f"   ✅ Admin user ready: {admin.get('username')} (PIN: {admin.get('pin')})")
    else:
        print(f"   ❌ Admin user setup failed")
    
    # Check sample staff users
    sample_staff = list(db.users.find({"role": "staff"}).limit(3))
    for staff in sample_staff:
        if staff.get("pin") == STAFF_DEFAULT_PIN:
            print(f"   ✅ Staff user ready: {staff.get('username')} (PIN: {staff.get('pin')})")
        else:
            print(f"   ❌ Staff user {staff.get('username')} has incorrect PIN: {staff.get('pin')}")
    
    return True

def display_login_info():
    """Display login information for users"""
    
    print(f"\n🔐 Enhanced Login System Setup Complete!")
    print(f"=" * 60)
    
    print(f"\n👑 ADMIN LOGIN:")
    print(f"   Username: Admin")
    print(f"   Default PIN: 1234")
    print(f"   Note: Must change PIN on first login")
    
    print(f"\n👥 STAFF LOGIN:")
    print(f"   Default PIN for all staff: 888888")
    print(f"   Note: Must change PIN on first login")
    
    print(f"\n📱 LOGIN FEATURES:")
    print(f"   ✅ User dropdown selection")
    print(f"   ✅ iPhone-style numerical keypad")
    print(f"   ✅ Forced PIN change on first login")
    print(f"   ✅ Choice between 4-digit or 6-digit PIN")
    print(f"   ✅ Admin can reset staff PINs to default")
    
    # Show sample staff users
    print(f"\n👥 Available Staff Users:")
    staff_users = list(db.users.find({"role": "staff"}, {"username": 1, "pin": 1}).limit(10))
    for i, staff in enumerate(staff_users, 1):
        print(f"   {i:2}. {staff.get('username')} (PIN: {staff.get('pin')})")
    
    if len(staff_users) > 10:
        print(f"   ... and {len(staff_users) - 10} more staff users")

if __name__ == "__main__":
    success = setup_enhanced_login_system()
    if success:
        display_login_info()
        print(f"\n🚀 Enhanced login system is ready!")
        print(f"   Restart the frontend to see the new login interface.")
    else:
        print(f"\n❌ Setup failed")