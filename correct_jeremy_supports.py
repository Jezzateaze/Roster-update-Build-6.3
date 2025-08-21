#!/usr/bin/env python3
"""
Script to correct Jeremy James Tomlinson's support provider information with the exact details provided by user
"""

from pymongo import MongoClient
import os
from datetime import datetime

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def correct_jeremy_supports():
    """Update Jeremy's support providers with the correct information as provided by user"""
    
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    # Correct support providers as specified by the user
    correct_supports = [
        {
            "description": "Personal care and daily living assistant Manager.",
            "provider": "Bountiful Care Services - Sarah Rogan +61 493 971 778",
            "frequency": "7 days per week",
            "type": "In-home support"
        },
        {
            "description": "Personal care and daily living assistant.",
            "provider": "BYOU Living Services - Nox Toakula 0423 550 272",
            "frequency": "2-3 days per week",
            "type": "In-home support"
        },
        {
            "description": "Clinical Nurse support from Bountiful Care",
            "provider": "Candice +61 433 431 560",
            "frequency": "Regularly (2-3 times a month)",
            "type": "Mainstream"
        },
        {
            "description": "GP support from Meadowlands Medical",
            "provider": "Dr Kim Zambelli 1300 746 447",
            "frequency": "Regularly (3-5 times per year)",
            "type": "Mainstream"
        },
        {
            "description": "Physiotherapy support",
            "provider": "Quest Physio - Julius Alpay (07) 30888035 julius@questphysio.com.au",
            "frequency": "Regularly (once a week)",
            "type": "Mainstream"
        },
        {
            "description": "Respiratory support",
            "provider": "Sleep Disorder Centre, PA Hospital - Sharon Kwiatkowski 07 3176 5161 / 07 3176 7096 / 0428 093 850 / 0461 562 707 Sharon.kwiatkowski@health.qld.gov.au",
            "frequency": "Regularly (3-5 times per year)",
            "type": "Mainstream"
        },
        {
            "description": "OT support",
            "provider": "Spinal life Australia - Yvette Farry +61 429 888 825 yfarry@spinal.com.au",
            "frequency": "Regularly (3-5 times per year)",
            "type": "Mainstream"
        },
        {
            "description": "Pet care support for Siana-Rose",
            "provider": "Healthy Plus - Greencross Vets Cannon Hill 07 3188 1507, Location: 1853-1881 Creek Road, Cannon Hill, QLD, 4170",
            "frequency": "As needed",
            "type": "Pet & Vet support"
        }
    ]
    
    # Update only the supports section while preserving other biography data
    result = db.clients.update_one(
        {"id": jeremy_id},
        {
            "$set": {
                "biography.supports": correct_supports,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count > 0:
        print("✅ Jeremy's support providers corrected successfully!")
        print(f"   - Updated {len(correct_supports)} support providers")
        print("   - Personal care providers: Bountiful Care (Sarah Rogan) & BYOU Living (Nox Toakula)")
        print("   - Medical providers: Candice (Clinical Nurse), Dr Kim Zambelli (GP)")
        print("   - Therapy providers: Julius Alpay (Physio), Sharon Kwiatkowski (Respiratory), Yvette Farry (OT)")
        print("   - Pet care: Greencross Vets Cannon Hill for Siana-Rose")
        return True
    else:
        print("❌ Failed to update Jeremy's support providers - client not found")
        return False

def verify_correction():
    """Verify the support provider correction"""
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    client_data = db.clients.find_one({"id": jeremy_id})
    if client_data and "biography" in client_data:
        supports = client_data["biography"].get("supports", [])
        print(f"\n📋 Support Provider Verification:")
        print(f"   ✅ Total support providers: {len(supports)}")
        
        for i, support in enumerate(supports, 1):
            print(f"   {i}. {support['description'][:50]}...")
            print(f"      Provider: {support['provider'][:60]}...")
            print(f"      Frequency: {support['frequency']}")
            print(f"      Type: {support['type']}")
        return True
    else:
        print("❌ Support provider data not found")
        return False

if __name__ == "__main__":
    print("🔄 Correcting Jeremy James Tomlinson's support provider information...")
    
    success = correct_jeremy_supports()
    if success:
        verify_correction()
    else:
        print("Correction failed. Please check the client ID and database connection.")