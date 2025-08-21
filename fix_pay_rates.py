#!/usr/bin/env python3
"""
Script to fix staff pay rates to the correct amounts as specified by user
"""

from pymongo import MongoClient
import os
from datetime import datetime

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def fix_pay_rates():
    """Update staff pay rates to correct amounts"""
    
    print('🔍 Current Staff Pay Rates:')
    settings = db.settings.find_one() or {}
    current_rates = settings.get('rates', {})
    for rate_type, amount in current_rates.items():
        print(f'   {rate_type}: ${amount}')
    
    print()
    print('📝 Updating to correct rates as specified by user...')
    
    # Correct rates as specified by the user
    correct_rates = {
        'weekday_day': 42.00,      # Weekday Day Rate (6am-8pm) - $42
        'weekday_evening': 44.50,  # Weekday Evening Rate (after 8pm) - $44.50
        'weekday_night': 48.50,    # Weekday Night Rate (overnight) - $48.50 (CORRECTED from $52)
        'saturday': 57.50,         # Saturday Rate (all hours) - $57.50
        'sunday': 74.00,          # Sunday Rate (all hours) - $74
        'public_holiday': 88.50,   # Public Holiday Rate (all hours) - $88.50
        'sleepover_default': 175.00,  # Sleepover Allowance (Default) - $175 (includes 2 hours wake time)
        'sleepover_schads': 286.56   # Keep existing SCHADS rate
    }
    
    # Update the rates in settings
    result = db.settings.update_one(
        {},
        {
            '$set': {
                'rates': correct_rates,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    
    print('✅ Staff pay rates updated successfully!')
    print()
    print('🎯 New Correct Rates:')
    print('   Weekday Day Rate (6am-8pm): $42.00')
    print('   Weekday Evening Rate (after 8pm): $44.50')
    print('   Weekday Night Rate (overnight): $48.50 ⭐ CORRECTED')
    print('   Saturday Rate (all hours): $57.50')
    print('   Sunday Rate (all hours): $74.00')
    print('   Public Holiday Rate (all hours): $88.50')
    print('   Sleepover Allowance (Default): $175.00 (includes 2 hours wake time)')
    print('   Sleepover SCHADS Rate: $286.56')
    
    return result.acknowledged

def verify_rates():
    """Verify the rates were updated correctly"""
    print('\n🔍 Verification - Updated Rates in Database:')
    settings = db.settings.find_one() or {}
    updated_rates = settings.get('rates', {})
    
    expected_rates = {
        'weekday_day': 42.00,
        'weekday_evening': 44.50,
        'weekday_night': 48.50,
        'saturday': 57.50,
        'sunday': 74.00,
        'public_holiday': 88.50,
        'sleepover_default': 175.00,
        'sleepover_schads': 286.56
    }
    
    all_correct = True
    for rate_type, expected_amount in expected_rates.items():
        actual_amount = updated_rates.get(rate_type, 0)
        status = "✅" if actual_amount == expected_amount else "❌"
        if actual_amount != expected_amount:
            all_correct = False
        print(f'   {status} {rate_type}: ${actual_amount} (expected ${expected_amount})')
    
    if all_correct:
        print('\n🎉 All pay rates are now correct!')
    else:
        print('\n⚠️  Some rates may need additional correction')
    
    return all_correct

if __name__ == "__main__":
    print("🔧 Fixing Staff Pay Rates to Correct Amounts...")
    print("=" * 60)
    
    success = fix_pay_rates()
    if success:
        verify_rates()
        print("\n🚀 Pay rates have been corrected and will be reflected in the Shift Times display!")
    else:
        print("❌ Failed to update pay rates")