#!/usr/bin/env python3
"""
Script to update Jeremy James Tomlinson's client profile with comprehensive biography information
"""

from pymongo import MongoClient
import os
from datetime import datetime

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def update_jeremy_biography():
    """Update Jeremy's profile with comprehensive biography information"""
    
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    # Structure Jeremy's goals as provided by the user
    goals = [
        {
            "title": "Increase independence around the home",
            "description": "During this plan he would to like increase my level of independence around the home, including cooking so that I can have friends and family over more for dinner nights and entertain and be less reliant on support from others.",
            "how_to_achieve": "He can implement learnt skills and strategies to perform activities of daily living around the house."
        },
        {
            "title": "Develop daily living skills for independent living",
            "description": "In this plan period he would like to develop his daily living skills so that he can continue to live safely and independently in a house of his own.",
            "how_to_achieve": "He can continue to practice learnt independent living skills to support transition to independent living with his support staff and team. He can identify what supports would assist him to live independently."
        },
        {
            "title": "Increase mobility and social participation",
            "description": "During this plan he would like to increase his mobility and independence to get out of the house, so he can increase his social participation and see his family and friends.",
            "how_to_achieve": "He and his staff can identify activities that he would like to participate in within the community. He can access support from my staff to get out of the house more often."
        },
        {
            "title": "Complete education and find employment",
            "description": "In this plan period he would like to develop the physical capacity to work towards finishing his TAFE and Uni courses in diploma of photography and creative art and finishing of his degree in digital musical engineering so that he can look into employment opportunities in the future.",
            "how_to_achieve": "He can identify what supports he requires to finish his TAFE and Uni courses. He can search for employment opportunities that would be of interest to him."
        },
        {
            "title": "Get physiotherapy for pain management",
            "description": "He would like to get physiotherapy to manage his pain and movement and provide training to all carers.",
            "how_to_achieve": "His Support Coordinator will connect him with providers to source the supports he need to enable him to achieve his goal."
        },
        {
            "title": "Return to hydrotherapy",
            "description": "He would like to get back to hydrotherapy.",
            "how_to_achieve": "He will work collaboratively with and have guidance from a relevant allied health therapist, and support worker to assist him to get back to hydrotherapy"
        }
    ]
    
    # Structure Jeremy's support providers as provided
    supports = [
        {
            "description": "The GP, neurology, immunology, urology, respiratory, theatre surgical, speech pathology physiotherapist, clinical Nurse and OT team provide support for treatment and monitoring of my health and wellbeing.",
            "provider": "Mainstream",
            "frequency": "Weekly",
            "type": "Mainstream"
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
        }
    ]
    
    # Comprehensive biography information
    biography_data = {
        "strengths": "He likes to do gardening, crafts, cooking, photography, painting and gaming.",
        "living_arrangements": "His name is Jeremy James Tomlinson and he has recently moved out of his parents home into my his own apartment at 20/384 Stanley Rd, Carina 4152. It's a lovely 1 bedroom apartment, a little bit cluttered but has a very warm and inviting atmosphere filled with all his paintings displayed on the walls for everyone to enjoy. Close to Shops, Restaurants, Cafes and parks all in walking distance for staff to attend Jeremy in his Power wheelchair when he takes his Beautiful Fluffy Companion Dog Siana-Rose or (Cc for short) out for a run to burn her up all her energy for the night, She is a 2 year old Maltese female puppy princess, who can be very high maintenance at times, and always fully of energy she loves to play fetch with her toys with the Jeremy and his staff. Sometime Siana-Rose demands more time and attention then Jeremy actually does in a shift. but she always rewards all his staff with lots and lots of cuddles and she will always greet the staff at the door for cuddles when they start their shifts.",
        "daily_life": "Due to his movement abilities and lack of support he spends most of his day in his room, in bed watching TV or working his phone. He enjoy's cooking and when his not in pain he loves to spend as much time as he can with his family and his nieces and nephews when they're allowed over, either playing with them or watching them on the swings or going out on adventures days in the city or museums. He used to like to do gardening with them as well but unfortunately due to the lack of mobility he is unable to do so any more, he also loves to do lots of crafts and painting, and loves to teach people how to cook delicious new recipes for dinner and lots of baking and decorating cakes, cookies and desserts. He is also interested in going back to TAFE and Uni to continue his diploma of photography and creative art and finishing of his degree in digital musical engineering and looking for employment opportunities. He really enjoy's going fishing down at Manly pier and being on the water. He would love to get more adventurous and get out and to be pushed to do and try new things and do things he has not done for a while.",
        "goals": goals,
        "supports": supports,
        "additional_info": "Jeremy's goals are set by him and written in his own words. They help the people supporting him to know what he wants to work towards and the things that are important to him. His goals can be big or small, short term or long term, broad or specific. They can be about anything he wants to work towards. He can change or update his goals at any time."
    }
    
    # Update Jeremy's profile in the database
    result = db.clients.update_one(
        {"id": jeremy_id},
        {
            "$set": {
                "biography": biography_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count > 0:
        print("✅ Jeremy James Tomlinson's biography updated successfully!")
        print(f"   - Updated {len(goals)} goals")
        print(f"   - Updated {len(supports)} support providers")
        print("   - Updated strengths, living arrangements, and daily life information")
        return True
    else:
        print("❌ Failed to update Jeremy's biography - client not found")
        return False

def verify_update():
    """Verify the biography update was successful"""
    jeremy_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"
    
    client_data = db.clients.find_one({"id": jeremy_id})
    if client_data and "biography" in client_data:
        bio = client_data["biography"]
        print("\n📋 Biography Update Verification:")
        print(f"   ✅ Strengths: {len(bio.get('strengths', ''))} characters")
        print(f"   ✅ Living arrangements: {len(bio.get('living_arrangements', ''))} characters")
        print(f"   ✅ Daily life: {len(bio.get('daily_life', ''))} characters")
        print(f"   ✅ Goals: {len(bio.get('goals', []))} goals")
        print(f"   ✅ Supports: {len(bio.get('supports', []))} support providers")
        print(f"   ✅ Additional info: {len(bio.get('additional_info', ''))} characters")
        return True
    else:
        print("❌ Biography data not found in client profile")
        return False

if __name__ == "__main__":
    print("🔄 Updating Jeremy James Tomlinson's biography...")
    
    success = update_jeremy_biography()
    if success:
        verify_update()
    else:
        print("Update failed. Please check the client ID and database connection.")