from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, time, timedelta
import os
import uuid
from enum import Enum

# Database setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shift_roster_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="Shift Roster & Pay Calculator")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class PayMode(str, Enum):
    DEFAULT = "default"
    SCHADS = "schads"

class ShiftType(str, Enum):
    WEEKDAY_DAY = "weekday_day"
    WEEKDAY_EVENING = "weekday_evening"
    WEEKDAY_NIGHT = "weekday_night"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    PUBLIC_HOLIDAY = "public_holiday"
    SLEEPOVER = "sleepover"

# Pydantic models
class Staff(BaseModel):
    id: str
    name: str
    active: bool = True
    created_at: datetime = None

class ShiftTemplate(BaseModel):
    id: str
    name: str
    start_time: str
    end_time: str
    is_sleepover: bool = False
    day_of_week: int  # 0=Monday, 6=Sunday

class RosterEntry(BaseModel):
    id: str
    date: str  # YYYY-MM-DD
    shift_template_id: str
    staff_id: Optional[str] = None
    staff_name: Optional[str] = None
    start_time: str
    end_time: str
    is_sleepover: bool = False
    is_public_holiday: bool = False
    manual_shift_type: Optional[str] = None  # Manual override for shift type
    manual_hourly_rate: Optional[float] = None  # Manual override for hourly rate
    manual_sleepover: Optional[bool] = None  # Manual override for sleepover status
    wake_hours: Optional[float] = None  # Additional wake hours beyond 2 hours
    hours_worked: float = 0.0
    base_pay: float = 0.0
    sleepover_allowance: float = 0.0
    total_pay: float = 0.0

class Settings(BaseModel):
    pay_mode: PayMode = PayMode.DEFAULT
    rates: Dict[str, float] = {
        "weekday_day": 42.00,
        "weekday_evening": 44.50,
        "weekday_night": 48.50,
        "saturday": 57.50,
        "sunday": 74.00,
        "public_holiday": 88.50,
        "sleepover_default": 175.00,
        "sleepover_schads": 60.02
    }

class RosterTemplate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = None
    is_active: bool = True
    template_data: Dict[str, List[Dict]] = {}  # day_of_week (as string) -> list of shift templates

class DayTemplate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    day_of_week: int  # 0=Monday, 6=Sunday
    shifts: List[Dict] = []  # List of shift data (times, sleepover status)
    created_at: datetime = None
    is_active: bool = True

# Pay calculation functions
def determine_shift_type(date_str: str, start_time: str, end_time: str, is_public_holiday: bool) -> ShiftType:
    """Determine the shift type based on date and time - SIMPLIFIED LOGIC"""
    
    if is_public_holiday:
        return ShiftType.PUBLIC_HOLIDAY
    
    # Parse date and get day of week
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    day_of_week = date_obj.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    
    # Weekend rates override time-based logic
    if day_of_week == 5:  # Saturday
        return ShiftType.SATURDAY
    elif day_of_week == 6:  # Sunday
        return ShiftType.SUNDAY
    
    # For weekdays (Monday-Friday), check time ranges
    start_hour = int(start_time.split(":")[0])
    start_min = int(start_time.split(":")[1])
    end_hour = int(end_time.split(":")[0])
    end_min = int(end_time.split(":")[1])
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    # Handle overnight shifts
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60
    
    # Simple time-based classification for weekdays
    # Night: starts before 6am OR ends after midnight
    if start_hour < 6 or end_minutes > 24 * 60:
        return ShiftType.WEEKDAY_NIGHT
    # Evening: starts at 8pm or later OR extends past 8pm
    elif start_hour >= 20 or end_minutes >= 20 * 60:
        return ShiftType.WEEKDAY_EVENING
    # Day: everything else (6am-8pm range)
    else:
        return ShiftType.WEEKDAY_DAY

def calculate_hours_worked(start_time: str, end_time: str) -> float:
    """Calculate hours worked between start and end time"""
    start_hour, start_min = map(int, start_time.split(":"))
    end_hour, end_min = map(int, end_time.split(":"))
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    # Handle overnight shifts
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60
    
    total_minutes = end_minutes - start_minutes
    return total_minutes / 60.0

