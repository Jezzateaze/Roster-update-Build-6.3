from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, time, timedelta
import os
import uuid
import hashlib
import secrets
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

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    STAFF = "staff"

# Pydantic models
class Staff(BaseModel):
    id: Optional[str] = None
    name: str
    active: bool = True
    created_at: Optional[datetime] = None

class ShiftTemplate(BaseModel):
    id: str
    name: str
    start_time: str
    end_time: str
    is_sleepover: bool = False
    day_of_week: int  # 0=Monday, 6=Sunday
    manual_shift_type: Optional[str] = None  # Override automatic shift type detection
    manual_hourly_rate: Optional[float] = None  # Override automatic hourly rate calculation

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
    allow_overlap: Optional[bool] = False  # Allow this shift to overlap with others (for 2:1 shifts)

class Settings(BaseModel):
    pay_mode: PayMode = PayMode.DEFAULT
    timezone: str = "Australia/Brisbane"  # AEST UTC+10
    time_format: str = "24hr"  # "12hr" or "24hr"
    first_day_of_week: str = "monday"  # "monday" or "sunday"
    dark_mode: bool = False  # true or false
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

class CalendarEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    date: str  # YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM (optional for all-day events)
    end_time: Optional[str] = None    # HH:MM (optional for all-day events)
    is_all_day: bool = False
    event_type: str = "appointment"  # appointment, meeting, task, reminder, personal
    priority: str = "medium"  # low, medium, high, urgent
    location: Optional[str] = None
    attendees: List[str] = []  # List of attendee names
    reminder_minutes: Optional[int] = None  # Minutes before event to remind
    is_completed: bool = False  # For tasks
    created_at: datetime = None
    is_active: bool = True

# Authentication Models
class User(BaseModel):
    id: str
    username: str
    pin_hash: str  # Hashed PIN
    role: UserRole = UserRole.STAFF
    staff_id: Optional[str] = None  # Link to staff record for staff users
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD
    hire_date: Optional[str] = None      # YYYY-MM-DD
    hourly_rate: Optional[float] = None
    is_first_login: bool = True
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None

class LoginRequest(BaseModel):
    username: str
    pin: str

class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str

class ResetPinRequest(BaseModel):
    username: str
    email: str

class Session(BaseModel):
    id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

