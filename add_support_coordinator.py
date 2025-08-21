#!/usr/bin/env python3
"""
Script to add Support Coordination support provider to Jeremy James Tomlinson's biography
"""

from pymongo import MongoClient
import os
from datetime import datetime

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def add_support_coordinator():
    """Add Support Coordination support provider to Jeremy's existing supports"""
    
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    # New support coordinator to add
    new_support = {
        "description": "Support coordination support from Spinal life Australia",
        "provider": "Ashleigh Smith +61 437 212 295 / 07 3435 3240 ajsmith@spinal.com.au",
        "frequency": "Regularly (3-5 times per month)",
        "type": "Support Coordinator"
    }
    
    # Add the new support to the existing supports array
    result = db.clients.update_one(
        {"id": jeremy_id},
        {
            "$push": {
                "biography.supports": new_support
            },
            "$set": {
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count > 0:
        print("✅ Support Coordinator added successfully!")
        print(f"   - Provider: Ashleigh Smith")
        print(f"   - Organization: Spinal life Australia")
        print(f"   - Contact: +61 437 212 295 / 07 3435 3240")
        print(f"   - Email: ajsmith@spinal.com.au")
        print(f"   - Frequency: Regularly (3-5 times per month)")
        print(f"   - Type: Support Coordinator")
        return True
    else:
        print("❌ Failed to add Support Coordinator - client not found")
        return False

def verify_addition():
    """Verify the support coordinator was added"""
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    client_data = db.clients.find_one({"id": jeremy_id})
    if client_data and "biography" in client_data:
        supports = client_data["biography"].get("supports", [])
        print(f"\n📋 Updated Support Provider List:")
        print(f"   ✅ Total support providers: {len(supports)}")
        
        for i, support in enumerate(supports, 1):
            print(f"   {i}. {support['description']}")
            print(f"      Provider: {support['provider'][:70]}{'...' if len(support['provider']) > 70 else ''}")
            print(f"      Frequency: {support['frequency']}")
            print(f"      Type: {support['type']}")
            print()
        
        # Specifically verify the new support coordinator
        support_coord = next((s for s in supports if s['type'] == 'Support Coordinator'), None)
        if support_coord:
            print("🎯 Support Coordinator Verification:")
            print(f"   ✅ Found: {support_coord['description']}")
            print(f"   ✅ Provider: {support_coord['provider']}")
            print(f"   ✅ Type: {support_coord['type']}")
        else:
            print("❌ Support Coordinator not found in the list")
        
        return True
    else:
        print("❌ Biography data not found")
        return False

if __name__ == "__main__":
    print("🔄 Adding Support Coordinator to Jeremy James Tomlinson's support providers...")
    
    success = add_support_coordinator()
    if success:
        verify_addition()
    else:
        print("Addition failed. Please check the client ID and database connection.")