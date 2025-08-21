import os
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/workcare_manage')
client = MongoClient(mongo_url)
db = client.workcare_manage

print('🔍 Debugging Export Function Step by Step...')

# Simulate the export function logic
month = '2024-12'
current_user = {'role': 'admin', 'id': 'test-admin-id'}

# Parse month (YYYY-MM format)
year, month_num = map(int, month.split('-'))
start_date = f'{year}-{month_num:02d}-01'
if month_num == 12:
    end_year = year + 1
    end_month = 1
else:
    end_year = year
    end_month = month_num + 1
end_date = f'{end_year}-{end_month:02d}-01'

print(f'1. Date range: {start_date} to {end_date}')

# Query roster entries for the month
query = {
    'date': {'$gte': start_date, '$lt': end_date}
}

roster_entries = list(db.roster_entries.find(query, {'_id': 0}).sort('date', 1))
print(f'2. Found {len(roster_entries)} roster entries from DB')

if roster_entries:
    print(f'   First entry: {roster_entries[0].get("date")}')
    print(f'   Staff ID in first entry: {roster_entries[0].get("staff_id")}')

# Get staff information
staff_dict = {}
for staff in db.staff.find({}, {'_id': 0}):
    staff_dict[staff['id']] = staff

print(f'3. Found {len(staff_dict)} staff members')

# Process entries and add calculated information
export_data = []
for i, entry in enumerate(roster_entries[:3]):  # Check first 3 entries
    print(f'\nProcessing entry {i+1}:')
    print(f'  Date: {entry.get("date")}')
    print(f'  Staff ID: {entry.get("staff_id")}')
    
    staff_info = staff_dict.get(entry.get('staff_id', ''), {})
    staff_name = staff_info.get('name', 'Unassigned') if entry.get('staff_id') else 'Unassigned'
    print(f'  Staff name: {staff_name}')
    
    # Role-based data filtering
    if current_user['role'] == 'staff':
        # Staff can only see their own shifts
        if entry.get('staff_id') != current_user.get('id'):
            print(f'  FILTERED OUT: Staff role, not own shift')
            continue
    else:
        print(f'  ADMIN: Including entry')
    
    # Calculate pay information
    hours_worked = entry.get('hours_worked', 0)
    base_pay = entry.get('base_pay', 0)
    total_pay = entry.get('total_pay', 0)
    
    print(f'  Hours: {hours_worked}, Base pay: {base_pay}, Total: {total_pay}')
    
    export_entry = {
        'Date': entry.get('date', ''),
        'Staff Name': staff_name,
        'Hours Worked': f'{hours_worked:.1f}h',
        'Total Pay': f'${total_pay:.2f}',
    }
    
    export_data.append(export_entry)
    print(f'  ADDED to export_data')

print(f'\n4. Final export_data length: {len(export_data)}')
print(f'   Export data empty: {not export_data}')