# New models for Shift & Staff Availability System
class AvailabilityType(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable" 
    TIME_OFF_REQUEST = "time_off_request"
    PREFERRED_SHIFTS = "preferred_shifts"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class NotificationType(str, Enum):
    SHIFT_REQUEST_APPROVED = "shift_request_approved"
    SHIFT_REQUEST_REJECTED = "shift_request_rejected"
    AVAILABILITY_CONFLICT = "availability_conflict"
    GENERAL = "general"

class ShiftRequest(BaseModel):
    id: Optional[str] = None
    roster_entry_id: str  # ID of the unassigned shift
    staff_id: str
    staff_name: str
    request_date: datetime
    status: RequestStatus = RequestStatus.PENDING
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

class StaffAvailability(BaseModel):
    id: Optional[str] = None
    staff_id: str
    staff_name: str
    availability_type: AvailabilityType
    date_from: Optional[str] = None  # YYYY-MM-DD for specific dates
    date_to: Optional[str] = None    # YYYY-MM-DD for date ranges
    day_of_week: Optional[int] = None  # 0-6 for recurring weekly availability
    start_time: Optional[str] = None   # HH:MM for time-specific availability
    end_time: Optional[str] = None     # HH:MM for time-specific availability
    is_recurring: bool = False         # Whether this applies every week
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    related_id: Optional[str] = None  # ID of related shift request, availability, etc.
    is_read: bool = False
    created_at: Optional[datetime] = None

# Authentication helper functions
def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA-256"""
    return hashlib.sha256(pin.encode()).hexdigest()

def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against its hash"""
    return hash_pin(pin) == pin_hash

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def create_admin_user():
    """Create the default admin user if it doesn't exist"""
    admin_user = db.users.find_one({"username": "Admin"})
    if not admin_user:
        admin_data = {
            "id": str(uuid.uuid4()),
            "username": "Admin",
            "pin_hash": hash_pin("0000"),  # Default PIN: 0000
            "role": "admin",
            "email": "jeremy.tomlinson88@gmail.com",
            "first_name": "Administrator",
            "is_first_login": True,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        db.users.insert_one(admin_data)
        print("✅ Admin user created with default PIN: 0000")

def send_reset_email(email: str, temp_pin: str):
    """Send password reset email (simplified version)"""
    # In a production environment, you would configure proper SMTP settings
    # For now, we'll just print the reset PIN to console
    print(f"🔐 RESET PIN for {email}: {temp_pin}")
    print("📧 In production, this would be sent via email")

# Initialize admin user on startup
create_admin_user()

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
    # Evening: starts at 8pm or later OR extends past 8pm (SCHADS: shifts ending AT 8pm are still Day shifts)
    elif start_hour >= 20 or end_minutes > 20 * 60:
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

def check_shift_overlap(date_str: str, start_time: str, end_time: str, exclude_id: Optional[str] = None, shift_name: Optional[str] = None) -> bool:
    """Check if a shift overlaps with existing shifts on the same date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        exclude_id: ID of shift to exclude from overlap check (for updates)
        shift_name: Name of the shift being checked (to allow 2:1 overlaps)
    
    Returns:
        True if overlap detected and should be prevented, False if overlap is allowed
    """
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
            # Check if either shift has "2:1" in the name - if so, allow overlap
            existing_shift_name = ""
            
            # Try to get shift name from template or roster entry
            if shift.get("shift_template_id"):
                template = db.shift_templates.find_one({"id": shift["shift_template_id"]})
                if template:
                    existing_shift_name = template.get("name", "")
            
            # Also check if the shift itself has a name field
            if not existing_shift_name and shift.get("name"):
                existing_shift_name = shift.get("name", "")
            
            # Check both current shift name and existing shift name for "2:1"
            current_has_2to1 = shift_name and "2:1" in shift_name.lower()
            existing_has_2to1 = "2:1" in existing_shift_name.lower()
            
            # Only allow overlap if BOTH shifts have "2:1" in their names
            # OR if the current shift being added/updated has "2:1" in its name
            if current_has_2to1:
                print(f"Allowing overlap for 2:1 shift - Current: {shift_name}, Existing: {existing_shift_name}")
                continue  # Allow this overlap because current shift is 2:1
            else:
                return True  # Prevent overlap - regular shifts cannot overlap with anything
    
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

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Get current authenticated user"""
    token = credentials.credentials
    session = db.sessions.find_one({"token": token, "is_active": True})
    
    if not session or session["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.users.find_one({"id": session["user_id"], "is_active": True})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

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
    # Sort staff alphabetically by name
    staff_list.sort(key=lambda staff: staff['name'].lower())
    return staff_list

@app.post("/api/staff")
async def create_staff(staff: Staff):
    """Create a new staff member"""
    if not staff.id:
        staff.id = str(uuid.uuid4())
    if not staff.created_at:
        staff.created_at = datetime.now()
    
    # Validate staff name is not empty
    if not staff.name or staff.name.strip() == "":
        raise HTTPException(status_code=422, detail="Staff name cannot be empty")
    
    # Check if staff name already exists
    existing_staff = db.staff.find_one({"name": staff.name, "active": True})
    if existing_staff:
        raise HTTPException(status_code=400, detail=f"Staff member with name '{staff.name}' already exists")
    
    try:
        db.staff.insert_one(staff.dict())
        return staff
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create staff member: {str(e)}")

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
    """Update a shift template with all fields including manual overrides"""
    result = db.shift_templates.update_one({"id": template_id}, {"$set": template.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shift template not found")
    return template

# Calendar events endpoints
@app.get("/api/calendar-events")
async def get_calendar_events(start_date: Optional[str] = None, end_date: Optional[str] = None, event_type: Optional[str] = None):
    """Get calendar events with optional filtering"""
    query = {"is_active": True}
    
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    if event_type:
        query["event_type"] = event_type
    
    events = list(db.calendar_events.find(query, {"_id": 0}))
    return events

@app.get("/api/calendar-events/{date}")
async def get_events_for_date(date: str):
    """Get all events for a specific date"""
    events = list(db.calendar_events.find({"date": date, "is_active": True}, {"_id": 0}))
    return events

@app.post("/api/calendar-events")
async def create_calendar_event(event: CalendarEvent):
    """Create a new calendar event"""
    event.id = str(uuid.uuid4())
    event.created_at = datetime.now()
    db.calendar_events.insert_one(event.dict())
    return event

@app.put("/api/calendar-events/{event_id}")
async def update_calendar_event(event_id: str, event: CalendarEvent):
    """Update an existing calendar event"""
    result = db.calendar_events.update_one({"id": event_id}, {"$set": event.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return event

@app.delete("/api/calendar-events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event"""
    result = db.calendar_events.update_one({"id": event_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return {"message": "Calendar event deleted"}

@app.put("/api/calendar-events/{event_id}/complete")
async def complete_task(event_id: str):
    """Mark a task as completed"""
    result = db.calendar_events.update_one(
        {"id": event_id, "event_type": "task"}, 
        {"$set": {"is_completed": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task marked as completed"}

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
    
    # Check if target date already has shifts and look for overlaps
    overlaps = []
    for shift_data in template.shifts:
        if check_shift_overlap(target_date, shift_data["start_time"], shift_data["end_time"], shift_name=template.name):
            overlaps.append(f"{shift_data['start_time']}-{shift_data['end_time']}")
    
    if overlaps:
        raise HTTPException(
            status_code=409, 
            detail=f"Cannot apply template: overlaps detected with existing shifts at times: {', '.join(overlaps)} (Note: 2:1 shifts are allowed to overlap)"
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

@app.post("/api/generate-roster-from-shift-templates/{month}")
async def generate_roster_from_shift_templates(month: str, templates_data: dict):
    """Generate roster for a month using the shift templates from Shift Times section"""
    year, month_num = map(int, month.split("-"))
    templates = templates_data.get("templates", [])
    
    if not templates:
        raise HTTPException(status_code=400, detail="No shift templates provided")
    
    # Generate entries for each day of the month using shift templates
    from calendar import monthrange
    _, days_in_month = monthrange(year, month_num)
    
    entries_created = 0
    overlaps_detected = []
    
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month_num, day)
        date_str = date_obj.strftime("%Y-%m-%d")
        day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
        
        # Get shift templates for this day of week
        day_templates = [t for t in templates if t.get("day_of_week") == day_of_week]
        
        for template in day_templates:
            template_name = template.get("name", "")
            
            # Check for overlaps (allows 2:1 shifts to overlap)
            if check_shift_overlap(date_str, template["start_time"], template["end_time"], shift_name=template_name):
                overlaps_detected.append({
                    "date": date_str,
                    "start_time": template["start_time"],
                    "end_time": template["end_time"],
                    "name": template_name
                })
                continue  # Skip overlapping shifts (unless they're 2:1)
            
            # Check if entry already exists
            existing = db.roster.find_one({
                "date": date_str,
                "start_time": template["start_time"],
                "end_time": template["end_time"]
            })
            
            if not existing:
                entry = RosterEntry(
                    id=str(uuid.uuid4()),
                    date=date_str,
                    shift_template_id=template.get("id", f"template-{day_of_week}"),
                    start_time=template["start_time"],
                    end_time=template["end_time"],
                    is_sleepover=template.get("is_sleepover", False),
                    manual_shift_type=template.get("manual_shift_type"),
                    manual_hourly_rate=template.get("manual_hourly_rate")
                )
                
                # Calculate pay using template overrides
                settings_doc = db.settings.find_one()
                settings = Settings(**settings_doc) if settings_doc else Settings()
                entry = calculate_pay(entry, settings)
                
                db.roster.insert_one(entry.dict())
                entries_created += 1
    
    result = {
        "message": f"Generated {entries_created} roster entries for {month} using Shift Times templates",
        "entries_created": entries_created
    }
    
    if overlaps_detected:
        result["overlaps_detected"] = len(overlaps_detected)
        result["overlap_details"] = overlaps_detected[:5]  # Show first 5 overlaps
        result["note"] = "Shifts with '2:1' in the name are allowed to overlap"
    
    return result

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
            # Get shift name from template if available
            shift_name = shift_data.get("name", template.name)
            
            # Check for overlaps (allows 2:1 shifts to overlap)
            if check_shift_overlap(date_str, shift_data["start_time"], shift_data["end_time"], shift_name=shift_name):
                overlaps_detected.append({
                    "date": date_str,
                    "start_time": shift_data["start_time"],
                    "end_time": shift_data["end_time"],
                    "name": shift_name
                })
                continue  # Skip overlapping shifts (unless they're 2:1)
            
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
        result["note"] = "Shifts with '2:1' in the name are allowed to overlap"
    
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
    # Get shift name from template if available
    shift_name = ""
    if entry.shift_template_id:
        template = db.shift_templates.find_one({"id": entry.shift_template_id})
        if template:
            shift_name = template.get("name", "")
    
    # Check for overlaps (excluding current entry, allows 2:1 shifts and manual override)
    if not entry.allow_overlap and check_shift_overlap(entry.date, entry.start_time, entry.end_time, exclude_id=entry_id, shift_name=shift_name):
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
    """Add a single shift to the roster with overlap detection (allows 2:1 shifts and manual override)"""
    # Get shift name from template if available
    shift_name = ""
    if entry.shift_template_id:
        template = db.shift_templates.find_one({"id": entry.shift_template_id})
        if template:
            shift_name = template.get("name", "")
    
    # Check for overlaps (allows 2:1 shifts to overlap, or if allow_overlap is explicitly set)
    if not entry.allow_overlap and check_shift_overlap(entry.date, entry.start_time, entry.end_time, shift_name=shift_name):
        raise HTTPException(
            status_code=409, 
            detail=f"Shift overlaps with existing shift on {entry.date} from {entry.start_time} to {entry.end_time}. Use 'Allow Overlap' option for 2:1 shifts."
        )
    
    # Get current settings for pay calculation
    settings_doc = db.settings.find_one()
    settings = Settings(**settings_doc) if settings_doc else Settings()
    
    entry.id = str(uuid.uuid4())
    entry = calculate_pay(entry, settings)
    
    db.roster.insert_one(entry.dict())
    return entry

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user with username and PIN"""
    user = db.users.find_one({"username": request.username, "is_active": True})
    if not user or not verify_pin(request.pin, user["pin_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or PIN")
    
    # Create session
    token = generate_token()
    session = Session(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        token=token,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=8)  # 8-hour session
    )
    
    db.sessions.insert_one(session.dict())
    
    # Update last login
    db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Remove sensitive data from response
    user_data = {k: v for k, v in user.items() if k not in ["pin_hash", "_id"]}
    
    return {
        "user": user_data,
        "token": token,
        "expires_at": session.expires_at
    }

@app.post("/api/auth/change-pin")
async def change_pin(request: ChangePinRequest, user: dict = Depends(get_current_user)):
    """Change user PIN"""
    if not verify_pin(request.current_pin, user["pin_hash"]):
        raise HTTPException(status_code=400, detail="Current PIN is incorrect")
    
    # Validate new PIN (4 or 6 digits)
    if not request.new_pin.isdigit() or len(request.new_pin) not in [4, 6]:
        raise HTTPException(status_code=400, detail="PIN must be 4 or 6 digits")
    
    new_pin_hash = hash_pin(request.new_pin)
    db.users.update_one(
        {"id": user["id"]},
        {"$set": {"pin_hash": new_pin_hash, "is_first_login": False}}
    )
    
    return {"message": "PIN changed successfully"}

@app.post("/api/auth/reset-pin")
async def reset_pin(request: ResetPinRequest):
    """Request PIN reset via email"""
    user = db.users.find_one({"username": request.username, "email": request.email, "is_active": True})
    if not user:
        raise HTTPException(status_code=404, detail="User not found with provided username and email")
    
    # Generate temporary PIN
    temp_pin = str(secrets.randbelow(1000000)).zfill(6)  # 6-digit temp PIN
    temp_pin_hash = hash_pin(temp_pin)
    
    # Update user with temporary PIN
    db.users.update_one(
        {"id": user["id"]},
        {"$set": {"pin_hash": temp_pin_hash, "is_first_login": True}}
    )
    
    # Send reset email
    send_reset_email(request.email, temp_pin)
    
    return {"message": "Temporary PIN sent to email address"}

@app.post("/api/admin/reset_pin")
async def admin_reset_pin(request: dict, current_user: dict = Depends(get_current_user)):
    """Admin reset PIN for any user (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Try to find user by email first, then by generated email pattern
    user = db.users.find_one({"email": email, "is_active": True})
    
    # If not found and email looks like generated email, try to find by staff name
    if not user and "@company.com" in email:
        # Extract staff name from generated email pattern
        staff_name_pattern = email.split("@")[0]
        # Find staff member by name pattern
        staff_member = db.staff.find_one({"active": True})
        if staff_member:
            staff_names = list(db.staff.find({"active": True}))
            for staff in staff_names:
                generated_email = f"{staff['name'].lower().replace(' ', '')}@company.com"
                if generated_email == email:
                    # Create a user account for this staff member if it doesn't exist
                    existing_user = db.users.find_one({"staff_id": staff["id"]}) 
                    if not existing_user:
                        # Create user account for staff member with default staff PIN
                        new_user = User(
                            id=str(uuid.uuid4()),
                            username=staff["name"].lower().replace(" ", ""),
                            pin_hash=hash_pin("888888"),  # Default staff PIN: 888888
                            role=UserRole.STAFF,
                            email=email,
                            first_name=staff["name"].split()[0] if " " in staff["name"] else staff["name"],
                            last_name=" ".join(staff["name"].split()[1:]) if " " in staff["name"] else "",
                            staff_id=staff["id"],
                            created_at=datetime.utcnow(),
                            is_first_login=True  # Staff must change PIN on first login
                        )
                        db.users.insert_one(new_user.dict())
                        user = new_user.dict()
                    else:
                        user = existing_user
                    break
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Determine appropriate reset PIN based on user role
    if user.get("role") == "admin":
        reset_pin = "0000"  # Admin reset PIN
        pin_length = 4
    else:
        reset_pin = "888888"  # Staff reset PIN
        pin_length = 6
    
    reset_pin_hash = hash_pin(reset_pin)
    
    # Update user with reset PIN and mark as first login for staff
    update_data = {
        "pin_hash": reset_pin_hash
    }
    
    # Staff must change PIN after reset, Admin doesn't need to
    if user.get("role") != "admin":
        update_data["is_first_login"] = True
    
    db.users.update_one(
        {"id": user["id"]},
        {"$set": update_data}
    )
    
    return {
        "message": "PIN reset successful",
        "temp_pin": reset_pin,
        "username": user.get("username", ""),
        "pin_length": pin_length,
        "must_change": user.get("role") != "admin"
    }

@app.get("/api/auth/logout")
async def logout(token: str):
    """Logout user and invalidate session"""
    db.sessions.update_one(
        {"token": token},
        {"$set": {"is_active": False}}
    )
    return {"message": "Logged out successfully"}

# User management endpoints
@app.get("/api/users/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    user_data = {k: v for k, v in current_user.items() if k not in ["pin_hash", "_id"]}
    return user_data

@app.put("/api/users/me")
async def update_current_user_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    """Update current user's profile"""
    # Filter allowed fields that user can update
    allowed_fields = ["first_name", "last_name", "email", "phone", "address", "date_of_birth", "emergency_contact"]
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user in database
    result = db.users.update_one(
        {"id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user data
    updated_user = db.users.find_one({"id": current_user["id"]}, {"_id": 0, "pin_hash": 0})
    return updated_user

@app.get("/api/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = list(db.users.find({"is_active": True}, {"_id": 0, "pin_hash": 0}))
    return users

@app.post("/api/users")
async def create_user(user_data: dict, current_user: dict = Depends(get_current_user)):
    """Create new user (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if username already exists
    existing_user = db.users.find_one({"username": user_data["username"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Determine default PIN based on role
    role = user_data.get("role", "staff")
    if role == "admin":
        default_pin = "0000"
        requires_pin_change = False
    else:
        default_pin = "888888"  # Staff default PIN
        requires_pin_change = True  # Staff must change PIN on first login
    
    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data["username"],
        pin_hash=hash_pin(default_pin),
        role=role,
        email=user_data.get("email"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        staff_id=user_data.get("staff_id"),
        created_at=datetime.utcnow(),
        is_first_login=requires_pin_change
    )
    
    db.users.insert_one(new_user.dict())
    
    # Remove sensitive data from response
    user_response = {k: v for k, v in new_user.dict().items() if k != "pin_hash"}
    user_response["default_pin"] = default_pin  # Include default PIN in response for admin
    return user_response

# Address autocomplete endpoint using free Nominatim API
@app.get("/api/address/search")
async def search_addresses(q: str, limit: int = 5):
    """Search addresses using OpenStreetMap Nominatim API (free)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "addressdetails": 1,
                    "limit": limit,
                    "countrycodes": "au,us,gb,ca,nz"  # Limit to common English-speaking countries
                },
                headers={
                    "User-Agent": "RosterSync-AddressAutocomplete/1.0"
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                formatted_results = []
                
                for result in results:
                    address = result.get("address", {})
                    formatted_results.append({
                        "display_name": result.get("display_name", ""),
                        "street_number": address.get("house_number", ""),
                        "route": address.get("road", ""),
                        "locality": address.get("city") or address.get("town") or address.get("village", ""),
                        "administrative_area_level_1": address.get("state", ""),
                        "country": address.get("country", ""),
                        "postal_code": address.get("postcode", ""),
                        "latitude": float(result.get("lat", 0)),
                        "longitude": float(result.get("lon", 0))
                    })
                
                return formatted_results
            else:
                return []
                
    except Exception as e:
        print(f"Address search error: {e}")
        return []

# Initialize database with default admin user if not exists
def initialize_admin():
    """Initialize default admin user if not exists"""
    admin_user = db.users.find_one({"username": "Admin"})
    if not admin_user:
        print("Creating default admin user...")
        default_admin = User(
            id=str(uuid.uuid4()),
            username="Admin",
            pin_hash=hash_pin("0000"),  # Default PIN: 0000 (user can change this)
            role=UserRole.ADMIN,
            email="admin@company.com",
            first_name="System",
            last_name="Administrator",
            created_at=datetime.utcnow(),
            is_active=True,
            is_first_login=False  # Admin doesn't need to change PIN immediately
        )
        db.users.insert_one(default_admin.dict())
        print("✅ Default admin user created: Username=Admin, PIN=0000")
    else:
        print("✅ Admin user already exists - preserving existing PIN")

# Initialize admin on startup
initialize_admin()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)