def check_shift_overlap(date_str: str, start_time: str, end_time: str, exclude_id: Optional[str] = None) -> bool:
    """Check if a shift overlaps with existing shifts on the same date"""
    existing_shifts = list(db.roster.find({"date": date_str}))
    
    if exclude_id:
        existing_shifts = [s for s in existing_shifts if s.get("id") != exclude_id]
    
    if not existing_shifts:
        return False
    
    # Convert times to minutes for comparison
    def time_to_minutes(time_str: str) -> int:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    new_start = time_to_minutes(start_time)
    new_end = time_to_minutes(end_time)
    
    # Handle overnight shift
    if new_end <= new_start:
        new_end += 24 * 60
    
    for shift in existing_shifts:
        existing_start = time_to_minutes(shift["start_time"])
        existing_end = time_to_minutes(shift["end_time"])
        
        # Handle overnight shift
        if existing_end <= existing_start:
            existing_end += 24 * 60
        
        # Check for overlap
        if (new_start < existing_end and new_end > existing_start):
            return True
    
    return False

def calculate_pay(roster_entry: RosterEntry, settings: Settings) -> RosterEntry:
    """Calculate pay for a roster entry with sleepover logic"""
    hours = calculate_hours_worked(roster_entry.start_time, roster_entry.end_time)
    roster_entry.hours_worked = hours
    
    # Determine if this is a sleepover shift
    is_sleepover = roster_entry.manual_sleepover if roster_entry.manual_sleepover is not None else roster_entry.is_sleepover
    
    if is_sleepover:
        # Sleepover calculation: $175 flat rate includes 2 hours
        roster_entry.sleepover_allowance = 175.00  # Fixed $175 per night
        
        # Additional wake hours beyond 2 hours at applicable hourly rate
        wake_hours = roster_entry.wake_hours if roster_entry.wake_hours else 0
        extra_wake_hours = max(0, wake_hours - 2) if wake_hours > 2 else 0
        
        if extra_wake_hours > 0:
            # Get applicable hourly rate for extra wake time
            if roster_entry.manual_hourly_rate:
                hourly_rate = roster_entry.manual_hourly_rate
            else:
                # Determine rate based on shift type or manual override
                if roster_entry.manual_shift_type:
                    shift_type_map = {
                        "weekday_day": ShiftType.WEEKDAY_DAY,
                        "weekday_evening": ShiftType.WEEKDAY_EVENING,
                        "weekday_night": ShiftType.WEEKDAY_NIGHT,
                        "saturday": ShiftType.SATURDAY,
                        "sunday": ShiftType.SUNDAY,
                        "public_holiday": ShiftType.PUBLIC_HOLIDAY
                    }
                    shift_type = shift_type_map.get(roster_entry.manual_shift_type, ShiftType.WEEKDAY_DAY)
                else:
                    shift_type = determine_shift_type(
                        roster_entry.date, 
                        roster_entry.start_time, 
                        roster_entry.end_time,
                        roster_entry.is_public_holiday
                    )
                
                # Get hourly rate based on shift type
                if shift_type == ShiftType.PUBLIC_HOLIDAY:
                    hourly_rate = settings.rates["public_holiday"]
                elif shift_type == ShiftType.SATURDAY:
                    hourly_rate = settings.rates["saturday"]
                elif shift_type == ShiftType.SUNDAY:
                    hourly_rate = settings.rates["sunday"]
                elif shift_type == ShiftType.WEEKDAY_EVENING:
                    hourly_rate = settings.rates["weekday_evening"]
                elif shift_type == ShiftType.WEEKDAY_NIGHT:
                    hourly_rate = settings.rates["weekday_night"]
                else:
                    hourly_rate = settings.rates["weekday_day"]
            
            roster_entry.base_pay = extra_wake_hours * hourly_rate
        else:
            roster_entry.base_pay = 0  # Only sleepover allowance
            
    else:
        # Regular shift calculation
        roster_entry.sleepover_allowance = 0
        
        # Use manual hourly rate if provided
        if roster_entry.manual_hourly_rate:
            hourly_rate = roster_entry.manual_hourly_rate
        else:
            # Use manual shift type if provided, otherwise determine automatically
            if roster_entry.manual_shift_type:
                shift_type_map = {
                    "weekday_day": ShiftType.WEEKDAY_DAY,
                    "weekday_evening": ShiftType.WEEKDAY_EVENING,
                    "weekday_night": ShiftType.WEEKDAY_NIGHT,
                    "saturday": ShiftType.SATURDAY,
                    "sunday": ShiftType.SUNDAY,
                    "public_holiday": ShiftType.PUBLIC_HOLIDAY
                }
                shift_type = shift_type_map.get(roster_entry.manual_shift_type, ShiftType.WEEKDAY_DAY)
            else:
                # Determine shift type automatically
                shift_type = determine_shift_type(
                    roster_entry.date, 
                    roster_entry.start_time, 
                    roster_entry.end_time,
                    roster_entry.is_public_holiday
                )
            
            # Get hourly rate based on shift type
            if shift_type == ShiftType.PUBLIC_HOLIDAY:
                hourly_rate = settings.rates["public_holiday"]
            elif shift_type == ShiftType.SATURDAY:
                hourly_rate = settings.rates["saturday"]
            elif shift_type == ShiftType.SUNDAY:
                hourly_rate = settings.rates["sunday"]
            elif shift_type == ShiftType.WEEKDAY_EVENING:
                hourly_rate = settings.rates["weekday_evening"]
            elif shift_type == ShiftType.WEEKDAY_NIGHT:
                hourly_rate = settings.rates["weekday_night"]
            else:
                hourly_rate = settings.rates["weekday_day"]
        
        roster_entry.base_pay = hours * hourly_rate
    
    roster_entry.total_pay = roster_entry.base_pay + roster_entry.sleepover_allowance
    return roster_entry

# Initialize default data
def initialize_default_data():
    """Initialize default staff and shift templates"""
    
    # Default staff members
    default_staff = [
        "Angela", "Chanelle", "Rose", "Caroline", "Nox", "Elina",
        "Kayla", "Rhet", "Nikita", "Molly", "Felicity", "Issey"
    ]
    
    for staff_name in default_staff:
        existing = db.staff.find_one({"name": staff_name})
        if not existing:
            staff = Staff(
                id=str(uuid.uuid4()),
                name=staff_name,
                active=True,
                created_at=datetime.now()
            )
            db.staff.insert_one(staff.dict())
    
    # Clear existing shift templates and create new ones per user requirements
    db.shift_templates.delete_many({})
    
    # Updated shift templates according to user specifications
    shift_templates = [
        # Monday
        {"name": "Monday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 0},  # Weekday Day
        {"name": "Monday Shift 2", "start_time": "15:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 0},  # Weekday Day  
        {"name": "Monday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 0},  # Weekday Evening
        {"name": "Monday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 0},   # Sleepover
        
        # Tuesday
        {"name": "Tuesday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 1},  # Weekday Day
        {"name": "Tuesday Shift 2", "start_time": "12:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 1},  # Weekday Day
        {"name": "Tuesday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 1},  # Weekday Evening
        {"name": "Tuesday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 1},   # Sleepover
        
        # Wednesday
        {"name": "Wednesday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 2},  # Weekday Day
        {"name": "Wednesday Shift 2", "start_time": "15:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 2},  # Weekday Day
        {"name": "Wednesday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 2},  # Weekday Evening
        {"name": "Wednesday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 2},   # Sleepover
        
        # Thursday
        {"name": "Thursday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 3},  # Weekday Day
        {"name": "Thursday Shift 2", "start_time": "12:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 3},  # Weekday Day
        {"name": "Thursday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 3},  # Weekday Evening
        {"name": "Thursday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 3},   # Sleepover
        
        # Friday
        {"name": "Friday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 4},  # Weekday Day
        {"name": "Friday Shift 2", "start_time": "15:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 4},  # Weekday Day
        {"name": "Friday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 4},  # Weekday Evening
        {"name": "Friday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 4},   # Sleepover
        
        # Saturday
        {"name": "Saturday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 5},  # Saturday Rate
        {"name": "Saturday Shift 2", "start_time": "15:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 5},  # Saturday Rate
        {"name": "Saturday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 5},  # Saturday Rate
        {"name": "Saturday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 5},   # Sleepover
        
        # Sunday
        {"name": "Sunday Shift 1", "start_time": "07:30", "end_time": "15:30", "is_sleepover": False, "day_of_week": 6},  # Sunday Rate
        {"name": "Sunday Shift 2", "start_time": "15:00", "end_time": "20:00", "is_sleepover": False, "day_of_week": 6},  # Sunday Rate
        {"name": "Sunday Shift 3", "start_time": "15:30", "end_time": "23:30", "is_sleepover": False, "day_of_week": 6},  # Sunday Rate
        {"name": "Sunday Shift 4", "start_time": "23:30", "end_time": "07:30", "is_sleepover": True, "day_of_week": 6},   # Sleepover
    ]
    
    for template_data in shift_templates:
        template = ShiftTemplate(
            id=str(uuid.uuid4()),
            **template_data
        )
        db.shift_templates.insert_one(template.dict())
    
    # Initialize default settings
    existing_settings = db.settings.find_one()
    if not existing_settings:
        settings = Settings()
        db.settings.insert_one(settings.dict())

# API Endpoints

@app.on_event("startup")
async def startup_event():
    initialize_default_data()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Staff endpoints
@app.get("/api/staff")
async def get_staff():
    staff_list = list(db.staff.find({"active": True}, {"_id": 0}))
    return staff_list

@app.post("/api/staff")
async def create_staff(staff: Staff):
    staff.id = str(uuid.uuid4())
    staff.created_at = datetime.now()
    db.staff.insert_one(staff.dict())
    return staff

@app.put("/api/staff/{staff_id}")
async def update_staff(staff_id: str, staff: Staff):
    result = db.staff.update_one({"id": staff_id}, {"$set": staff.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@app.delete("/api/staff/{staff_id}")
async def delete_staff(staff_id: str):
    result = db.staff.update_one({"id": staff_id}, {"$set": {"active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deactivated"}

# Shift template endpoints
@app.get("/api/shift-templates")
async def get_shift_templates():
    templates = list(db.shift_templates.find({}, {"_id": 0}))
    return templates

@app.post("/api/shift-templates")
async def create_shift_template(template: ShiftTemplate):
    template.id = str(uuid.uuid4())
    db.shift_templates.insert_one(template.dict())
    return template

@app.put("/api/shift-templates/{template_id}")
async def update_shift_template(template_id: str, template: ShiftTemplate):
    result = db.shift_templates.update_one({"id": template_id}, {"$set": template.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shift template not found")
    return template

# Day template endpoints
@app.get("/api/day-templates")
async def get_day_templates():
    """Get all day templates"""
    templates = list(db.day_templates.find({"is_active": True}, {"_id": 0}))
    return templates

@app.get("/api/day-templates/{day_of_week}")
async def get_day_templates_for_day(day_of_week: int):
    """Get day templates for a specific day of week"""
    templates = list(db.day_templates.find({"day_of_week": day_of_week, "is_active": True}, {"_id": 0}))
    return templates

@app.post("/api/day-templates")
async def create_day_template(template: DayTemplate):
    """Create a new day template"""
    template.id = str(uuid.uuid4())
    template.created_at = datetime.now()
    db.day_templates.insert_one(template.dict())
    return template

@app.post("/api/day-templates/save-day/{template_name}")
async def save_day_as_template(template_name: str, date: str):
    """Save all shifts from a specific date as a day template"""
    # Get all roster entries for the specific date
    roster_entries = list(db.roster.find({"date": date}, {"_id": 0}))
    
    if not roster_entries:
        raise HTTPException(status_code=404, detail=f"No shifts found for date {date}")
    
    # Get day of week from the date
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
    day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
    
    # Extract shift data (without staff assignments and date-specific info)
    shifts = []
    for entry in roster_entries:
        shift_data = {
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "is_sleepover": entry.get("is_sleepover", False)
        }
        shifts.append(shift_data)
    
    # Sort shifts by start time for consistency
    shifts.sort(key=lambda x: x["start_time"])
    
    # Create the day template
    day_template = DayTemplate(
        id=str(uuid.uuid4()),
        name=template_name,
        description=f"{day_name} template with {len(shifts)} shifts (from {date})",
        day_of_week=day_of_week,
        shifts=shifts,
        created_at=datetime.now()
    )
    
    db.day_templates.insert_one(day_template.dict())
    return day_template

@app.post("/api/day-templates/apply-to-date/{template_id}")
async def apply_day_template_to_date(template_id: str, target_date: str):
    """Apply a day template to a specific date"""
    # Get the day template
    template_doc = db.day_templates.find_one({"id": template_id, "is_active": True})
    if not template_doc:
        raise HTTPException(status_code=404, detail="Day template not found")
    
    template = DayTemplate(**template_doc)
    
    # Check if target date already has shifts
    existing_shifts = list(db.roster.find({"date": target_date}))
    if existing_shifts:
        # Check for overlaps
        overlaps = []
        for shift_data in template.shifts:
            if check_shift_overlap(target_date, shift_data["start_time"], shift_data["end_time"]):
                overlaps.append(f"{shift_data['start_time']}-{shift_data['end_time']}")
        
        if overlaps:
            raise HTTPException(
                status_code=409, 
                detail=f"Cannot apply template: overlaps detected with existing shifts at times: {', '.join(overlaps)}"
            )
    
    # Apply the template shifts to the target date
    entries_created = 0
    settings_doc = db.settings.find_one()
    settings = Settings(**settings_doc) if settings_doc else Settings()
    
    for shift_data in template.shifts:
        # Create roster entry
        entry = RosterEntry(
            id=str(uuid.uuid4()),
            date=target_date,
            shift_template_id=f"day-template-{template_id}",
            start_time=shift_data["start_time"],
            end_time=shift_data["end_time"],
            is_sleepover=shift_data.get("is_sleepover", False)
        )
        
        # Calculate pay
        entry = calculate_pay(entry, settings)
        
        db.roster.insert_one(entry.dict())
        entries_created += 1
    
    return {
        "message": f"Applied '{template.name}' to {target_date}",
        "entries_created": entries_created,
        "template_name": template.name
    }

@app.delete("/api/day-templates/{template_id}")
async def delete_day_template(template_id: str):
    """Delete a day template"""
    result = db.day_templates.update_one({"id": template_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Day template not found")
    return {"message": "Day template deleted"}

# Roster template endpoints
@app.get("/api/roster-templates")
async def get_roster_templates():
    """Get all roster templates"""
    templates = list(db.roster_templates.find({"is_active": True}, {"_id": 0}))
    return templates

@app.post("/api/roster-templates")
async def create_roster_template(template: RosterTemplate):
    """Create a new roster template"""
    template.id = str(uuid.uuid4())
    template.created_at = datetime.now()
    db.roster_templates.insert_one(template.dict())
    return template

@app.put("/api/roster-templates/{template_id}")
async def update_roster_template(template_id: str, template: RosterTemplate):
    """Update an existing roster template"""
    result = db.roster_templates.update_one({"id": template_id}, {"$set": template.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Roster template not found")
    return template

@app.delete("/api/roster-templates/{template_id}")
async def delete_roster_template(template_id: str):
    """Delete a roster template"""
    result = db.roster_templates.update_one({"id": template_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Roster template not found")
    return {"message": "Roster template deleted"}

@app.post("/api/roster-templates/save-current/{template_name}")
async def save_current_roster_as_template(template_name: str, month: str):
    """Save current month's roster as a template"""
    # Get all roster entries for the month
    roster_entries = list(db.roster.find({"date": {"$regex": f"^{month}"}}, {"_id": 0}))
    
    if not roster_entries:
        raise HTTPException(status_code=404, detail="No roster entries found for the specified month")
    
    # Group entries by day of week
    template_data = {}
    
    for entry in roster_entries:
        date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
        day_of_week = str(date_obj.weekday())  # Convert to string for MongoDB compatibility
        
        if day_of_week not in template_data:
            template_data[day_of_week] = []
        
        # Store the shift template info (without staff assignments and dates)
        shift_template = {
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "is_sleepover": entry.get("is_sleepover", False)
        }
        
        # Avoid duplicates by checking if this shift template already exists for this day
        if shift_template not in template_data[day_of_week]:
            template_data[day_of_week].append(shift_template)
    
    # Create the roster template
    roster_template = RosterTemplate(
        id=str(uuid.uuid4()),
        name=template_name,
        description=f"Template created from {month} roster",
        created_at=datetime.now(),
        template_data=template_data
    )
    
    db.roster_templates.insert_one(roster_template.dict())
    return roster_template

@app.post("/api/generate-roster-from-template/{template_id}/{month}")
async def generate_roster_from_template(template_id: str, month: str):
    """Generate roster entries for a month using a roster template"""
    # Get the roster template
    template_doc = db.roster_templates.find_one({"id": template_id, "is_active": True})
    if not template_doc:
        raise HTTPException(status_code=404, detail="Roster template not found")
    
    template = RosterTemplate(**template_doc)
    year, month_num = map(int, month.split("-"))
    
    # Generate entries for each day of the month
    from calendar import monthrange
    _, days_in_month = monthrange(year, month_num)
    
    entries_created = 0
    overlaps_detected = []
    
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month_num, day)
        date_str = date_obj.strftime("%Y-%m-%d")
        day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
        
        # Get shift templates for this day of week
        day_shifts = template.template_data.get(str(day_of_week), [])
        if not day_shifts:
            day_shifts = template.template_data.get(day_of_week, [])  # Try integer key
        
        for shift_data in day_shifts:
            # Check for overlaps before creating
            if check_shift_overlap(date_str, shift_data["start_time"], shift_data["end_time"]):
                overlaps_detected.append({
                    "date": date_str,
                    "start_time": shift_data["start_time"],
                    "end_time": shift_data["end_time"]
                })
                continue  # Skip overlapping shifts
            
            # Check if entry already exists
            existing = db.roster.find_one({
                "date": date_str,
                "start_time": shift_data["start_time"],
                "end_time": shift_data["end_time"]
            })
            
            if not existing:
                entry = RosterEntry(
                    id=str(uuid.uuid4()),
                    date=date_str,
                    shift_template_id=f"template-{template_id}-{day_of_week}",
                    start_time=shift_data["start_time"],
                    end_time=shift_data["end_time"],
                    is_sleepover=shift_data.get("is_sleepover", False)
                )
                
                # Calculate pay
                settings_doc = db.settings.find_one()
                settings = Settings(**settings_doc) if settings_doc else Settings()
                entry = calculate_pay(entry, settings)
                
                db.roster.insert_one(entry.dict())
                entries_created += 1
    
    result = {
        "message": f"Generated {entries_created} roster entries for {month} using template '{template.name}'",
        "entries_created": entries_created
    }
    
    if overlaps_detected:
        result["overlaps_detected"] = len(overlaps_detected)
        result["overlap_details"] = overlaps_detected[:5]  # Show first 5 overlaps
    
    return result

# Roster endpoints
@app.get("/api/roster")
async def get_roster(month: str):
    """Get roster for a specific month (YYYY-MM format)"""
    roster_entries = list(db.roster.find({"date": {"$regex": f"^{month}"}}, {"_id": 0}))
    return roster_entries

@app.post("/api/roster")
async def create_roster_entry(entry: RosterEntry):
    # Get current settings for pay calculation
    settings_doc = db.settings.find_one()
    settings = Settings(**settings_doc) if settings_doc else Settings()
    
    entry.id = str(uuid.uuid4())
    entry = calculate_pay(entry, settings)
    
    db.roster.insert_one(entry.dict())
    return entry

@app.put("/api/roster/{entry_id}")
async def update_roster_entry(entry_id: str, entry: RosterEntry):
    # Check for overlaps (excluding current entry)
    if check_shift_overlap(entry.date, entry.start_time, entry.end_time, exclude_id=entry_id):
        raise HTTPException(
            status_code=409, 
            detail=f"Updated shift would overlap with existing shift on {entry.date}"
        )
    
    # Get current settings for pay calculation
    settings_doc = db.settings.find_one()
    settings = Settings(**settings_doc) if settings_doc else Settings()
    
    entry = calculate_pay(entry, settings)
    
    result = db.roster.update_one({"id": entry_id}, {"$set": entry.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Roster entry not found")
    return entry

@app.delete("/api/roster/{entry_id}")
async def delete_roster_entry(entry_id: str):
    result = db.roster.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Roster entry not found")
    return {"message": "Roster entry deleted"}

# Settings endpoints
@app.get("/api/settings")
async def get_settings():
    settings_doc = db.settings.find_one({}, {"_id": 0})
    return settings_doc if settings_doc else Settings().dict()

@app.put("/api/settings")
async def update_settings(settings: Settings):
    db.settings.update_one({}, {"$set": settings.dict()}, upsert=True)
    return settings

# Generate monthly roster
@app.post("/api/generate-roster/{month}")
async def generate_monthly_roster(month: str):
    """Generate roster entries for a month based on shift templates"""
    year, month_num = map(int, month.split("-"))
    
    # Get shift templates
    templates = list(db.shift_templates.find())
    
    # Generate entries for each day of the month
    from calendar import monthrange
    _, days_in_month = monthrange(year, month_num)
    
    entries_created = 0
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month_num, day)
        date_str = date_obj.strftime("%Y-%m-%d")
        day_of_week = date_obj.weekday()  # 0=Monday
        
        # Find templates for this day of week
        day_templates = [t for t in templates if t["day_of_week"] == day_of_week]
        
        for template in day_templates:
            # Check if entry already exists
            existing = db.roster.find_one({
                "date": date_str,
                "shift_template_id": template["id"]
            })
            
            if not existing:
                entry = RosterEntry(
                    id=str(uuid.uuid4()),
                    date=date_str,
                    shift_template_id=template["id"],
                    start_time=template["start_time"],
                    end_time=template["end_time"],
                    is_sleepover=template["is_sleepover"]
                )
                
                # Calculate pay
                settings_doc = db.settings.find_one()
                settings = Settings(**settings_doc) if settings_doc else Settings()
                entry = calculate_pay(entry, settings)
                
                db.roster.insert_one(entry.dict())
                entries_created += 1
    
    return {"message": f"Generated {entries_created} roster entries for {month}"}

# Clear roster for a month
@app.delete("/api/roster/month/{month}")
async def clear_monthly_roster(month: str):
    """Clear all roster entries for a specific month"""
    result = db.roster.delete_many({"date": {"$regex": f"^{month}"}})
    return {"message": f"Deleted {result.deleted_count} roster entries for {month}"}

@app.post("/api/roster/add-shift")
async def add_individual_shift(entry: RosterEntry):
    """Add a single shift to the roster with overlap detection"""
    # Check for overlaps first
    if check_shift_overlap(entry.date, entry.start_time, entry.end_time):
        raise HTTPException(
            status_code=409, 
            detail=f"Shift overlaps with existing shift on {entry.date} from {entry.start_time} to {entry.end_time}"
        )
    
    # Get current settings for pay calculation
    settings_doc = db.settings.find_one()
    settings = Settings(**settings_doc) if settings_doc else Settings()
    
    entry.id = str(uuid.uuid4())
    entry = calculate_pay(entry, settings)
    
    db.roster.insert_one(entry.dict())
    return entry

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)