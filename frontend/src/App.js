import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar } from './components/ui/calendar';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { AddressAutocomplete } from './components/ui/address-autocomplete';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Switch } from './components/ui/switch';
import { Separator } from './components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Users, Calendar as CalendarIcon, Settings, DollarSign, Clock, Download, Plus, Edit, Trash2, Check, CheckSquare, Copy, User, LogOut, Bell, FileText, Calendar as CalendarViewIcon, X } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Helper function for timezone-safe date formatting
const formatDateString = (date) => {
  // Handle both Date objects and date strings
  if (typeof date === 'string') {
    // If it's already a string in YYYY-MM-DD format, return as is
    if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return date;
    }
    // Otherwise, try to parse it as a Date
    date = new Date(date);
  }
  
  // Ensure we have a valid Date object
  if (!(date instanceof Date) || isNaN(date.getTime())) {
    console.error('Invalid date passed to formatDateString:', date);
    return '';
  }
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// Helper function to get Brisbane AEST timezone date
const getBrisbaneDate = (date = new Date()) => {
  // Brisbane is AEST (UTC+10) - handle timezone conversion
  const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
  const brisbaneTime = new Date(utc + (10 * 3600000)); // +10 hours for AEST
  return brisbaneTime;
};

// ISO 8601 week date system functions
const getISOWeek = (date) => {
  const tempDate = new Date(date.getTime());
  tempDate.setHours(0, 0, 0, 0);
  // Thursday in current week decides the year
  tempDate.setDate(tempDate.getDate() + 3 - (tempDate.getDay() + 6) % 7);
  // January 4 is always in week 1
  const week1 = new Date(tempDate.getFullYear(), 0, 4);
  // Adjust to Thursday in week 1 and count weeks from there
  return 1 + Math.round(((tempDate.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
};

const getISOWeekYear = (date) => {
  const tempDate = new Date(date.getTime());
  tempDate.setDate(tempDate.getDate() + 3 - (tempDate.getDay() + 6) % 7);
  return tempDate.getFullYear();
};

// Get Monday of the ISO week
const getMondayOfISOWeek = (week, year) => {
  const jan4 = new Date(year, 0, 4);
  const jan4Day = (jan4.getDay() + 6) % 7; // Monday = 0
  const mondayOfWeek1 = new Date(jan4.getTime() - jan4Day * 86400000);
  return new Date(mondayOfWeek1.getTime() + (week - 1) * 7 * 86400000);
};






// Helper function to format time based on user preference
const formatTime = (timeString, is24Hour = true) => {
  if (!timeString) return '';
  
  if (is24Hour) {
    return timeString; // Already in 24hr format (HH:MM)
  }
  
  // Convert to 12hr format
  const [hours, minutes] = timeString.split(':');
  const hour24 = parseInt(hours, 10);
  
  if (hour24 === 0) {
    return `12:${minutes} AM`;
  } else if (hour24 < 12) {
    return `${hour24}:${minutes} AM`;
  } else if (hour24 === 12) {
    return `12:${minutes} PM`;
  } else {
    return `${hour24 - 12}:${minutes} PM`;
  }
};

// Helper function to convert 12hr format back to 24hr for storage
const convertTo24Hour = (timeString) => {
  if (!timeString) return '';
  
  // If already in 24hr format, return as is
  if (!/AM|PM/i.test(timeString)) {
    return timeString;
  }
  
  const [time, period] = timeString.split(/\s+(AM|PM)/i);
  const [hours, minutes] = time.split(':');
  let hour24 = parseInt(hours, 10);
  
  if (period.toUpperCase() === 'AM' && hour24 === 12) {
    hour24 = 0;
  } else if (period.toUpperCase() === 'PM' && hour24 !== 12) {
    hour24 += 12;
  }
  
  return `${String(hour24).padStart(2, '0')}:${minutes}`;
};

// Helper functions for unassigned shifts filtering
const filterUnassignedShiftsByViewMode = (shifts, viewMode, currentDate, searchDate) => {
  if (!shifts || shifts.length === 0) return [];
  
  const today = getBrisbaneDate();
  const targetDate = viewMode === 'search' && searchDate ? new Date(searchDate) : currentDate;
  
  switch (viewMode) {
    case 'daily':
      const todayStr = formatDateString(targetDate);
      return shifts.filter(shift => shift.date === todayStr);
      
    case 'weekly':
      const startOfWeek = new Date(targetDate);
      const day = startOfWeek.getDay();
      const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
      startOfWeek.setDate(diff);
      
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      
      return shifts.filter(shift => {
        const shiftDate = new Date(shift.date);
        return shiftDate >= startOfWeek && shiftDate <= endOfWeek;
      });
      
    case 'monthly':
      const startOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1);
      const endOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0);
      
      return shifts.filter(shift => {
        const shiftDate = new Date(shift.date);
        return shiftDate >= startOfMonth && shiftDate <= endOfMonth;
      });
      
    case 'search':
      if (!searchDate) return shifts;
      return shifts.filter(shift => shift.date === searchDate);
      
    case 'calendar':
    default:
      return shifts;
  }
};

const groupUnassignedShiftsByDate = (shifts) => {
  const grouped = {};
  shifts.forEach(shift => {
    const date = shift.date;
    if (!grouped[date]) {
      grouped[date] = [];
    }
    grouped[date].push(shift);
  });
  
  // Sort dates
  const sortedDates = Object.keys(grouped).sort();
  const result = {};
  sortedDates.forEach(date => {
    result[date] = grouped[date].sort((a, b) => a.start_time.localeCompare(b.start_time));
  });
  
  return result;
};

function App() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [showLoginDialog, setShowLoginDialog] = useState(true); // Show login screen
  const [showChangePinDialog, setShowChangePinDialog] = useState(false);
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [showStaffProfileDialog, setShowStaffProfileDialog] = useState(false);
  const [showStaffSelfProfileDialog, setShowStaffSelfProfileDialog] = useState(false);
  const [selectedStaffForProfile, setSelectedStaffForProfile] = useState(null);
  const [loginData, setLoginData] = useState({ username: '', pin: '' });
  const [availableUsers, setAvailableUsers] = useState([]);
  const [useDropdown, setUseDropdown] = useState(true);
  const [changePinData, setChangePinData] = useState({ current_pin: '', new_pin: '', confirm_pin: '' });
  const [profileData, setProfileData] = useState({});
  const [editingProfile, setEditingProfile] = useState(false);
  
  // Save staff profile function
  const saveStaffProfile = async () => {
    try {
      if (!selectedStaffForProfile) return;
      
      const response = await axios.put(`${API_BASE_URL}/api/staff/${selectedStaffForProfile.id}`, selectedStaffForProfile);
      console.log('Staff profile saved:', response.data);
      
      // Update the staff list locally
      const updatedStaff = staff.map(s => 
        s.id === selectedStaffForProfile.id ? selectedStaffForProfile : s
      );
      setStaff(updatedStaff);
      
      setShowStaffProfileDialog(false);
      alert('✅ Staff profile updated successfully!');
    } catch (error) {
      console.error('Error saving staff profile:', error);
      alert(`❌ Error saving profile: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // Reset staff PIN function  
  const resetStaffPin = async () => {
    try {
      if (!selectedStaffForProfile) return;
      
      const staffName = selectedStaffForProfile.name;
      const isAdmin = selectedStaffForProfile.role === 'admin';
      
      if (window.confirm(`🔐 RESET PIN\n\nAre you sure you want to reset the PIN for ${staffName}?\n\nThis will generate a new ${isAdmin ? '4-digit' : '6-digit'} temporary PIN that ${isAdmin ? 'can be used immediately' : 'must be changed on first login'}.`)) {
        const response = await axios.post(`${API_BASE_URL}/api/admin/reset_pin`, {
          email: selectedStaffForProfile.email || `${selectedStaffForProfile.name.toLowerCase().replace(/\s+/g, '')}@company.com`
        });
        
        console.log('PIN reset response:', response.data);
        
        const { temp_pin, username, pin_length, must_change } = response.data;
        
        alert(`🔐 PIN has been reset for ${staffName}.\n\n` +
              `New ${pin_length}-digit PIN: ${temp_pin}\n` +
              `Username: ${username}\n\n` +
              `${must_change ? 
                '⚠️ IMPORTANT: This staff member MUST change their PIN on first login for security.' :
                'This PIN can be used immediately.'}\n\n` +
              `Please provide these credentials to ${staffName} securely.`);
      }
    } catch (error) {
      console.error('Error resetting PIN:', error);
      
      // Better error message extraction
      let errorMessage = 'Unknown error occurred';
      
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else {
          errorMessage = JSON.stringify(error.response.data);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Error resetting PIN: ${errorMessage}`);
    }
  };

  // Delete staff member function (Admin only)
  const handleDeleteStaff = async (staffMember) => {
    if (!isAdmin()) {
      alert('❌ Admin access required to delete staff members.');
      return;
    }

    const confirmMessage = `⚠️ Are you sure you want to delete staff member "${staffMember.name}"?\n\nThis action will:\n• Deactivate the staff member\n• Unassign them from all future shifts\n• Preserve past shift records for payroll history\n\nType "DELETE" to confirm:`;
    
    const confirmation = prompt(confirmMessage);
    
    if (confirmation !== 'DELETE') {
      alert('❌ Deletion cancelled. Staff member was not deleted.');
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE_URL}/api/staff/${staffMember.id}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      const result = response.data;
      
      let message = `✅ ${result.message}\n\n`;
      
      if (result.shifts_affected) {
        message += `📊 Shift Impact:\n`;
        message += `• Future shifts unassigned: ${result.shifts_affected.future_shifts_unassigned}\n`;
        message += `• Past shifts preserved: ${result.shifts_affected.past_shifts_preserved}\n`;
        message += `• Total shifts affected: ${result.shifts_affected.total_shifts}\n\n`;
      }
      
      message += `The staff member has been deactivated and removed from future scheduling.`;
      
      alert(message);
      
      // Refresh data
      fetchInitialData();
      fetchRosterData();
      
    } catch (error) {
      console.error('Error deleting staff member:', error);
      alert(`❌ Error deleting staff member: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Sync staff users - Create missing user accounts for staff (Admin only)
  const syncStaffUsers = async () => {
    if (!isAdmin()) {
      alert('❌ Admin access required to sync staff users.');
      return;
    }

    const confirmMessage = `🔧 Staff User Synchronization\n\nThis will:\n• Create user accounts for staff members without login credentials\n• Set default PIN "888888" for new accounts\n• Clean up staff records with empty names\n• Allow staff to login and change their PINs\n\nProceed with synchronization?`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/admin/sync_staff_users`, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      const result = response.data;
      
      let message = `✅ ${result.message}\n\n`;
      
      if (result.summary) {
        message += `📊 Summary:\n`;
        message += `• Created: ${result.summary.created} new user accounts\n`;
        message += `• Existing: ${result.summary.existing} accounts already existed\n`;
        message += `• Errors: ${result.summary.errors} errors encountered\n`;
        message += `• Cleaned up: ${result.summary.cleaned_up} empty name records\n\n`;
      }
      
      if (result.created_users && result.created_users.length > 0) {
        message += `👥 New User Accounts Created:\n`;
        result.created_users.forEach(user => {
          message += `• ${user}\n`;
        });
        message += `\n`;
      }
      
      if (result.errors && result.errors.length > 0) {
        message += `⚠️ Errors Encountered:\n`;
        result.errors.forEach(error => {
          message += `• ${error}\n`;
        });
        message += `\n`;
      }
      
      message += `🎯 Next Steps:\n`;
      message += `• Staff can now login with their username and PIN "888888"\n`;
      message += `• They will be prompted to change their PIN on first login\n`;
      message += `• Test staff login functionality`;
      
      alert(message);
      
      // Refresh data
      fetchInitialData();
      fetchAvailableUsers();
      
    } catch (error) {
      console.error('Error syncing staff users:', error);
      alert(`❌ Error syncing staff users: ${error.response?.data?.detail || error.message}`);
    }
  };

  const [authError, setAuthError] = useState('');
  const [addingStaff, setAddingStaff] = useState(false);

  const [currentDate, setCurrentDate] = useState(getBrisbaneDate());
  const [staff, setStaff] = useState([]);
  const [clients, setClients] = useState([]); // New state for client profiles
  const [selectedClient, setSelectedClient] = useState(null); // Currently selected client
  const [currentClient, setCurrentClient] = useState(null); // Client being processed with OCR
  const [shiftTemplates, setShiftTemplates] = useState([]);
  const [rosterEntries, setRosterEntries] = useState([]);
  const [settings, setSettings] = useState({
    pay_mode: 'default',
    timezone: 'Australia/Brisbane', // AEST UTC+10
    time_format: '24hr', // '12hr' or '24hr'
    first_day_of_week: 'monday', // 'monday' or 'sunday'
    dark_mode: false, // true or false
    rates: {
      weekday_day: 42.00,
      weekday_evening: 44.50,
      weekday_night: 48.50,
      saturday: 57.50,
      sunday: 74.00,
      public_holiday: 88.50,
      sleepover_default: 175.00,
      sleepover_schads: 60.02
    }
  });
  const [selectedShift, setSelectedShift] = useState(null);
  const [showShiftDialog, setShowShiftDialog] = useState(false);
  const [showStaffDialog, setShowStaffDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  
  // Bulk editing states for Shift Times panel
  const [bulkEditMode, setBulkEditMode] = useState(false);
  const [selectedTemplates, setSelectedTemplates] = useState(new Set());
  const [showBulkEditDialog, setShowBulkEditDialog] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({
    start_time: '',
    end_time: '',
    is_sleepover: false,
    allow_overlap: false,
    shift_type_override: '',
    day_of_week: '',
    apply_to: 'selected' // 'selected' or 'all'
  });
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showBreakWarning, setShowBreakWarning] = useState(false);
  const [breakWarningData, setBreakWarningData] = useState(null);
  const [showAddShiftDialog, setShowAddShiftDialog] = useState(false);
  const [rosterTemplates, setRosterTemplates] = useState([]);
  const [showRosterTemplateDialog, setShowRosterTemplateDialog] = useState(false);
  const [showManageTemplatesDialog, setShowManageTemplatesDialog] = useState(false);
  const [showTemplateEditDialog, setShowTemplateEditDialog] = useState(false);
  const [selectedRosterTemplateForEdit, setSelectedRosterTemplateForEdit] = useState(null);
  const [showOverlapDialog, setShowOverlapDialog] = useState(false);
  const [overlapData, setOverlapData] = useState(null);
  const [showYTDReportDialog, setShowYTDReportDialog] = useState(false);
  const [ytdReportType, setYTDReportType] = useState('financial'); // 'calendar' or 'financial'
  const [showSaveTemplateDialog, setShowSaveTemplateDialog] = useState(false);
  const [showGenerateFromTemplateDialog, setShowGenerateFromTemplateDialog] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [selectedRosterTemplate, setSelectedRosterTemplate] = useState(null);
  const [newShift, setNewShift] = useState({
    date: '',
    start_time: '09:00',
    end_time: '17:00',
    staff_id: null,
    staff_name: null,
    is_sleepover: false,
    allow_overlap: false
  });
  const [newStaffName, setNewStaffName] = useState('');
  const [activeTab, setActiveTab] = useState('roster');
  const [dayTemplates, setDayTemplates] = useState([]);
  const [showDayTemplateDialog, setShowDayTemplateDialog] = useState(false);
  const [selectedDateForTemplate, setSelectedDateForTemplate] = useState(null);
  const [dayTemplateAction, setDayTemplateAction] = useState(''); // 'save' or 'load'
  const [selectedDayTemplate, setSelectedDayTemplate] = useState(null);
  const [newDayTemplateName, setNewDayTemplateName] = useState('');
  const [viewMode, setViewMode] = useState('calendar'); // 'daily', 'weekly', 'monthly', 'calendar'
  const [selectedSingleDate, setSelectedSingleDate] = useState(new Date());
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [showEventDialog, setShowEventDialog] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    date: '',
    start_time: '',
    end_time: '',
    is_all_day: false,
    event_type: 'appointment',
    priority: 'medium',
    location: '',
    attendees: [],
    reminder_minutes: 15
  });

  // Availability and Shift Request states
  const [unassignedShifts, setUnassignedShifts] = useState([]);
  const [shiftRequests, setShiftRequests] = useState([]);
  const [staffAvailability, setStaffAvailability] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showShiftRequestDialog, setShowShiftRequestDialog] = useState(false);
  const [selectedUnassignedShift, setSelectedUnassignedShift] = useState(null);
  const [showAvailabilityDialog, setShowAvailabilityDialog] = useState(false);
  const [newAvailability, setNewAvailability] = useState({
    availability_type: 'available',
    date_from: '',
    date_to: '',
    day_of_week: null,
    start_time: '',
    end_time: '',
    is_recurring: false,
    notes: '',
    staff_id: '' // For admin to select which staff member
  });
  const [showNotifications, setShowNotifications] = useState(false);
  const [unassignedShiftsViewMode, setUnassignedShiftsViewMode] = useState('daily');
  const [unassignedShiftsSearchDate, setUnassignedShiftsSearchDate] = useState('');
  
  // Shift Request CRUD states
  const [showEditShiftRequestDialog, setShowEditShiftRequestDialog] = useState(false);
  const [showAddShiftRequestDialog, setShowAddShiftRequestDialog] = useState(false);
  const [editingShiftRequest, setEditingShiftRequest] = useState(null);
  const [newShiftRequest, setNewShiftRequest] = useState({
    staff_id: '',
    roster_entry_id: '',
    notes: '',
    admin_notes: ''
  });

  // Staff Availability CRUD states
  const [showEditStaffAvailabilityDialog, setShowEditStaffAvailabilityDialog] = useState(false);
  const [editingStaffAvailability, setEditingStaffAvailability] = useState(null);

  // Client Profile Dialog States
  const [showClientDialog, setShowClientDialog] = useState(false);
  const [showClientProfileDialog, setShowClientProfileDialog] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  
  // Client Biography Dialog States
  const [showClientBiographyDialog, setShowClientBiographyDialog] = useState(false);
  const [editingClientBiography, setEditingClientBiography] = useState(null);
  const [clientBiographyData, setClientBiographyData] = useState({
    strengths: '',
    living_arrangements: '',
    daily_life: '',
    goals: [],
    supports: [],
    additional_info: ''
  });
  const [newClient, setNewClient] = useState({
    full_name: '',
    date_of_birth: '',
    sex: 'Male',
    disability_condition: '',
    mobile: '',
    address: '',
    emergency_contacts: [
      { name: '', relationship: '', mobile: '', address: '' }
    ],
    current_ndis_plan: null
  });
  
  // Touch/swipe handling for mobile
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  const [swipingShiftId, setSwipingShiftId] = useState(null);
  
  // Bulk selection functionality
  const [selectedShifts, setSelectedShifts] = useState(new Set());
  const [bulkSelectionMode, setBulkSelectionMode] = useState(false);
  const [showBulkActionsDialog, setShowBulkActionsDialog] = useState(false);

  // Fetch unassigned shifts
  const fetchUnassignedShifts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/unassigned-shifts`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setUnassignedShifts(response.data);
    } catch (error) {
      console.error('Error fetching unassigned shifts:', error);
    }
  };

  // Fetch shift requests
  const fetchShiftRequests = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/shift-requests`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setShiftRequests(response.data);
    } catch (error) {
      console.error('Error fetching shift requests:', error);
    }
  };

  // Fetch staff availability
  const fetchStaffAvailability = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/staff-availability`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setStaffAvailability(response.data);
    } catch (error) {
      console.error('Error fetching staff availability:', error);
    }
  };

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/notifications`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  // Submit shift request
  const submitShiftRequest = async (shiftId, notes) => {
    try {
      await axios.post(`${API_BASE_URL}/api/shift-requests`, {
        roster_entry_id: shiftId,
        notes: notes
      }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Shift request submitted successfully!');
      fetchShiftRequests();
      fetchUnassignedShifts();
      setShowShiftRequestDialog(false);
    } catch (error) {
      console.error('Error submitting shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Create staff availability
  const createStaffAvailability = async (availability) => {
    try {
      // For Admin users, validate that staff_id is selected
      if (isAdmin() && !availability.staff_id) {
        alert('❌ Please select a staff member');
        return;
      }
      
      // Prepare the availability data
      const availabilityData = {
        ...availability,
        // For staff users, automatically use their own staff_id and name
        // For admin users, use the selected staff_id and find the corresponding name
        staff_id: isStaff() ? currentUser?.staff_id : availability.staff_id
      };
      
      // Add staff_name which is required by the backend
      if (isStaff()) {
        availabilityData.staff_name = currentUser?.name || currentUser?.username;
      } else if (isAdmin() && availability.staff_id) {
        // Find the staff member's name from the staff list
        const selectedStaff = staff.find(s => s.id === availability.staff_id);
        if (selectedStaff) {
          availabilityData.staff_name = selectedStaff.name;
        }
      }

      await axios.post(`${API_BASE_URL}/api/staff-availability`, availabilityData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Availability updated successfully!');
      fetchStaffAvailability();
      setShowAvailabilityDialog(false);
      setNewAvailability({
        availability_type: 'available',
        date_from: '',
        date_to: '',
        day_of_week: null,
        start_time: '',
        end_time: '',
        is_recurring: false,
        notes: '',
        staff_id: ''
      });
    } catch (error) {
      console.error('Error creating availability:', error);
      
      // Better error message handling to avoid [object Object] display
      let errorMessage = 'Unknown error occurred';
      
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.detail) {
          // Handle both string and object detail responses
          if (typeof error.response.data.detail === 'string') {
            errorMessage = error.response.data.detail;
          } else if (typeof error.response.data.detail === 'object') {
            // Convert object to readable string
            errorMessage = JSON.stringify(error.response.data.detail);
          }
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else {
          // Fallback: convert entire response data to string
          errorMessage = JSON.stringify(error.response.data);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Error: ${errorMessage}`);
    }
  };

  // Approve shift request (Admin only)
  const approveShiftRequest = async (requestId, adminNotes) => {
    try {
      await axios.put(`${API_BASE_URL}/api/shift-requests/${requestId}/approve`, 
        { admin_notes: adminNotes }, 
        { headers: { 'Authorization': `Bearer ${authToken}` } }
      );
      alert('✅ Shift request approved successfully!');
      fetchShiftRequests();
      fetchUnassignedShifts();
      fetchRosterData();
    } catch (error) {
      console.error('Error approving shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Reject shift request (Admin only)
  const rejectShiftRequest = async (requestId, adminNotes) => {
    try {
      await axios.put(`${API_BASE_URL}/api/shift-requests/${requestId}/reject`, 
        { admin_notes: adminNotes }, 
        { headers: { 'Authorization': `Bearer ${authToken}` } }
      );
      alert('✅ Shift request rejected');
      fetchShiftRequests();
      fetchNotifications(); // Refresh notifications
    } catch (error) {
      console.error('Error rejecting shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Edit/Update shift request (Admin only)
  const updateShiftRequest = async (requestId, requestData) => {
    try {
      await axios.put(`${API_BASE_URL}/api/shift-requests/${requestId}`, requestData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Shift request updated successfully');
      fetchShiftRequests();
      setShowEditShiftRequestDialog(false);
      setEditingShiftRequest(null);
    } catch (error) {
      console.error('Error updating shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Delete shift request (Admin only)  
  const deleteShiftRequest = async (requestId) => {
    if (!window.confirm('Are you sure you want to delete this shift request?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/shift-requests/${requestId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Shift request deleted successfully');
      fetchShiftRequests();
    } catch (error) {
      console.error('Error deleting shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Create new shift request (Admin only)
  const createShiftRequest = async (requestData) => {
    try {
      // Validate required fields
      if (!requestData.staff_id || !requestData.roster_entry_id) {
        alert('❌ Please select both a staff member and a shift');
        return;
      }

      await axios.post(`${API_BASE_URL}/api/shift-requests`, requestData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Shift request created successfully');
      fetchShiftRequests();
      setShowAddShiftRequestDialog(false);
      setNewShiftRequest({
        staff_id: '',
        roster_entry_id: '',
        notes: '',
        admin_notes: ''
      });
    } catch (error) {
      console.error('Error creating shift request:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Clear all shift requests (Admin only)
  const clearAllShiftRequests = async () => {
    if (!window.confirm('Are you sure you want to clear ALL shift requests? This cannot be undone.')) {
      return;
    }
    
    try {
      // Delete all shift requests one by one
      const deletePromises = shiftRequests.map(request => 
        axios.delete(`${API_BASE_URL}/api/shift-requests/${request.id}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        })
      );
      
      await Promise.all(deletePromises);
      alert(`✅ Cleared ${shiftRequests.length} shift requests successfully`);
      fetchShiftRequests();
    } catch (error) {
      console.error('Error clearing shift requests:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Update staff availability (Admin only)
  const updateStaffAvailability = async (availabilityId, availabilityData) => {
    try {
      await axios.put(`${API_BASE_URL}/api/staff-availability/${availabilityId}`, availabilityData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Staff availability updated successfully');
      fetchStaffAvailability();
      setShowEditStaffAvailabilityDialog(false);
      setEditingStaffAvailability(null);
    } catch (error) {
      console.error('Error updating staff availability:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Delete staff availability (Admin only or own records for staff)
  const deleteStaffAvailability = async (availabilityId) => {
    if (!window.confirm('Are you sure you want to delete this availability record?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/staff-availability/${availabilityId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Availability record deleted successfully');
      fetchStaffAvailability();
    } catch (error) {
      console.error('Error deleting availability:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Clear all staff availability (Admin only)
  const clearAllStaffAvailability = async () => {
    if (!window.confirm('Are you sure you want to clear ALL staff availability records? This cannot be undone.')) {
      return;
    }
    
    try {
      // Delete all availability records one by one
      const deletePromises = staffAvailability.map(availability => 
        axios.delete(`${API_BASE_URL}/api/staff-availability/${availability.id}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        })
      );
      
      await Promise.all(deletePromises);
      alert(`✅ Cleared ${staffAvailability.length} availability records successfully`);
      fetchStaffAvailability();
    } catch (error) {
      console.error('Error clearing staff availability:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Mark notification as read
  const markNotificationRead = async (notificationId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      fetchNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Check assignment conflicts (when admin assigns staff)
  const checkAssignmentConflicts = async (staffId, date, startTime, endTime) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/check-assignment-conflicts`, {
        staff_id: staffId,
        date: date,
        start_time: startTime,
        end_time: endTime
      }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      return response.data;
    } catch (error) {
      console.error('Error checking assignment conflicts:', error);
      return { has_conflicts: false, conflicts: [], can_override: true };
    }
  };

  // Helper function to format date strings for display
  const formatAvailabilityDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-AU', { 
      weekday: 'short', 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Helper function to get availability type badge
  const getAvailabilityTypeBadge = (type) => {
    const badges = {
      'available': <Badge className="bg-green-100 text-green-800">✅ Available</Badge>,
      'unavailable': <Badge className="bg-red-100 text-red-800">❌ Unavailable</Badge>,
      'time_off_request': <Badge className="bg-orange-100 text-orange-800">🏖️ Time Off Request</Badge>,
      'preferred_shifts': <Badge className="bg-blue-100 text-blue-800">⭐ Preferred</Badge>
    };
    return badges[type] || <Badge variant="secondary">{type}</Badge>;
  };

  // Helper function to get day of week name
  const getDayOfWeekName = (dayNumber) => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return days[dayNumber] || 'Unknown';
  };

  // Load availability data when authenticated
  useEffect(() => {
    if (isAuthenticated && authToken) {
      fetchUnassignedShifts();
      fetchShiftRequests();
      fetchStaffAvailability();
      fetchNotifications();
    }
  }, [isAuthenticated, authToken]);

  // Helper function to check if current user is admin
  const isAdmin = () => {
    return currentUser && currentUser.role === 'admin';
  };

  // Helper function to check if current user is staff
  const isStaff = () => {
    return currentUser && currentUser.role === 'staff';
  };

  // =====================================
  // CLIENT PROFILE MANAGEMENT FUNCTIONS
  // =====================================

  // OCR-related states
  const [showOCRDialog, setShowOCRDialog] = useState(false);
  const [ocrProcessing, setOCRProcessing] = useState(false);
  const [ocrResults, setOCRResults] = useState(null);
  const [ocrTaskId, setOCRTaskId] = useState(null);
  const [ocrProgress, setOCRProgress] = useState(0);
  const [extractedClientData, setExtractedClientData] = useState(null);
  const [showOCRReviewDialog, setShowOCRReviewDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [processedFileCount, setProcessedFileCount] = useState(0);
  const [totalFileCount, setTotalFileCount] = useState(0);

  // Fetch all clients
  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Create new client profile (Admin only)
  const createClientProfile = async (clientData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/clients`, clientData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Client profile created successfully!');
      fetchClients();
      setShowClientDialog(false);
      setNewClient({
        full_name: '',
        date_of_birth: '',
        sex: 'Male',
        disability_condition: '',
        mobile: '',
        address: '',
        emergency_contacts: [
          { name: '', relationship: '', mobile: '', address: '' }
        ],
        current_ndis_plan: null
      });
    } catch (error) {
      console.error('Error creating client profile:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Update client profile (Admin only)
  const updateClientProfile = async (clientId, clientData) => {
    try {
      await axios.put(`${API_BASE_URL}/api/clients/${clientId}`, clientData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Client profile updated successfully!');
      fetchClients();
      setShowClientDialog(false);
      setEditingClient(null);
    } catch (error) {
      console.error('Error updating client profile:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Delete client profile (Admin only)
  const deleteClientProfile = async (clientId) => {
    if (!window.confirm('Are you sure you want to delete this client profile?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/clients/${clientId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      alert('✅ Client profile deleted successfully');
      fetchClients();
    } catch (error) {
      console.error('Error deleting client profile:', error);
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Get client budget summary
  const getClientBudgetSummary = async (clientId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/clients/${clientId}/budget-summary`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching budget summary:', error);
      return null;
    }
  };

  // Load client data when authenticated
  useEffect(() => {
    if (isAuthenticated && authToken) {
      fetchClients();
    }
  }, [isAuthenticated, authToken]);

  // =====================================
  // CLIENT BIOGRAPHY MANAGEMENT FUNCTIONS
  // =====================================

  // Open client biography dialog for editing
  const openClientBiographyDialog = (client) => {
    setEditingClientBiography(client);
    setClientBiographyData({
      strengths: client.biography?.strengths || '',
      living_arrangements: client.biography?.living_arrangements || '',
      daily_life: client.biography?.daily_life || '',
      goals: client.biography?.goals || [],
      supports: client.biography?.supports || [],
      additional_info: client.biography?.additional_info || ''
    });
    setShowClientBiographyDialog(true);
  };

  // Update client biography
  const updateClientBiography = async (clientId, biographyData) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/api/clients/${clientId}/biography`, biographyData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      alert('✅ Client biography updated successfully!');
      fetchClients(); // Refresh client list
      setShowClientBiographyDialog(false);
      return response.data;
    } catch (error) {
      console.error('Error updating client biography:', error);
      if (error.response?.status === 403) {
        alert('❌ Access denied - You don\'t have permission to edit this information.');
      } else {
        alert('❌ Failed to update client biography. Please try again.');
      }
      throw error;
    }
  };

  // Add new goal to biography
  const addGoalToBiography = () => {
    const newGoal = {
      title: '',
      description: '',
      how_to_achieve: ''
    };
    setClientBiographyData(prev => ({
      ...prev,
      goals: [...prev.goals, newGoal]
    }));
  };

  // Remove goal from biography
  const removeGoalFromBiography = (index) => {
    setClientBiographyData(prev => ({
      ...prev,
      goals: prev.goals.filter((_, i) => i !== index)
    }));
  };

  // Update goal in biography
  const updateGoalInBiography = (index, field, value) => {
    setClientBiographyData(prev => ({
      ...prev,
      goals: prev.goals.map((goal, i) => 
        i === index ? { ...goal, [field]: value } : goal
      )
    }));
  };

  // Add new support to biography
  const addSupportToBiography = () => {
    const newSupport = {
      description: '',
      provider: '',
      frequency: '',
      type: ''
    };
    setClientBiographyData(prev => ({
      ...prev,
      supports: [...prev.supports, newSupport]
    }));
  };

  // Remove support from biography
  const removeSupportFromBiography = (index) => {
    setClientBiographyData(prev => ({
      ...prev,
      supports: prev.supports.filter((_, i) => i !== index)
    }));
  };

  // Update support in biography
  const updateSupportInBiography = (index, field, value) => {
    setClientBiographyData(prev => ({
      ...prev,
      supports: prev.supports.map((support, i) => 
        i === index ? { ...support, [field]: value } : support
      )
    }));
  };

  // =====================================
  // OCR DOCUMENT PROCESSING FUNCTIONS
  // =====================================

  // Process multiple uploaded NDIS plan documents
  const processMultipleOCRDocuments = async (files) => {
    if (!files || files.length === 0) return;

    console.log(`🔄 Starting batch OCR processing for ${files.length} files`);
    setOCRProcessing(true);
    setOCRProgress(0);
    setOCRResults(null);
    setExtractedClientData(null);
    setProcessedFileCount(0);
    setTotalFileCount(files.length);

    const totalFiles = files.length;
    const results = [];
    let completedFiles = 0;

    try {
      console.log(`Processing ${totalFiles} files sequentially...`);
      
      // Process files sequentially to avoid overwhelming the server
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const currentFileNum = i + 1;
        
        console.log(`📄 Processing file ${currentFileNum}/${totalFiles}: ${file.name}`);
        
        // Update progress for current file
        const baseProgress = (i / totalFiles) * 100;
        setOCRProgress(baseProgress);
        setProcessedFileCount(i);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('extract_client_data', 'true');

        try {
          console.log(`🚀 Uploading file ${currentFileNum}: ${file.name}`);
          
          const response = await axios.post(`${API_BASE_URL}/api/ocr/process`, formData, {
            headers: { 
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 60000 // 60 second timeout per file
          });

          const taskId = response.data.task_id;
          console.log(`✅ File ${currentFileNum} uploaded, task ID: ${taskId}`);
          
          // If processing completed immediately
          if (response.data.status === 'completed') {
            console.log(`✅ File ${currentFileNum} processed immediately`);
            results.push({
              filename: file.name,
              taskId: taskId,
              data: response.data.extracted_data,
              success: true,
              fileNumber: currentFileNum
            });
          } else {
            // Poll for results for this specific file
            console.log(`⏳ Polling results for file ${currentFileNum}: ${file.name}`);
            const result = await pollSingleOCRResult(taskId, file.name, currentFileNum);
            results.push(result);
          }

        } catch (error) {
          console.error(`❌ Error processing file ${currentFileNum} (${file.name}):`, error);
          results.push({
            filename: file.name,
            taskId: null,
            data: null,
            success: false,
            error: error.response?.data?.detail || error.message || 'Processing failed',
            fileNumber: currentFileNum
          });
        }

        completedFiles++;
        // Update progress after each file
        const fileProgress = (completedFiles / totalFiles) * 100;
        setOCRProgress(fileProgress);
        setProcessedFileCount(completedFiles);
        
        console.log(`📊 Progress: ${completedFiles}/${totalFiles} files completed (${fileProgress.toFixed(1)}%)`);
      }

      // Process completed - analyze results
      const successfulResults = results.filter(r => r.success);
      const failedResults = results.filter(r => !r.success);
      
      console.log(`✅ Batch processing complete: ${successfulResults.length}/${totalFiles} successful, ${failedResults.length} failed`);

      if (successfulResults.length === 0) {
        // All files failed
        alert(`❌ All ${totalFiles} files failed to process. Please check the file formats and try again.`);
        setOCRProcessing(false);
        setOCRProgress(0);
        return;
      }

      // Combine results and find best data
      console.log('🔄 Combining results from successful files...');
      const combinedData = combineMultipleOCRResults(results);
      
      const ocrResultData = {
        type: 'multiple',
        totalFiles: totalFiles,
        successfulFiles: successfulResults.length,
        failedFiles: failedResults.length,
        individualResults: results,
        combinedData: combinedData
      };
      
      console.log('📊 Final OCR results:', ocrResultData);
      
      setOCRResults(ocrResultData);
      setExtractedClientData(combinedData);
      setOCRProgress(100);
      setOCRProcessing(false);
      
      if (combinedData && combinedData.confidence_score > 0) {
        console.log('✅ Showing OCR review dialog');
        setShowOCRReviewDialog(true);
      } else {
        alert(`⚠️ Processing completed but no usable data was extracted from any of the ${totalFiles} files. Please try with clearer images or different files.`);
      }

    } catch (error) {
      console.error('❌ Critical error during batch OCR processing:', error);
      setOCRProcessing(false);
      setOCRProgress(0);
      alert(`❌ Critical error processing documents: ${error.message}\n\nPlease try with fewer files or check your connection.`);
    }
  };

  // Poll OCR result for a single file
  const pollSingleOCRResult = async (taskId, filename, fileNumber = 0) => {
    const maxAttempts = 45; // 45 seconds max per file (increased for large batches)
    let attempts = 0;

    console.log(`⏳ Polling OCR result for file ${fileNumber}: ${filename} (task: ${taskId})`);

    return new Promise((resolve) => {
      const poll = async () => {
        try {
          attempts++;
          console.log(`🔍 Polling attempt ${attempts}/${maxAttempts} for file ${fileNumber}: ${filename}`);
          
          const response = await axios.get(`${API_BASE_URL}/api/ocr/result/${taskId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` },
            timeout: 10000 // 10 second timeout per poll
          });

          if (response.data.status === 'completed') {
            console.log(`✅ File ${fileNumber} (${filename}) processing completed successfully`);
            resolve({
              filename: filename,
              taskId: taskId,
              data: response.data.extracted_data,
              success: true,
              fileNumber: fileNumber
            });
          } else if (response.data.status === 'failed') {
            console.error(`❌ File ${fileNumber} (${filename}) processing failed:`, response.data.error);
            resolve({
              filename: filename,
              taskId: taskId,
              data: null,
              success: false,
              error: response.data.error || 'Processing failed',
              fileNumber: fileNumber
            });
          } else if (attempts < maxAttempts) {
            // Still processing, try again
            console.log(`⏳ File ${fileNumber} (${filename}) still processing... (${response.data.status})`);
            setTimeout(poll, 1000);
          } else {
            // Timeout
            console.error(`⏰ File ${fileNumber} (${filename}) processing timeout after ${maxAttempts} attempts`);
            resolve({
              filename: filename,
              taskId: taskId,
              data: null,
              success: false,
              error: `Processing timeout after ${maxAttempts} seconds`,
              fileNumber: fileNumber
            });
          }
        } catch (error) {
          console.error(`❌ Error polling OCR result for file ${fileNumber} (${filename}):`, error);
          if (attempts < maxAttempts && !error.message?.includes('timeout')) {
            // Retry on network errors, but not on timeouts
            setTimeout(poll, 1000);
          } else {
            resolve({
              filename: filename,
              taskId: taskId,
              data: null,
              success: false,
              error: error.message || 'Polling error',
              fileNumber: fileNumber
            });
          }
        }
      };

      poll();
    });
  };

  // Combine OCR results from multiple documents
  const combineMultipleOCRResults = (results) => {
    const successfulResults = results.filter(r => r.success && r.data);
    
    console.log(`🔄 Combining results from ${successfulResults.length} successful files out of ${results.length} total`);
    
    if (successfulResults.length === 0) {
      console.warn('❌ No successful results to combine');
      return null;
    }

    // If only one successful result, return it with proper formatting
    if (successfulResults.length === 1) {
      const result = successfulResults[0];
      console.log(`✅ Single successful result from: ${result.filename}`);
      return {
        ...result.data,
        sources: [result.filename],
        confidence_score: result.data?.confidence_score || 0,
        fieldSources: {}
      };
    }

    // Combine data from multiple sources, preferring higher confidence scores
    const combined = {
      full_name: null,
      date_of_birth: null,
      ndis_number: null,
      plan_start_date: null,
      plan_end_date: null,
      funding_categories: [],
      disability_condition: null,
      address: null,
      mobile: null,
      confidence_score: 0,
      sources: successfulResults.map(r => r.filename),
      fieldSources: {} // Track which file provided each field
    };

    const fieldMappings = [
      'full_name', 'date_of_birth', 'ndis_number', 'plan_start_date', 
      'plan_end_date', 'disability_condition', 'address', 'mobile'
    ];

    // For each field, find the best value from all results
    fieldMappings.forEach(field => {
      let bestValue = null;
      let bestSource = null;
      let bestConfidence = -1;

      successfulResults.forEach(result => {
        const value = result.data?.[field];
        const confidence = result.data?.confidence_score || 0;
        
        if (value && typeof value === 'string' && value.trim() !== '') {
          // Prefer non-empty values with higher confidence
          // Also prefer longer values (more complete information)
          const valueScore = confidence + (value.length * 0.1);
          
          if (bestValue === null || valueScore > bestConfidence) {
            bestValue = value.trim();
            bestSource = result.filename;
            bestConfidence = valueScore;
          }
        }
      });

      if (bestValue) {
        combined[field] = bestValue;
        combined.fieldSources[field] = bestSource;
        console.log(`📄 Field '${field}' = '${bestValue}' from ${bestSource}`);
      }
    });

    // Calculate average confidence, weighted by successful extractions
    const confidenceScores = successfulResults
      .map(r => r.data?.confidence_score || 0)
      .filter(score => score > 0);
    
    if (confidenceScores.length > 0) {
      combined.confidence_score = confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length;
    }

    // Bonus confidence if multiple sources agree on key fields
    const keyFields = ['full_name', 'ndis_number', 'date_of_birth'];
    const foundKeyFields = keyFields.filter(field => combined[field]).length;
    if (foundKeyFields >= 2) {
      combined.confidence_score = Math.min(100, combined.confidence_score * 1.1);
    }

    console.log(`✅ Combined data with ${foundKeyFields}/${keyFields.length} key fields and ${combined.confidence_score.toFixed(1)}% confidence`);
    
    return combined;
  };
  const processOCRDocument = async (file) => {
    if (!file) return;

    setOCRProcessing(true);
    setOCRProgress(0);
    setOCRResults(null);
    setExtractedClientData(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('extract_client_data', 'true');

      const response = await axios.post(`${API_BASE_URL}/api/ocr/process`, formData, {
        headers: { 
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      const taskId = response.data.task_id;
      setOCRTaskId(taskId);
      setOCRProgress(50);

      // If processing completed immediately, get results
      if (response.data.status === 'completed') {
        setOCRResults(response.data);
        setExtractedClientData(response.data.extracted_data);
        setOCRProgress(100);
        setOCRProcessing(false);
        
        if (response.data.extracted_data) {
          setShowOCRReviewDialog(true);
        }
      } else {
        // Poll for results
        pollOCRResults(taskId);
      }

    } catch (error) {
      console.error('Error processing OCR document:', error);
      setOCRProcessing(false);
      setOCRProgress(0);
      alert(`❌ Error processing document: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Poll OCR results
  const pollOCRResults = async (taskId) => {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const response = await axios.get(`${API_BASE_URL}/api/ocr/result/${taskId}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.data.status === 'completed') {
          setOCRResults(response.data);
          setExtractedClientData(response.data.extracted_data);
          setOCRProgress(100);
          setOCRProcessing(false);
          
          if (response.data.extracted_data) {
            setShowOCRReviewDialog(true);
          }
        } else if (response.data.status === 'failed') {
          setOCRProcessing(false);
          setOCRProgress(0);
          alert(`❌ Document processing failed: ${response.data.error || 'Unknown error'}`);
        } else if (attempts < maxAttempts) {
          // Still processing, try again
          setOCRProgress(50 + (attempts * 2)); // Gradual progress increase
          setTimeout(poll, 1000);
        } else {
          // Timeout
          setOCRProcessing(false);
          setOCRProgress(0);
          alert('❌ Document processing timed out. Please try again.');
        }
      } catch (error) {
        console.error('Error polling OCR results:', error);
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
        } else {
          setOCRProcessing(false);
          setOCRProgress(0);
          alert('❌ Error getting processing results. Please try again.');
        }
      }
    };

    poll();
  };

  // Apply OCR data to client profile
  const applyOCRToClient = async (clientId = null) => {
    if (!ocrTaskId) {
      alert('❌ No OCR data available to apply');
      return;
    }

    try {
      const url = clientId 
        ? `${API_BASE_URL}/api/ocr/apply-to-client/${ocrTaskId}?client_id=${clientId}`
        : `${API_BASE_URL}/api/ocr/apply-to-client/${ocrTaskId}`;

      const response = await axios.post(url, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });

      alert(`✅ ${response.data.message}`);
      
      // Refresh clients list
      fetchClients();
      
      // Close dialogs
      setShowOCRReviewDialog(false);
      setShowOCRDialog(false);
      setShowClientDialog(false);
      
      // Reset OCR states
      resetOCRStates();

    } catch (error) {
      console.error('Error applying OCR data:', error);
      alert(`❌ Error applying OCR data: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Reset OCR states
  const resetOCRStates = () => {
    setOCRProcessing(false);
    setOCRResults(null);
    setOCRTaskId(null);
    setOCRProgress(0);
    setExtractedClientData(null);
    setShowOCRReviewDialog(false);
    setSelectedFile(null);
    setCurrentClient(null);
    setProcessedFileCount(0);
    setTotalFileCount(0);
  };

  // Handle file selection for OCR (multiple files)
  const handleOCRFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    // Check for large batches and warn user
    if (files.length > 20) {
      const proceed = window.confirm(
        `⚠️ Large Batch Detected: ${files.length} files selected.\n\n` +
        `Processing many files may take several minutes and could timeout.\n` +
        `For best results, consider processing in smaller batches of 10-20 files.\n\n` +
        `Do you want to continue with all ${files.length} files?`
      );
      
      if (!proceed) {
        // Clear the file input
        event.target.value = '';
        return;
      }
    }

    // Validate all files first
    const maxSize = 50 * 1024 * 1024; // 50MB per file
    const allowedTypes = [
      'application/pdf', 
      'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
      'image/heif', 'image/heic', 'image/heif-sequence', 'image/heic-sequence'
    ];
    
    // Additional iOS/mobile-specific MIME types that are sometimes used
    const mobileCompatibleTypes = [
      'application/octet-stream',  // iOS Safari often uses this for PDFs
      'application/binary',
      'application/download',
      'text/plain'  // Sometimes used by mobile browsers
    ];
    
    const invalidFiles = files.filter(file => {
      const isPdfByExtension = file.name.toLowerCase().endsWith('.pdf');
      const isHeifByExtension = file.name.toLowerCase().endsWith('.heif') || file.name.toLowerCase().endsWith('.heic');
      const isMobileCompatible = mobileCompatibleTypes.includes(file.type) && (isPdfByExtension || isHeifByExtension);
      
      const validType = allowedTypes.includes(file.type) || isMobileCompatible;
      const validSize = file.size <= maxSize;
      
      // Log file details for debugging mobile uploads
      console.log(`File validation: ${file.name}, Type: ${file.type}, Size: ${file.size}, Valid: ${validType && validSize}`);
      
      return !validType || !validSize;
    });

    if (invalidFiles.length > 0) {
      const messages = invalidFiles.slice(0, 5).map(file => { // Show max 5 error examples
        if (!allowedTypes.includes(file.type)) {
          return `${file.name}: Invalid file type`;
        }
        if (file.size > maxSize) {
          return `${file.name}: File too large (max 50MB)`;
        }
        return `${file.name}: Invalid file`;
      });
      
      if (invalidFiles.length > 5) {
        messages.push(`... and ${invalidFiles.length - 5} more files`);
      }
      
      alert(`❌ Invalid files detected (${invalidFiles.length}/${files.length}):\n${messages.join('\n')}\n\nPlease select only PDF or image files (JPG, PNG, TIFF, BMP, HEIF/HEIC) under 50MB each.`);
      
      // Clear the file input
      event.target.value = '';
      return;
    }

    console.log(`Starting OCR processing for ${files.length} files:`, files.map(f => f.name));
    setSelectedFile(files);
    processMultipleOCRDocuments(files);
  };

  // Handle drag and drop for OCR (multiple files)
  const handleOCRDrop = (event) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    if (files.length === 0) return;

    // Check for large batches and warn user
    if (files.length > 20) {
      const proceed = window.confirm(
        `⚠️ Large Batch Detected: ${files.length} files selected.\n\n` +
        `Processing many files may take several minutes and could timeout.\n` +
        `For best results, consider processing in smaller batches of 10-20 files.\n\n` +
        `Do you want to continue with all ${files.length} files?`
      );
      
      if (!proceed) {
        return;
      }
    }

    // Validate all files
    const maxSize = 50 * 1024 * 1024; // 50MB per file
    const allowedTypes = [
      'application/pdf', 
      'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
      'image/heif', 'image/heic', 'image/heif-sequence', 'image/heic-sequence'
    ];
    
    // Additional iOS/mobile-specific MIME types that are sometimes used
    const mobileCompatibleTypes = [
      'application/octet-stream',  // iOS Safari often uses this for PDFs
      'application/binary',
      'application/download',
      'text/plain'  // Sometimes used by mobile browsers
    ];
    
    const invalidFiles = files.filter(file => {
      const isPdfByExtension = file.name.toLowerCase().endsWith('.pdf');
      const isHeifByExtension = file.name.toLowerCase().endsWith('.heif') || file.name.toLowerCase().endsWith('.heic');
      const isMobileCompatible = mobileCompatibleTypes.includes(file.type) && (isPdfByExtension || isHeifByExtension);
      
      const validType = allowedTypes.includes(file.type) || isMobileCompatible;
      const validSize = file.size <= maxSize;
      
      // Log file details for debugging mobile uploads
      console.log(`Drag & Drop validation: ${file.name}, Type: ${file.type}, Size: ${file.size}, Valid: ${validType && validSize}`);
      
      return !validType || !validSize;
    });

    if (invalidFiles.length > 0) {
      const messages = invalidFiles.slice(0, 5).map(file => { // Show max 5 error examples
        if (!allowedTypes.includes(file.type)) {
          return `${file.name}: Invalid file type`;
        }
        if (file.size > maxSize) {
          return `${file.name}: File too large (max 50MB)`;
        }
        return `${file.name}: Invalid file`;
      });
      
      if (invalidFiles.length > 5) {
        messages.push(`... and ${invalidFiles.length - 5} more files`);
      }
      
      alert(`❌ Invalid files detected (${invalidFiles.length}/${files.length}):\n${messages.join('\n')}\n\nPlease select only PDF or image files (JPG, PNG, TIFF, BMP, HEIF/HEIC) under 50MB each.`);
      return;
    }

    console.log(`Starting OCR processing for ${files.length} dropped files:`, files.map(f => f.name));
    setSelectedFile(files);
    processMultipleOCRDocuments(files);
  };

  const handleOCRDragOver = (event) => {
    event.preventDefault();
  };

  // Fetch available users for login dropdown
  const fetchAvailableUsers = async () => {
    try {
      console.log('Fetching available users...');
      // First, get all staff members
      const staffResponse = await axios.get(`${API_BASE_URL}/api/staff`);
      const staffList = staffResponse.data;
      console.log('Staff list fetched:', staffList);
      
      // Create user list with Admin + Staff members
      const users = [
        {
          username: 'Admin',
          displayName: '👤 Admin (Administrator)',
          type: 'admin'
        }
      ];
      
      // Add staff members (convert staff names to likely usernames)
      staffList.forEach(staff => {
        if (staff.active && 
            staff.name && 
            staff.name.trim() !== '' // Filter out staff with empty names
        ) {
          const username = staff.name.toLowerCase().replace(/\s+/g, '');
          users.push({
            username: username,
            displayName: `👥 ${staff.name} (Staff)`,
            type: 'staff',
            staffId: staff.id
          });
        }
      });
      
      console.log('Available users to set:', users);
      setAvailableUsers(users);
    } catch (error) {
      console.error('Error fetching users for dropdown:', error);
      console.log('Falling back to manual input mode');
      // If we can't fetch users, provide at least the Admin user and fall back to manual input
      setAvailableUsers([
        {
          username: 'Admin',
          displayName: '👤 Admin (Administrator)', 
          type: 'admin'
        }
      ]);
      // Don't disable dropdown if we have at least Admin
      // setUseDropdown(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchInitialData();
    fetchAvailableUsers();
    
    // Check for existing authentication
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('currentUser');
    
    if (storedToken && storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setCurrentUser(user);
        setAuthToken(storedToken);
        setIsAuthenticated(true);
        setShowLoginDialog(false);
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      } catch (error) {
        // Clear invalid stored data
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
      }
    }
  }, []);

  // Auto-login as Admin function
  const autoLoginAsAdmin = async () => {
    try {
      console.log('🔐 Auto-logging in as Admin...');
      
      // Check if already authenticated from localStorage first
      const storedToken = localStorage.getItem('authToken');
      const storedUser = localStorage.getItem('currentUser');
      
      if (storedToken && storedUser) {
        try {
          const user = JSON.parse(storedUser);
          if (user.role === 'admin') {
            console.log('✅ Using stored admin credentials');
            setCurrentUser(user);
            setAuthToken(storedToken);
            setIsAuthenticated(true);
            setShowLoginDialog(false);
            axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
            return;
          }
        } catch (e) {
          console.log('Stored credentials invalid, proceeding with fresh login');
          localStorage.removeItem('authToken');
          localStorage.removeItem('currentUser');
        }
      }
      
      // Attempt fresh login
      const loginData = {
        username: "Admin",
        pin: "0000"
      };

      console.log('Making login request to:', `${API_BASE_URL}/api/auth/login`);
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, loginData);
      console.log('Login response:', response.data);
      
      if (response.data.token) {
        const user = response.data.user;
        const token = response.data.token;
        
        // Set authentication state
        setCurrentUser(user);
        setAuthToken(token);
        setIsAuthenticated(true);
        setShowLoginDialog(false); // Hide login dialog
        
        // Store in localStorage for persistence
        localStorage.setItem('authToken', token);
        localStorage.setItem('currentUser', JSON.stringify(user));
        
        // Set default authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        console.log('✅ Auto-login as Admin successful');
        console.log('User:', user);
        console.log('Auth token:', token);
      } else {
        console.error('❌ Auto-login failed: No token received');
        useDirectAdminLogin();
      }
    } catch (error) {
      console.error('❌ Auto-login as Admin failed:', error);
      console.log('API_BASE_URL:', API_BASE_URL);
      useDirectAdminLogin();
    }
  };

  // Direct admin login fallback (no API call)
  const useDirectAdminLogin = () => {
    console.log('🔧 Using direct admin login fallback...');
    
    const mockAdminUser = {
      id: 'admin-direct',
      username: 'Admin',
      role: 'admin',
      name: 'Administrator',
      is_active: true
    };
    
    const mockToken = 'direct-admin-token-' + Date.now();
    
    // Set authentication state directly
    setCurrentUser(mockAdminUser);
    setAuthToken(mockToken);
    setIsAuthenticated(true);
    setShowLoginDialog(false);
    
    // Store in localStorage
    localStorage.setItem('authToken', mockToken);
    localStorage.setItem('currentUser', JSON.stringify(mockAdminUser));
    
    // Set authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;
    
    console.log('✅ Direct admin login successful');
    console.log('User:', mockAdminUser);
  };

  useEffect(() => {
    if (currentDate && isAuthenticated) {
      fetchRosterData();
    }
  }, [currentDate, isAuthenticated]);

  const fetchInitialData = async () => {
    try {
      const [staffRes, templatesRes, settingsRes, rosterTemplatesRes, dayTemplatesRes, eventsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/staff`),
        axios.get(`${API_BASE_URL}/api/shift-templates`),
        axios.get(`${API_BASE_URL}/api/settings`),
        axios.get(`${API_BASE_URL}/api/roster-templates`),
        axios.get(`${API_BASE_URL}/api/day-templates`),
        axios.get(`${API_BASE_URL}/api/calendar-events`)
      ]);
      
      setStaff(staffRes.data);
      setShiftTemplates(templatesRes.data);
      setSettings(settingsRes.data);
      setRosterTemplates(rosterTemplatesRes.data);
      setDayTemplates(dayTemplatesRes.data);
      setCalendarEvents(eventsRes.data);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const fetchRosterData = async () => {
    try {
      const monthString = currentDate.toISOString().slice(0, 7); // YYYY-MM
      
      // Get the first day of the current month to check if we need previous month data
      const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const startOfWeek = new Date(firstDay);
      startOfWeek.setDate(startOfWeek.getDate() - (firstDay.getDay() + 6) % 7); // Start from Monday
      
      // If the first Monday of the week is from the previous month, fetch that data too
      const requests = [axios.get(`${API_BASE_URL}/api/roster?month=${monthString}`)];
      
      if (startOfWeek.getMonth() !== firstDay.getMonth()) {
        const prevMonthString = startOfWeek.toISOString().slice(0, 7);
        requests.push(axios.get(`${API_BASE_URL}/api/roster?month=${prevMonthString}`));
      }
      
      // Also check if we need next month data for the last week
      const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      const endOfWeek = new Date(lastDay);
      endOfWeek.setDate(endOfWeek.getDate() + (7 - lastDay.getDay()) % 7); // End of Sunday
      
      if (endOfWeek.getMonth() !== lastDay.getMonth()) {
        const nextMonthString = endOfWeek.toISOString().slice(0, 7);
        requests.push(axios.get(`${API_BASE_URL}/api/roster?month=${nextMonthString}`));
      }
      
      const responses = await Promise.all(requests);
      const allEntries = responses.flatMap(response => response.data);
      
      setRosterEntries(allEntries);
    } catch (error) {
      console.error('Error fetching roster data:', error);
    }
  };

  const generateMonthlyRoster = async () => {
    if (!window.confirm(`Generate roster for ${currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })} using your saved Shift Times templates?`)) {
      return;
    }

    try {
      const monthString = currentDate.toISOString().slice(0, 7);
      console.log('Generating roster for month:', monthString);
      console.log('Using shift templates:', shiftTemplates);
      
      if (shiftTemplates.length === 0) {
        alert('No shift templates found in Shift Times section. Please create default templates first.');
        return;
      }

      // Generate roster using shift templates from Shift Times section
      const response = await axios.post(`${API_BASE_URL}/api/generate-roster-from-shift-templates/${monthString}`, {
        templates: shiftTemplates
      });
      
      // Check for overlaps and show dialog if any exist
      if (response.data.overlaps_detected && response.data.overlaps_detected > 0) {
        setOverlapData({
          type: 'shift-templates',
          month: monthString,
          templates: shiftTemplates,
          response: response.data,
          message: `Generated roster for ${currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}`
        });
        setShowOverlapDialog(true);
        return; // Don't show success message yet
      }
      
      fetchRosterData();
      
      let message = `Generated roster for ${currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}`;
      if (response.data.entries_created) {
        message += `\n${response.data.entries_created} shifts created`;
      }
      if (response.data.overlaps_detected === 0) {
        message += `\nNo overlapping shifts detected`;
      }
      
      alert(message);
    } catch (error) {
      console.error('Error generating roster:', error);
      
      // Fallback to the old method if new endpoint doesn't exist
      try {
        console.log('Trying fallback method...');
        const monthString = currentDate.toISOString().slice(0, 7);
        await axios.post(`${API_BASE_URL}/api/generate-roster/${monthString}`);
        fetchRosterData();
        alert(`Generated roster for ${currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}`);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        alert(`Error generating roster: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const saveCurrentRosterAsTemplate = async () => {
    if (!newTemplateName.trim()) {
      alert('Please enter a template name');
      return;
    }
    
    try {
      const monthString = currentDate.toISOString().slice(0, 7);
      await axios.post(`${API_BASE_URL}/api/roster-templates/save-current/${encodeURIComponent(newTemplateName)}?month=${monthString}`);
      
      setNewTemplateName('');
      setShowSaveTemplateDialog(false);
      fetchInitialData(); // Reload templates
      alert(`Template "${newTemplateName}" saved successfully!`);
    } catch (error) {
      console.error('Error saving template:', error);
      alert(`Error saving template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const generateRosterFromTemplate = async () => {
    if (!selectedRosterTemplate) {
      alert('Please select a template');
      return;
    }
    
    try {
      const monthString = currentDate.toISOString().slice(0, 7);
      const response = await axios.post(`${API_BASE_URL}/api/generate-roster-from-template/${selectedRosterTemplate}/${monthString}`);
      
      // Check for overlaps and show dialog if any exist
      if (response.data.overlaps_detected && response.data.overlaps_detected > 0) {
        setOverlapData({
          type: 'roster-template',
          month: monthString,
          templateId: selectedRosterTemplate,
          response: response.data,
          message: response.data.message
        });
        setShowOverlapDialog(true);
        return; // Don't close dialog or show success message yet
      }
      
      setShowGenerateFromTemplateDialog(false);
      setSelectedRosterTemplate(null);
      fetchRosterData();
      
      let message = response.data.message;
      if (response.data.overlaps_detected === 0) {
        message += `\n\nNo overlapping shifts detected - all shifts created successfully.`;
      }
      alert(message);
    } catch (error) {
      console.error('Error generating roster from template:', error);
      alert(`Error generating roster: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Handle publishing all shifts including overlaps
  const handlePublishAllShifts = async () => {
    if (!overlapData) return;

    try {
      let response;
      
      if (overlapData.type === 'shift-templates') {
        // Force generate with overlaps for shift templates
        response = await axios.post(`${API_BASE_URL}/api/generate-roster-from-shift-templates/${overlapData.month}`, {
          templates: overlapData.templates,
          force_overlaps: true
        });
      } else if (overlapData.type === 'roster-template') {
        // Force generate with overlaps for roster template
        response = await axios.post(`${API_BASE_URL}/api/generate-roster-from-template/${overlapData.templateId}/${overlapData.month}`, {
          force_overlaps: true
        });
      }

      fetchRosterData();
      setShowOverlapDialog(false);
      setOverlapData(null);
      
      // Close any open dialogs
      setShowGenerateFromTemplateDialog(false);
      setSelectedRosterTemplate(null);

      let message = response.data.message;
      if (response.data.entries_created) {
        message += `\n✅ ${response.data.entries_created} shifts created (including ${response.data.overlaps_detected || 0} overlapping shifts)`;
      }
      
      alert(`🎉 All shifts published!\n\n${message}`);
    } catch (error) {
      console.error('Error publishing all shifts:', error);
      alert(`❌ Error publishing shifts: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Handle skipping overlapping shifts
  const handleSkipOverlapShifts = async () => {
    if (!overlapData) return;

    // The initial response already has the non-overlapping shifts created
    fetchRosterData();
    setShowOverlapDialog(false);
    
    // Close any open dialogs
    setShowGenerateFromTemplateDialog(false);
    setSelectedRosterTemplate(null);

    const response = overlapData.response;
    let message = overlapData.message;
    
    if (response.entries_created) {
      message += `\n✅ ${response.entries_created} shifts created`;
    }
    if (response.overlaps_detected) {
      message += `\n⚠️ ${response.overlaps_detected} overlapping shifts were skipped`;
    }
    
    alert(`📋 Roster published (overlaps skipped)!\n\n${message}`);
    setOverlapData(null);
  };

  const deleteRosterTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this roster template? This action cannot be undone.')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/roster-templates/${templateId}`);
      setSelectedRosterTemplate(null);
      fetchInitialData(); // Reload templates
      alert('Roster template deleted successfully');
    } catch (error) {
      console.error('Error deleting roster template:', error);
      alert(`Error deleting template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const editRosterTemplate = async (templateId) => {
    const template = rosterTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    // Set the selected template for editing and open the comprehensive edit dialog
    setSelectedRosterTemplateForEdit(template);
    setShowTemplateEditDialog(true);
  };

  // Save comprehensive template edits
  const saveRosterTemplateEdits = async () => {
    if (!selectedRosterTemplateForEdit) return;

    try {
      await axios.put(`${API_BASE_URL}/api/roster-templates/${selectedRosterTemplateForEdit.id}`, selectedRosterTemplateForEdit);
      fetchInitialData(); // Reload templates
      setShowTemplateEditDialog(false);
      setSelectedRosterTemplateForEdit(null);
      alert('✅ Template updated successfully with advanced 2:1 shift settings!');
    } catch (error) {
      console.error('Error updating roster template:', error);
      alert(`❌ Error updating template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getTemplateShiftDetails = (template) => {
    if (!template.template_data) return 'No shift data available';
    
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    let shiftCount = 0;
    let details = [];
    
    dayNames.forEach((dayName, dayIndex) => {
      const dayKey = String(dayIndex); // Template data uses string keys
      const dayShifts = template.template_data[dayKey] || [];
      
      if (dayShifts.length > 0) {
        shiftCount += dayShifts.length;
        const shiftTimes = dayShifts.map(shift => 
          `${formatTime(shift.start_time, settings.time_format === '24hr')}-${formatTime(shift.end_time, settings.time_format === '24hr')}${shift.is_sleepover ? ' (Sleepover)' : ''}`
        ).join(', ');
        details.push(`${dayName}: ${shiftTimes}`);
      }
    });
    
    return {
      totalShifts: shiftCount,
      details: details.length > 0 ? details : ['No shifts defined']
    };
  };

  const openDayTemplateDialog = (date, action) => {
    setSelectedDateForTemplate(date);
    setDayTemplateAction(action);
    setShowDayTemplateDialog(true);
    
    if (action === 'save') {
      // Suggest template name based on date
      const dayOfWeek = date.getDay(); // 0=Sunday, 1=Monday, etc.
      const mondayBasedDayIndex = (dayOfWeek + 6) % 7; // Convert to Monday=0 system
      const dayName = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][mondayBasedDayIndex];
      setNewDayTemplateName(`${dayName} Template`);
    }
  };

  const saveDayAsTemplate = async () => {
    if (!newDayTemplateName.trim()) {
      alert('Please enter a template name');
      return;
    }
    
    if (!selectedDateForTemplate) {
      alert('No date selected');
      return;
    }
    
    try {
      const dateString = formatDateString(selectedDateForTemplate);
      await axios.post(`${API_BASE_URL}/api/day-templates/save-day/${encodeURIComponent(newDayTemplateName)}?date=${dateString}`);
      
      setNewDayTemplateName('');
      setShowDayTemplateDialog(false);
      fetchInitialData(); // Reload templates
      alert(`Day template "${newDayTemplateName}" saved successfully!`);
    } catch (error) {
      console.error('Error saving day template:', error);
      alert(`Error saving day template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const applyDayTemplate = async () => {
    if (!selectedDayTemplate) {
      alert('Please select a day template');
      return;
    }
    
    if (!selectedDateForTemplate) {
      alert('No date selected');
      return;
    }
    
    try {
      const dateString = formatDateString(selectedDateForTemplate);
      const response = await axios.post(`${API_BASE_URL}/api/day-templates/apply-to-date/${selectedDayTemplate}?target_date=${dateString}`);
      
      setShowDayTemplateDialog(false);
      setSelectedDayTemplate(null);
      fetchRosterData();
      
      alert(`${response.data.message}\nAdded ${response.data.entries_created} shifts to ${dateString}`);
    } catch (error) {
      console.error('Error applying day template:', error);
      if (error.response?.status === 409) {
        alert(`Cannot apply template: ${error.response.data.detail}`);
      } else {
        alert(`Error applying template: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const addCalendarEvent = async () => {
    if (!newEvent.title || !newEvent.date) {
      alert('Please fill in the title and date');
      return;
    }
    
    try {
      const eventData = {
        id: '',
        ...newEvent,
        attendees: newEvent.attendees.filter(a => a.trim()),
        created_at: new Date().toISOString()
      };
      
      await axios.post(`${API_BASE_URL}/api/calendar-events`, eventData);
      
      setNewEvent({
        title: '',
        description: '',
        date: '',
        start_time: '',
        end_time: '',
        is_all_day: false,
        event_type: 'appointment',
        priority: 'medium',
        location: '',
        attendees: [],
        reminder_minutes: 15
      });
      setShowEventDialog(false);
      fetchInitialData();
    } catch (error) {
      console.error('Error adding event:', error);
      alert(`Error adding event: ${error.response?.data?.detail || error.message}`);
    }
  };

  const updateCalendarEvent = async () => {
    if (!selectedEvent) return;
    
    try {
      await axios.put(`${API_BASE_URL}/api/calendar-events/${selectedEvent.id}`, selectedEvent);
      setShowEventDialog(false);
      setSelectedEvent(null);
      fetchInitialData();
    } catch (error) {
      console.error('Error updating event:', error);
      alert(`Error updating event: ${error.response?.data?.detail || error.message}`);
    }
  };

  const deleteCalendarEvent = async (eventId) => {
    try {
      if (window.confirm('Are you sure you want to delete this event?')) {
        await axios.delete(`${API_BASE_URL}/api/calendar-events/${eventId}`);
        fetchInitialData();
      }
    } catch (error) {
      console.error('Error deleting event:', error);
      alert(`Error deleting event: ${error.response?.data?.detail || error.message}`);
    }
  };

  const completeTask = async (eventId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/calendar-events/${eventId}/complete`);
      fetchInitialData();
    } catch (error) {
      console.error('Error completing task:', error);
      alert(`Error completing task: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Touch/swipe handling functions
  const handleTouchStart = (e, shiftId) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
    setSwipingShiftId(shiftId);
  };

  const handleTouchMove = (e, shiftId) => {
    if (swipingShiftId !== shiftId) return;
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = (e, shiftId) => {
    if (!touchStart || !touchEnd || swipingShiftId !== shiftId) {
      setSwipingShiftId(null);
      return;
    }
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;

    if (isLeftSwipe) {
      // Swipe left to delete
      if (window.confirm('Are you sure you want to delete this shift?')) {
        deleteShift(shiftId);
      }
    }
    
    setSwipingShiftId(null);
    setTouchStart(null);
    setTouchEnd(null);
  };

  // Bulk selection functions
  const toggleShiftSelection = (shiftId) => {
    const newSelected = new Set(selectedShifts);
    if (newSelected.has(shiftId)) {
      newSelected.delete(shiftId);
    } else {
      newSelected.add(shiftId);
    }
    setSelectedShifts(newSelected);
  };

  const selectAllShifts = () => {
    const allShiftIds = new Set(rosterEntries.map(entry => entry.id));
    setSelectedShifts(allShiftIds);
  };

  const clearSelection = () => {
    setSelectedShifts(new Set());
  };

  const getVisibleShifts = () => {
    if (viewMode === 'daily') {
      return getDayEntries(selectedSingleDate || currentDate);
    } else if (viewMode === 'weekly') {
      const startOfWeek = new Date(currentDate);
      const day = startOfWeek.getDay();
      const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1);
      startOfWeek.setDate(diff);
      
      const weekShifts = [];
      for (let i = 0; i < 7; i++) {
        const day = new Date(startOfWeek);
        day.setDate(startOfWeek.getDate() + i);
        weekShifts.push(...getDayEntries(day));
      }
      return weekShifts;
    } else {
      // Monthly view - get current month shifts
      const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      return rosterEntries.filter(entry => {
        const entryDate = new Date(entry.date);
        return entryDate >= monthStart && entryDate <= monthEnd;
      });
    }
  };

  const selectAllVisibleShifts = () => {
    const visibleShifts = getVisibleShifts();
    const visibleShiftIds = new Set(visibleShifts.map(shift => shift.id));
    setSelectedShifts(visibleShiftIds);
  };

  const bulkDeleteShifts = async () => {
    if (selectedShifts.size === 0) {
      alert('No shifts selected');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ${selectedShifts.size} selected shifts?`)) {
      return;
    }

    try {
      const deletePromises = Array.from(selectedShifts).map(shiftId => 
        axios.delete(`${API_BASE_URL}/api/roster/${shiftId}`)
      );
      
      await Promise.all(deletePromises);
      
      setSelectedShifts(new Set());
      setBulkSelectionMode(false);
      fetchRosterData();
      alert(`Successfully deleted ${selectedShifts.size} shifts`);
    } catch (error) {
      console.error('Error deleting shifts:', error);
      alert(`Error deleting shifts: ${error.response?.data?.detail || error.message}`);
    }
  };

  const toggleBulkSelectionMode = () => {
    console.log('Toggling bulk selection mode from:', bulkSelectionMode, 'to:', !bulkSelectionMode);
    setBulkSelectionMode(!bulkSelectionMode);
    setSelectedShifts(new Set());
  };

  const createDefaultShiftTemplates = async () => {
    try {
      // Create default shift templates for each day
      const defaultTemplates = [
        // Monday
        { day_of_week: 0, name: "Morning Shift", start_time: "09:00", end_time: "17:00", is_sleepover: false },
        { day_of_week: 0, name: "Evening Shift", start_time: "17:00", end_time: "01:00", is_sleepover: false },
        // Tuesday
        { day_of_week: 1, name: "Morning Shift", start_time: "09:00", end_time: "17:00", is_sleepover: false },
        { day_of_week: 1, name: "Evening Shift", start_time: "17:00", end_time: "01:00", is_sleepover: false },
        // Wednesday
        { day_of_week: 2, name: "Morning Shift", start_time: "09:00", end_time: "17:00", is_sleepover: false },
        { day_of_week: 2, name: "Evening Shift", start_time: "17:00", end_time: "01:00", is_sleepover: false },
        // Thursday
        { day_of_week: 3, name: "Morning Shift", start_time: "09:00", end_time: "17:00", is_sleepover: false },
        { day_of_week: 3, name: "Evening Shift", start_time: "17:00", end_time: "01:00", is_sleepover: false },
        // Friday
        { day_of_week: 4, name: "Morning Shift", start_time: "09:00", end_time: "17:00", is_sleepover: false },
        { day_of_week: 4, name: "Evening Shift", start_time: "17:00", end_time: "01:00", is_sleepover: false },
        // Saturday
        { day_of_week: 5, name: "Day Shift", start_time: "10:00", end_time: "18:00", is_sleepover: false },
        { day_of_week: 5, name: "Sleepover", start_time: "18:00", end_time: "10:00", is_sleepover: true },
        // Sunday
        { day_of_week: 6, name: "Day Shift", start_time: "10:00", end_time: "18:00", is_sleepover: false },
        { day_of_week: 6, name: "Sleepover", start_time: "18:00", end_time: "10:00", is_sleepover: true },
      ];

      for (const template of defaultTemplates) {
        const templateData = {
          id: '', // Will be auto-generated by backend
          ...template
        };
        await axios.post(`${API_BASE_URL}/api/shift-templates`, templateData);
      }

      fetchInitialData(); // Reload templates
      alert('Default shift templates created successfully!');
    } catch (error) {
      console.error('Error creating default templates:', error);
      alert(`Error creating templates: ${error.response?.data?.detail || error.message}`);
    }
  };

  const createShiftTemplateForDay = async (dayOfWeek) => {
    try {
      const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const templateData = {
        id: '', // Will be auto-generated by backend
        day_of_week: dayOfWeek,
        name: `New Shift`,
        start_time: "09:00",
        end_time: "17:00",
        is_sleepover: false
      };
      
      await axios.post(`${API_BASE_URL}/api/shift-templates`, templateData);
      fetchInitialData(); // Reload templates
      alert(`New shift template created for ${dayNames[dayOfWeek]}`);
    } catch (error) {
      console.error('Error creating shift template:', error);
      alert(`Error creating template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const updateRosterEntry = async (entryId, updates) => {
    try {
      const entry = rosterEntries.find(e => e.id === entryId);
      const updatedEntry = { ...entry, ...updates };
      
      const response = await axios.put(`${API_BASE_URL}/api/roster/${entryId}`, updatedEntry);
      console.log('Updated entry:', response.data);
      fetchRosterData();
    } catch (error) {
      console.error('Error updating roster entry:', error);
    }
  };

  const addStaff = async () => {
    if (!newStaffName.trim()) {
      alert('Please enter a staff name');
      return;
    }
    
    setAddingStaff(true);
    try {
      console.log('Adding staff member:', newStaffName);
      const newStaff = {
        name: newStaffName.trim(),
        active: true
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/staff`, newStaff);
      console.log('Staff added successfully:', response.data);
      
      setNewStaffName('');
      setShowStaffDialog(false);
      fetchInitialData();
      alert(`✅ Staff member "${newStaffName}" added successfully!`);
    } catch (error) {
      console.error('Error adding staff:', error);
      
      // Better error message extraction
      let errorMessage = 'Unknown error occurred';
      
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else {
          errorMessage = JSON.stringify(error.response.data);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Error adding staff: ${errorMessage}`);
    } finally {
      setAddingStaff(false);
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      await axios.put(`${API_BASE_URL}/api/settings`, newSettings);
      setSettings(newSettings);
      setShowSettingsDialog(false);
      // Refresh roster to recalculate pay
      fetchRosterData();
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const updateShiftTemplate = async (templateId, updatedData) => {
    try {
      console.log('Updating shift template:', templateId, updatedData);
      
      // Get the current template to preserve all fields
      const currentTemplate = shiftTemplates.find(t => t.id === templateId);
      if (!currentTemplate) {
        console.error('Template not found:', templateId);
        alert('Template not found');
        return;
      }
      
      // Merge the updated data with current template
      const completeTemplate = {
        ...currentTemplate,
        ...updatedData,
        id: templateId
      };
      
      console.log('Complete template data:', completeTemplate);
      
      const response = await axios.put(`${API_BASE_URL}/api/shift-templates/${templateId}`, completeTemplate);
      console.log('Update response:', response.data);
      
      // Refresh the templates list
      await fetchInitialData();
      alert('Shift template updated successfully!');
    } catch (error) {
      console.error('Error updating shift template:', error);
      alert(`Error updating template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const updateShiftTime = async (entryId, newStartTime, newEndTime) => {
    try {
      const entry = rosterEntries.find(e => e.id === entryId);
      const updatedEntry = { 
        ...entry, 
        start_time: newStartTime, 
        end_time: newEndTime 
      };
      
      await axios.put(`${API_BASE_URL}/api/roster/${entryId}`, updatedEntry);
      fetchRosterData();
    } catch (error) {
      console.error('Error updating shift time:', error);
    }
  };

  const checkShiftBreakViolation = (staffId, staffName, newShift) => {
    if (!staffId || !staffName) return null;

    // Get all shifts for this staff member in the current month
    const staffShifts = rosterEntries.filter(entry => 
      entry.staff_id === staffId && entry.id !== newShift.id
    );

    // Add the new shift to check against
    const allShifts = [...staffShifts, newShift].sort((a, b) => 
      new Date(a.date + 'T' + a.start_time) - new Date(b.date + 'T' + b.start_time)
    );

    for (let i = 0; i < allShifts.length - 1; i++) {
      const currentShift = allShifts[i];
      const nextShift = allShifts[i + 1];

      // Skip if either shift is the new one we're checking
      if (currentShift.id === newShift.id || nextShift.id === newShift.id) {
        // Calculate time between shifts
        const currentEndTime = new Date(currentShift.date + 'T' + currentShift.end_time);
        const nextStartTime = new Date(nextShift.date + 'T' + nextShift.start_time);
        
        // Handle overnight shifts
        if (currentShift.end_time < currentShift.start_time) {
          currentEndTime.setDate(currentEndTime.getDate() + 1);
        }
        if (nextShift.start_time < '12:00' && nextShift.end_time > nextShift.start_time) {
          // Normal day shift starting early
        }

        const timeDiffHours = (nextStartTime - currentEndTime) / (1000 * 60 * 60);

        // Check for violations (less than 10 hours break)
        if (timeDiffHours < 10 && timeDiffHours >= 0) {
          // Check exceptions: sleepover to regular or regular to sleepover
          const currentIsSleepover = currentShift.is_sleepover;
          const nextIsSleepover = nextShift.is_sleepover;
          
          // Allow if going from sleepover to regular or regular to sleepover
          if (currentIsSleepover || nextIsSleepover) {
            continue;
          }

          // Violation found
          return {
            violation: true,
            staffName,
            currentShift,
            nextShift,
            timeBetween: timeDiffHours.toFixed(1),
            message: `${staffName} has only ${timeDiffHours.toFixed(1)} hours break between shifts. Minimum 10 hours required.`,
            details: `${currentShift.date} ${currentShift.start_time}-${currentShift.end_time} → ${nextShift.date} ${nextShift.start_time}-${nextShift.end_time}`
          };
        }
      }
    }

    return null;
  };

  const handleStaffAssignmentWithBreakCheck = (staffId, staffName, shift) => {
    if (!staffId || staffId === "unassigned") {
      // Just unassign
      const updates = {
        staff_id: null,
        staff_name: null,
        start_time: shift.start_time,
        end_time: shift.end_time
      };
      updateRosterEntry(shift.id, updates);
      setShowShiftDialog(false);
      return;
    }

    // Check for break violations
    const violation = checkShiftBreakViolation(staffId, staffName, shift);
    
    if (violation) {
      // Show warning dialog
      setBreakWarningData({
        staffId,
        staffName,
        shift,
        violation
      });
      setShowBreakWarning(true);
    } else {
      // No violation, proceed with assignment
      const updates = {
        staff_id: staffId,
        staff_name: staffName,
        start_time: shift.start_time,
        end_time: shift.end_time
      };
      updateRosterEntry(shift.id, updates);
      setShowShiftDialog(false);
    }
  };

  const approveShiftAssignment = () => {
    if (breakWarningData) {
      const updates = {
        staff_id: breakWarningData.staffId,
        staff_name: breakWarningData.staffName,
        start_time: breakWarningData.shift.start_time,
        end_time: breakWarningData.shift.end_time
      };
      updateRosterEntry(breakWarningData.shift.id, updates);
    }
    setShowBreakWarning(false);
    setBreakWarningData(null);
    setShowShiftDialog(false);
  };

  const denyShiftAssignment = () => {
    setShowBreakWarning(false);
    setBreakWarningData(null);
    // Keep the shift dialog open for user to select different staff
  };

  const clearMonthlyRoster = async () => {
    try {
      const monthString = currentDate.toISOString().slice(0, 7);
      const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
      
      // Use a more reliable confirmation method
      if (window.confirm(`⚠️ CLEAR ENTIRE ROSTER\n\nAre you sure you want to delete ALL shifts for ${monthName}?\n\nThis action cannot be undone!`)) {
        console.log('Clearing roster for month:', monthString);
        const response = await axios.delete(`${API_BASE_URL}/api/roster/month/${monthString}`);
        console.log('Clear roster response:', response.data);
        
        // Show success message
        alert(`✅ Successfully cleared all shifts for ${monthName}\n\n${response.data.message}`);
        fetchRosterData();
      }
    } catch (error) {
      console.error('Error clearing roster:', error);
      alert(`❌ Error clearing roster: ${error.response?.data?.message || error.message}`);
    }
  };

  const addIndividualShift = async () => {
    if (!newShift.date || !newShift.start_time || !newShift.end_time) {
      alert('Please fill in all required fields (date, start time, end time)');
      return;
    }
    
    try {
      const shiftData = {
        id: '', // Will be auto-generated by backend
        date: newShift.date,
        shift_template_id: `custom-${Date.now()}`,
        start_time: newShift.start_time,
        end_time: newShift.end_time,
        is_sleepover: newShift.is_sleepover,
        staff_id: newShift.staff_id,
        staff_name: newShift.staff_name,
        is_public_holiday: false,
        hours_worked: 0.0,
        base_pay: 0.0,
        sleepover_allowance: 0.0,
        total_pay: 0.0,
        allow_overlap: newShift.allow_overlap // Pass the overlap permission
      };
      
      console.log('Adding shift:', shiftData);
      const response = await axios.post(`${API_BASE_URL}/api/roster/add-shift`, shiftData);
      console.log('Shift added successfully:', response.data);
      
      setNewShift({
        date: '',
        start_time: '09:00',
        end_time: '17:00',
        staff_id: null,
        staff_name: null,
        is_sleepover: false,
        allow_overlap: false
      });
      setShowAddShiftDialog(false);
      fetchRosterData();
    } catch (error) {
      console.error('Error adding shift:', error);
      if (error.response?.status === 409) {
        alert(`Cannot add shift: ${error.response.data.detail}\n\nTip: Check "Allow Overlap" if this is a 2:1 shift requiring multiple staff.`);
      } else {
        alert(`Error adding shift: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const deleteShift = async (shiftId) => {
    try {
      if (window.confirm('🗑️ DELETE SHIFT\n\nAre you sure you want to delete this shift?\n\nThis action cannot be undone!')) {
        console.log('Deleting shift:', shiftId);
        const response = await axios.delete(`${API_BASE_URL}/api/roster/${shiftId}`);
        console.log('Delete shift response:', response.data);
        fetchRosterData();
      }
    } catch (error) {
      console.error('Error deleting shift:', error);
      alert(`❌ Error deleting shift: ${error.response?.data?.message || error.message}`);
    }
  };

  // Authentication Functions
  const login = async () => {
    try {
      setAuthError('');
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, loginData);
      
      const { user, token } = response.data;
      
      setCurrentUser(user);
      setAuthToken(token);
      setIsAuthenticated(true);
      setShowLoginDialog(false);
      
      // Fetch roster data now that authentication is complete
      if (currentDate) {
        fetchRosterData();
      }
      
      // Store token in localStorage for persistence
      localStorage.setItem('authToken', token);
      localStorage.setItem('currentUser', JSON.stringify(user));
      
      // Set default axios header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Show PIN change dialog for first login
      if (user.is_first_login) {
        setShowChangePinDialog(true);
      }
      
    } catch (error) {
      setAuthError(error.response?.data?.detail || 'Login failed');
    }
  };

  const changePin = async () => {
    try {
      setAuthError('');
      
      if (changePinData.new_pin !== changePinData.confirm_pin) {
        setAuthError('New PIN and confirmation do not match');
        return;
      }
      
      if (!changePinData.new_pin.match(/^\d{4}$|^\d{6}$/)) {
        setAuthError('PIN must be 4 or 6 digits');
        return;
      }
      
      await axios.post(`${API_BASE_URL}/api/auth/change-pin`, {
        current_pin: changePinData.current_pin,
        new_pin: changePinData.new_pin
      });
      
      setShowChangePinDialog(false);
      setChangePinData({ current_pin: '', new_pin: '', confirm_pin: '' });
      
      // Update user status
      setCurrentUser(prev => ({ ...prev, is_first_login: false }));
      
      alert('✅ PIN changed successfully!');
      
    } catch (error) {
      setAuthError(error.response?.data?.detail || 'Failed to change PIN');
    }
  };

  const logout = async () => {
    try {
      if (authToken) {
        await axios.get(`${API_BASE_URL}/api/auth/logout?token=${authToken}`);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state
      setIsAuthenticated(false);
      setCurrentUser(null);
      setAuthToken(null);
      setShowLoginDialog(true);
      
      // Clear localStorage
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentUser');
      
      // Clear axios header
      delete axios.defaults.headers.common['Authorization'];
    }
  };



  // Helper to navigate dates with timezone awareness
  const navigateDate = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + direction);
    // Ensure we're using Brisbane timezone
    setCurrentDate(getBrisbaneDate(newDate));
  };

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + direction);
    setCurrentDate(getBrisbaneDate(newDate));
  };

  // Helper to navigate dates with timezone awareness for daily view
  const navigateDailyDate = (direction) => {
    const newDate = new Date(selectedSingleDate);
    newDate.setDate(newDate.getDate() + direction);
    // Ensure we're using Brisbane timezone
    setSelectedSingleDate(getBrisbaneDate(newDate));
  };

  // Helper function to get alphabetically sorted active staff
  const getSortedActiveStaff = () => {
    return staff
      .filter(member => member.active)
      .sort((a, b) => a.name.localeCompare(b.name));
  };

  // Quick toggle functions for header controls
  const toggleFirstDayOfWeek = () => {
    const newSettings = {
      ...settings,
      first_day_of_week: settings.first_day_of_week === 'monday' ? 'sunday' : 'monday'
    };
    setSettings(newSettings);
  };

  const toggleTimeFormat = () => {
    const newSettings = {
      ...settings,
      time_format: settings.time_format === '24hr' ? '12hr' : '24hr'
    };
    setSettings(newSettings);
  };

  const toggleDarkMode = () => {
    const newSettings = {
      ...settings,
      dark_mode: !settings.dark_mode
    };
    setSettings(newSettings);
    // Apply dark mode to document root
    if (newSettings.dark_mode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Bulk editing functions for Shift Times
  const toggleTemplateSelection = (templateId) => {
    const newSelection = new Set(selectedTemplates);
    if (newSelection.has(templateId)) {
      newSelection.delete(templateId);
    } else {
      newSelection.add(templateId);
    }
    setSelectedTemplates(newSelection);
  };

  const selectAllTemplates = () => {
    const allTemplateIds = new Set(shiftTemplates.map(template => template.id));
    setSelectedTemplates(allTemplateIds);
  };

  const clearTemplateSelection = () => {
    setSelectedTemplates(new Set());
  };

  const deleteTemplate = async (templateId) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/shift-templates/${templateId}`);
      const updatedTemplates = shiftTemplates.filter(t => t.id !== templateId);
      setShiftTemplates(updatedTemplates);
      alert('✅ Shift template deleted successfully!');
    } catch (error) {
      console.error('Error deleting template:', error);
      alert(`❌ Error deleting template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const deleteSelectedTemplates = async () => {
    if (selectedTemplates.size === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedTemplates.size} selected shift template(s)?`)) {
      try {
        const deletePromises = Array.from(selectedTemplates).map(templateId =>
          axios.delete(`${API_BASE_URL}/api/shift-templates/${templateId}`)
        );
        
        await Promise.all(deletePromises);
        
        const updatedTemplates = shiftTemplates.filter(t => !selectedTemplates.has(t.id));
        setShiftTemplates(updatedTemplates);
        setSelectedTemplates(new Set());
        setBulkEditMode(false);
        alert('✅ Selected shift templates deleted successfully!');
      } catch (error) {
        console.error('Error deleting templates:', error);
        alert(`❌ Error deleting templates: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const cloneTemplate = async (template) => {
    try {
      const clonedTemplate = {
        ...template,
        id: undefined, // Will be auto-generated
        name: `${template.name || 'Shift'} (Copy)`,
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/shift-templates`, clonedTemplate);
      const updatedTemplates = [...shiftTemplates, response.data];
      setShiftTemplates(updatedTemplates);
      alert('✅ Shift template cloned successfully!');
    } catch (error) {
      console.error('Error cloning template:', error);
      alert(`❌ Error cloning template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const applyBulkEdit = async () => {
    if (selectedTemplates.size === 0) return;
    
    try {
      const updatePromises = Array.from(selectedTemplates).map(async (templateId) => {
        const template = shiftTemplates.find(t => t.id === templateId);
        const updatedTemplate = { ...template };
        
        // Apply bulk edit changes
        if (bulkEditData.start_time) updatedTemplate.start_time = bulkEditData.start_time;
        if (bulkEditData.end_time) updatedTemplate.end_time = bulkEditData.end_time;
        if (bulkEditData.shift_type_override) updatedTemplate.shift_type_override = bulkEditData.shift_type_override;
        if (bulkEditData.day_of_week !== '') updatedTemplate.day_of_week = parseInt(bulkEditData.day_of_week);
        updatedTemplate.is_sleepover = bulkEditData.is_sleepover;
        updatedTemplate.allow_overlap = bulkEditData.allow_overlap || false;
        
        return axios.put(`${API_BASE_URL}/api/shift-templates/${templateId}`, updatedTemplate);
      });
      
      const responses = await Promise.all(updatePromises);
      
      // Update local state
      const updatedTemplates = shiftTemplates.map(template => {
        if (selectedTemplates.has(template.id)) {
          const response = responses.find(r => r.data.id === template.id);
          return response ? response.data : template;
        }
        return template;
      });
      
      setShiftTemplates(updatedTemplates);
      setSelectedTemplates(new Set());
      setBulkEditMode(false);
      setShowBulkEditDialog(false);
      setBulkEditData({
        start_time: '',
        end_time: '',
        is_sleepover: false,
        shift_type_override: '',
        day_of_week: '',
        apply_to: 'selected'
      });
      
      alert('✅ Bulk edit applied successfully!');
    } catch (error) {
      console.error('Error applying bulk edit:', error);
      alert(`❌ Error applying bulk edit: ${error.response?.data?.detail || error.message}`);
    }
  };

  // =====================================
  // EXPORT FUNCTIONALITY
  // =====================================

  const exportRosterData = async (format) => {
    try {
      const currentMonth = formatDateString(currentDate).substring(0, 7); // Get YYYY-MM format
      const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
      
      console.log(`Exporting ${format.toUpperCase()} for ${monthName} (${currentMonth})`);
      
      // Make API call to export endpoint
      const response = await axios.get(`${API_BASE_URL}/api/export/${format}/${currentMonth}`, {
        headers: { 
          'Authorization': `Bearer ${authToken}`,
        },
        responseType: 'blob' // Important for file downloads
      });
      
      // Create blob from response data
      const blob = new Blob([response.data], { 
        type: response.headers['content-type'] 
      });
      
      // Get filename from response headers or create default
      const contentDisposition = response.headers['content-disposition'];
      let filename = `roster_export_${monthName.replace(' ', '_')}.${format}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Create download link and trigger download
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      alert(`✅ ${format.toUpperCase()} export completed successfully!`);
      
    } catch (error) {
      console.error(`Export ${format} error:`, error);
      
      let errorMessage = 'Export failed. Please try again.';
      
      if (error.response?.status === 404) {
        errorMessage = 'No roster data found for the current month.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to export data.';
      } else if (error.response?.data) {
        try {
          // Try to parse error message from blob response
          const errorText = await error.response.data.text();
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Fallback if can't parse error
          console.log('Could not parse error response');
        }
      }
      
      alert(`❌ Export failed: ${errorMessage}`);
    }
  };

  const getDayEntries = (date) => {
    // Ensure we're working with a proper date and format it consistently
    const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const dateString = formatDateString(targetDate);
    
    // Filter entries that match this exact date
    const matchingEntries = rosterEntries.filter(entry => {
      return entry.date === dateString;
    });
    
    // Sort shifts by start time
    return matchingEntries.sort((a, b) => {
      const timeA = a.start_time.replace(':', '');
      const timeB = b.start_time.replace(':', '');
      return timeA.localeCompare(timeB);
    });
  };

  const getDayEvents = (date) => {
    const dateString = formatDateString(date);
    return calendarEvents.filter(event => event.date === dateString);
  };

  const getEventPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getEventTypeIcon = (type) => {
    switch (type) {
      case 'meeting': return '👥';
      case 'appointment': return '📅';
      case 'task': return '✓';
      case 'reminder': return '🔔';
      case 'personal': return '👤';
      default: return '📅';
    }
  };

  const getShiftTypeBadge = (entry) => {
    // Check for manual or automatic sleepover status
    const isSleepover = entry.manual_sleepover !== null ? entry.manual_sleepover : entry.is_sleepover;
    
    if (isSleepover) {
      return <Badge variant="secondary" className="bg-indigo-100 text-indigo-800">Sleepover</Badge>;
    }
    
    // If manual shift type is set, use it
    if (entry.manual_shift_type) {
      const typeMap = {
        'weekday_day': { label: 'Day', class: 'bg-green-100 text-green-800' },
        'weekday_evening': { label: 'Evening', class: 'bg-orange-100 text-orange-800' },
        'weekday_night': { label: 'Night', class: 'bg-purple-100 text-purple-800' },
        'saturday': { label: 'Saturday', class: 'bg-blue-100 text-blue-800' },
        'sunday': { label: 'Sunday', class: 'bg-purple-100 text-purple-800' },
        'public_holiday': { label: 'Public Holiday', class: 'bg-red-100 text-red-800' },
        'sleepover': { label: 'Sleepover', class: 'bg-indigo-100 text-indigo-800' }
      };
      const type = typeMap[entry.manual_shift_type];
      return <Badge variant="secondary" className={type.class}>{type.label}</Badge>;
    }
    
    // Simple automatic detection based on date
    const date = new Date(entry.date);
    const dayOfWeek = date.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday
    
    // Weekend check
    if (dayOfWeek === 6) { // Saturday
      return <Badge variant="secondary" className="bg-blue-100 text-blue-800">Saturday</Badge>;
    } else if (dayOfWeek === 0) { // Sunday
      return <Badge variant="secondary" className="bg-purple-100 text-purple-800">Sunday</Badge>;
    }
    
    // Weekday time-based check
    const startHour = parseInt(entry.start_time.split(':')[0]);
    const startMin = parseInt(entry.start_time.split(':')[1]);
    const endHour = parseInt(entry.end_time.split(':')[0]);
    const endMin = parseInt(entry.end_time.split(':')[1]);
    
    // Convert to minutes for more accurate comparison
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    
    // Simple logic for weekdays - shifts ending by 8:00 PM (20:00) are considered "Day"
    if (startHour < 6 || (endMinutes <= startMinutes && endHour > 0)) { // Night or overnight
      return <Badge variant="secondary" className="bg-purple-100 text-purple-800">Night</Badge>;
    } else if (endMinutes > 20 * 60) { // Evening (ends after 8:00 PM / 20:00)
      return <Badge variant="secondary" className="bg-orange-100 text-orange-800">Evening</Badge>;
    } else { // Day (includes shifts ending at or before 8:00 PM / 20:00)
      return <Badge variant="secondary" className="bg-green-100 text-green-800">Day</Badge>;
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(amount);
  };

  // Privacy control: Check if current user should see pay information
  const canViewPayInformation = (entryStaffId = null) => {
    if (!currentUser) return false;
    
    // Admin can see all pay information
    if (currentUser.role === 'admin') return true;
    
    // Staff can see pay for unassigned shifts
    if (!entryStaffId) return true;
    
    // Staff can only see their own pay information for assigned shifts
    if (currentUser.role === 'staff') {
      return currentUser.staff_id === entryStaffId;
    }
    
    return false;
  };

  // Check if current user should see NDIS charge information (Admin only)
  const canViewNDISCharges = () => {
    if (!isAuthenticated || !currentUser) return false;
    return currentUser.role === 'admin';
  };

  // Get appropriate amount to display based on user role
  const getDisplayAmount = (entry, entryStaffId = null) => {
    if (!isAuthenticated || !currentUser || !canViewPayInformation(entryStaffId)) {
      return null; // No pay information visible
    }
    
    // Admin users see NDIS charges, Staff users see staff pay
    if (canViewNDISCharges()) {
      return entry.ndis_total_charge || 0;
    } else {
      return entry.total_pay || 0;
    }
  };

  // Get display text for pay/charge information based on user role and privacy rules
  const getPayDisplayText = (entry, entryStaffId = null) => {
    const amount = getDisplayAmount(entry, entryStaffId);
    
    if (amount === null) {
      return '***'; // Hide information
    }
    
    return formatCurrency(amount);
  };

  // Get appropriate hourly rate for display based on user role
  const getDisplayHourlyRate = (entry) => {
    if (!canViewPayInformation(entry.staff_id)) {
      return null;
    }
    
    // Admin users see NDIS hourly rates, Staff users see staff rates
    if (canViewNDISCharges()) {
      return entry.ndis_hourly_charge || 0;
    } else {
      // Calculate staff hourly rate from total pay and hours
      const hours = entry.hours_worked || 0;
      if (hours > 0) {
        return (entry.total_pay || 0) / hours;
      }
      return 0;
    }
  };

  // Get display text for hourly rates
  const getHourlyRateDisplayText = (entry) => {
    const rate = getDisplayHourlyRate(entry);
    
    if (rate === null) {
      return '***';
    }
    
    return formatCurrency(rate);
  };

  // Get rate type label for display (NDIS vs Staff)
  const getRateTypeLabel = () => {
    if (!isAuthenticated || !currentUser) {
      return 'Pay'; // Fallback when not authenticated
    }
    
    if (canViewNDISCharges()) {
      return 'NDIS Charge';
    } else {
      return 'Staff Pay';
    }
  };

  const getWeeklyTotals = () => {
    const weekStart = new Date(currentDate);
    weekStart.setDate(currentDate.getDate() - currentDate.getDay() + 1); // Monday
    
    const weekEntries = rosterEntries.filter(entry => {
      const entryDate = new Date(entry.date);
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);
      return entryDate >= weekStart && entryDate <= weekEnd;
    });

    const staffTotals = {};
    let totalHours = 0;
    let totalPay = 0;

    weekEntries.forEach(entry => {
      // Only include shifts that have both staff_id AND staff_name (properly assigned shifts)
      // and ensure the staff member is active
      if (entry.staff_id && entry.staff_name) {
        const staffMember = staff.find(s => s.id === entry.staff_id);
        
        // Only count if staff member exists and is active
        if (staffMember && staffMember.active) {
          if (!staffTotals[entry.staff_name]) {
            staffTotals[entry.staff_name] = { hours: 0, pay: 0 };
          }
          staffTotals[entry.staff_name].hours += entry.hours_worked || 0;
          
          // Use appropriate amount based on user role (NDIS for Admin, staff pay for Staff)
          const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0;
          staffTotals[entry.staff_name].pay += displayAmount;
          totalHours += entry.hours_worked || 0;
          totalPay += displayAmount;
        }
      }
    });

    return { staffTotals, totalHours, totalPay };
  };

  const getDailyTotals = (date) => {
    const dayEntries = getDayEntries(date);
    let totalHours = 0;
    let totalPay = 0;
    let assignedShifts = 0;

    dayEntries.forEach(entry => {
      // Only include assigned shifts for both hours and pay calculations
      if (entry.staff_id && entry.staff_name) {
        const staffMember = staff.find(s => s.id === entry.staff_id);
        if (staffMember && staffMember.active) {
          totalHours += entry.hours_worked || 0;
          const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0;
          totalPay += displayAmount;
          assignedShifts++;
        }
      }
    });

    return { 
      totalHours, 
      totalPay, 
      totalShifts: dayEntries.length,
      assignedShifts 
    };
  };

  const getYearToDateTotals = (useFinancialYear = false) => {
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth(); // 0-11
    
    // Determine year boundaries
    let startDate, endDate;
    if (useFinancialYear) {
      // Australian Financial Year: July 1 - June 30
      if (currentMonth >= 6) { // July onwards (months 6-11)
        startDate = new Date(currentYear, 6, 1); // July 1 current year
        endDate = new Date(currentYear + 1, 5, 30); // June 30 next year
      } else { // January - June (months 0-5)
        startDate = new Date(currentYear - 1, 6, 1); // July 1 previous year
        endDate = new Date(currentYear, 5, 30); // June 30 current year
      }
    } else {
      // Calendar Year: January 1 - December 31
      startDate = new Date(currentYear, 0, 1); // January 1
      endDate = new Date(currentYear, 11, 31); // December 31
    }

    // Filter entries for date range
    let ytdEntries = rosterEntries.filter(entry => {
      const entryDate = new Date(entry.date);
      return entryDate >= startDate && entryDate <= endDate;
    });

    // Apply privacy filter for staff users
    if (isStaff() && currentUser?.staff_id) {
      ytdEntries = ytdEntries.filter(entry => entry.staff_id === currentUser.staff_id);
    }

    const staffTotals = {};
    let totalHours = 0;
    let totalPay = 0;

    ytdEntries.forEach(entry => {
      if (entry.staff_id && entry.staff_name) {
        const staffMember = staff.find(s => s.id === entry.staff_id);
        
        if (staffMember && staffMember.active) {
          if (!staffTotals[entry.staff_name]) {
            staffTotals[entry.staff_name] = { 
              hours: 0, 
              pay: 0,
              grossPay: 0,
              afterTaxPay: 0 
            };
          }
          
          const grossPay = entry.total_pay || 0; // Always use staff pay for tax calculations
          const afterTaxPay = calculateAfterTaxPay(grossPay, staffMember);
          const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0; // Display amount for totals
          
          staffTotals[entry.staff_name].hours += entry.hours_worked || 0;
          staffTotals[entry.staff_name].pay += displayAmount; // Use display amount for pay totals
          staffTotals[entry.staff_name].grossPay += grossPay; // Use staff pay for tax calculations
          staffTotals[entry.staff_name].afterTaxPay += afterTaxPay;
          
          totalHours += entry.hours_worked || 0;
          totalPay += displayAmount; // Use display amount for total
        }
      }
    });

    return { 
      staffTotals, 
      totalHours, 
      totalPay,
      startDate,
      endDate,
      period: useFinancialYear ? 'Financial Year' : 'Calendar Year'
    };
  };

  // Simple Australian tax calculation
  const calculateAfterTaxPay = (grossPay, staffMember = null) => {
    // Default Australian tax brackets for 2024-25
    const defaultTaxBrackets = [
      { min: 0, max: 18200, rate: 0 },           // Tax-free threshold
      { min: 18201, max: 45000, rate: 0.19 },   // 19%
      { min: 45001, max: 120000, rate: 0.325 }, // 32.5%
      { min: 120001, max: 180000, rate: 0.37 }, // 37%
      { min: 180001, max: Infinity, rate: 0.45 } // 45%
    ];

    // Use custom tax rate if staff member has one configured
    let taxBrackets = defaultTaxBrackets;
    let superannuationRate = 0.115; // Default 11.5% superannuation
    let customSuperContribution = 0;

    if (staffMember && staffMember.custom_tax_brackets) {
      taxBrackets = staffMember.custom_tax_brackets;
    }

    if (staffMember && staffMember.superannuation_rate !== undefined) {
      superannuationRate = staffMember.superannuation_rate / 100; // Convert percentage
    }

    if (staffMember && staffMember.additional_super_contribution) {
      if (staffMember.super_contribution_type === 'percentage') {
        customSuperContribution = grossPay * (staffMember.additional_super_contribution / 100);
      } else {
        customSuperContribution = staffMember.additional_super_contribution;
      }
    }

    // Annual gross pay (assuming this is annual)
    const annualGross = grossPay;
    
    // Calculate tax
    let tax = 0;
    let remainingIncome = annualGross;
    
    for (const bracket of taxBrackets) {
      if (remainingIncome <= 0) break;
      
      const taxableInThisBracket = Math.min(
        remainingIncome,
        bracket.max - bracket.min + 1
      );
      
      tax += taxableInThisBracket * bracket.rate;
      remainingIncome -= taxableInThisBracket;
    }

    // Calculate superannuation
    const mandatorySuper = grossPay * superannuationRate;
    const totalSuper = mandatorySuper + customSuperContribution;

    // After-tax pay
    const afterTaxPay = grossPay - tax - totalSuper;

    return {
      grossPay,
      tax,
      mandatorySuper,
      customSuperContribution,
      totalSuper,
      afterTaxPay: Math.max(0, afterTaxPay) // Ensure not negative
    };
  };

  const renderCalendarDay = (date) => {
    const dayEntries = getDayEntries(date);
    const dayEvents = getDayEvents(date);
    const dailyTotals = getDailyTotals(date);
    
    // Check if this date is from a different month (previous or next)
    const isCurrentMonth = date.getMonth() === currentDate.getMonth();
    const isPreviousMonth = date < new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const isNextMonth = date > new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    
    // Style classes for different month dates
    const backgroundClass = isCurrentMonth 
      ? 'bg-white' 
      : isPreviousMonth 
        ? 'bg-slate-100' 
        : 'bg-slate-50';
    
    const textClass = isCurrentMonth 
      ? 'text-slate-900' 
      : 'text-slate-500';
    
    // Mobile-responsive classes
    const isMobile = window.innerWidth <= 768;
    
    return (
      <div className={`calendar-day-container p-2 border-r border-b border-slate-200 ${backgroundClass} group hover:bg-slate-50 transition-colors relative`}>
        <div className={`font-medium ${isMobile ? 'text-xs mb-1' : 'text-sm mb-2'} flex items-center justify-between ${textClass} day-number-mobile`}>
          <span>{date.getDate()}</span>
          <div className="flex items-center space-x-1">
            {!isCurrentMonth && (
              <span className="text-xs text-slate-400">
                {isPreviousMonth ? 'Prev' : 'Next'}
              </span>
            )}
            {/* Day Template Buttons and Add Shift - Admin only */}
            {isCurrentMonth && isAdmin() && (
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <button
                  className="w-4 h-4 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors flex items-center justify-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    openDayTemplateDialog(date, 'save');
                  }}
                  title={`Save ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][(date.getDay() + 6) % 7]} as template`}
                  style={{ fontSize: '8px' }}
                >
                  S
                </button>
                <button
                  className="w-4 h-4 bg-green-500 text-white rounded text-xs hover:bg-green-600 transition-colors flex items-center justify-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    openDayTemplateDialog(date, 'load');
                  }}
                  title={`Load template to ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][(date.getDay() + 6) % 7]}`}
                  style={{ fontSize: '8px' }}
                >
                  L
                </button>
                <button
                  className="w-4 h-4 bg-orange-500 text-white rounded text-xs hover:bg-orange-600 transition-colors flex items-center justify-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    setNewShift({
                      ...newShift,
                      date: formatDateString(date)
                    });
                    setShowAddShiftDialog(true);
                  }}
                  title={`Add shift to ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][(date.getDay() + 6) % 7]} ${date.getDate()}`}
                  style={{ fontSize: '8px' }}
                >
                  +
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Dynamic content area that expands with shifts */}
        <div className="calendar-day-content flex-1">
          {/* Calendar Events */}
          {dayEvents.map(event => (
            <div
              key={event.id}
              className={`text-xs p-1 rounded cursor-pointer hover:bg-opacity-80 transition-colors border ${getEventPriorityColor(event.priority)} ${event.is_completed ? 'line-through opacity-60' : ''}`}
              onClick={() => {
                setSelectedEvent(event);
                setShowEventDialog(true);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-medium flex items-center gap-1">
                    <span>{getEventTypeIcon(event.event_type)}</span>
                    <span className="truncate">{event.title}</span>
                  </div>
                  {!event.is_all_day && event.start_time && (
                    <div className="text-xs opacity-75">
                      {formatTime(event.start_time, settings.time_format === '24hr')}{event.end_time && ` - ${formatTime(event.end_time, settings.time_format === '24hr')}`}
                    </div>
                  )}
                </div>
                {event.event_type === 'task' && !event.is_completed && (
                  <button
                    className="w-4 h-4 text-green-600 hover:text-green-800"
                    onClick={(e) => {
                      e.stopPropagation();
                      completeTask(event.id);
                    }}
                    title="Mark as completed"
                  >
                    ✓
                  </button>
                )}
              </div>
            </div>
          ))}
          
          {/* Shift Entries - Dynamic layout that expands */}
          {dayEntries.map(entry => {
            const shiftClasses = isMobile 
              ? "text-xs p-1 mb-1 rounded cursor-pointer hover:bg-slate-200 transition-colors group/shift relative border border-slate-100 shift-entry-mobile"
              : "text-xs p-2 mb-1 rounded cursor-pointer hover:bg-slate-200 transition-colors group/shift relative border border-slate-100";
            
            const timeClasses = isMobile 
              ? "shift-time-mobile font-medium"
              : "font-medium";
            
            return (
              <div
                key={entry.id}
                className={shiftClasses}
              >
                {bulkSelectionMode && (
                  <div className="absolute top-1 left-1 z-30 bg-white rounded p-0.5 shadow-sm border border-slate-300">
                    <input
                      type="checkbox"
                      checked={selectedShifts.has(entry.id)}
                      onChange={() => toggleShiftSelection(entry.id)}
                      className="w-3 h-3 rounded border-gray-300 border-2 text-blue-600 focus:ring-blue-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}
                <div 
                  className={`flex-1 ${bulkSelectionMode ? 'ml-5' : ''}`}
                  onClick={() => {
                    if (!isAdmin()) return; // Staff cannot edit shifts
                    if (bulkSelectionMode) {
                      toggleShiftSelection(entry.id);
                    } else {
                      setSelectedShift(entry);
                      setShowShiftDialog(true);
                    }
                  }}
                  style={{ cursor: isAdmin() ? 'pointer' : 'default' }}
                >
                  <div className="font-medium flex items-center justify-between">
                    <span className={`${isCurrentMonth ? '' : 'opacity-75'} ${timeClasses}`}>
                      {formatTime(entry.start_time, settings.time_format === '24hr')}-{formatTime(entry.end_time, settings.time_format === '24hr')}
                    </span>
                    {!bulkSelectionMode && isAdmin() && (
                      <Edit className="w-3 h-3 opacity-0 group-hover/shift:opacity-100 transition-opacity" />
                    )}
                  </div>
                  
                  {/* Enhanced shift details with hours - Mobile optimized */}
                  <div className={isMobile ? "mt-0.5 space-y-0.5" : "mt-1 space-y-1"}>
                    <div className={`text-slate-600 ${isCurrentMonth ? '' : 'opacity-75'} flex items-center justify-between`}>
                      <span className={isMobile ? "truncate text-xs" : ""}>{entry.staff_name || 'Unassigned'}</span>
                      <span className={`font-medium text-blue-600 ${isMobile ? "text-xs" : "text-xs"}`}>
                        {entry.hours_worked ? `${entry.hours_worked.toFixed(1)}h` : '0h'}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className={isCurrentMonth ? '' : 'opacity-75'}>
                        {getShiftTypeBadge(entry)}
                      </div>
                      <span className={`font-medium text-emerald-600 ${isCurrentMonth ? '' : 'opacity-75'} ${isMobile ? "text-xs" : ""}`}>
                        {getPayDisplayText(entry, entry.staff_id)}
                      </span>
                    </div>
                  </div>
                </div>
                {/* Action buttons - Admin only */}
                {!bulkSelectionMode && isAdmin() && (
                  <button
                    className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover/shift:opacity-100 flex items-center justify-center hover:bg-red-600 transition-all z-10 shadow-sm border border-white"
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      deleteShift(entry.id);
                    }}
                    title="Delete shift"
                    style={{ fontSize: '8px' }}
                  >
                    ✕
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Daily totals footer - positioned to never overlap content */}
        {isCurrentMonth && dayEntries.length > 0 && (
          <div className={`daily-totals-bar ${isMobile 
            ? "text-xs px-1 py-0.5 daily-total-mobile"
            : "text-xs px-2 py-1"
          }`}>
            <div className="flex justify-between items-center">
              <span className="font-medium text-slate-600">
                📊 {dailyTotals.totalShifts} shift{dailyTotals.totalShifts !== 1 ? 's' : ''}
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600 font-medium">
                  {dailyTotals.totalHours.toFixed(1)}h
                </span>
                {dailyTotals.assignedShifts > 0 && canViewPayInformation() && (
                  <span className="text-emerald-600 font-medium">
                    {formatCurrency(dailyTotals.totalPay)}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderDailyView = () => {
    const selectedDate = selectedSingleDate || currentDate;
    const dayEntries = getDayEntries(selectedDate);
    const dayEvents = getDayEvents(selectedDate);
    
    // Calculate day total based on user role - ONLY for assigned shifts
    const dayTotal = dayEntries.reduce((sum, entry) => {
      // Only count shifts that are assigned to staff members
      if (!entry.staff_id || !entry.staff_name) {
        return sum; // Skip unassigned shifts
      }
      
      if (isStaff() && entry.staff_id !== currentUser?.staff_id) {
        return sum; // Staff users don't see other staff's pay in totals
      }
      const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0;
      return sum + displayAmount;
    }, 0);
    
    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {/* Daily View Header */}
        <div className="bg-slate-50 p-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => navigateDailyDate(-1)}
              >
                Previous Day
              </Button>
              <h2 className="text-2xl font-bold text-slate-800">
                {selectedDate.toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </h2>
              <Button
                variant="outline"
                onClick={() => navigateDailyDate(1)}
              >
                Next Day
              </Button>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                onClick={() => {
                  setNewShift({
                    ...newShift,
                    date: formatDateString(selectedDate)
                  });
                  setShowAddShiftDialog(true);
                }}
              >
                Add Shift
              </Button>
              <Button
                variant="outline"
                onClick={() => setSelectedSingleDate(new Date())}
              >
                Today
              </Button>
            </div>
          </div>
        </div>

        {/* Daily Content */}
        <div className="p-6 space-y-6">
          {/* Events Section */}
          {dayEvents.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Events & Appointments</h3>
              <div className="space-y-2">
                {dayEvents.map(event => (
                  <div
                    key={event.id}
                    className={`p-3 rounded-lg border cursor-pointer hover:bg-opacity-80 transition-colors ${getEventPriorityColor(event.priority)} ${event.is_completed ? 'line-through opacity-60' : ''}`}
                    onClick={() => {
                      setSelectedEvent(event);
                      setShowEventDialog(true);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getEventTypeIcon(event.event_type)}</span>
                        <div>
                          <div className="font-medium">{event.title}</div>
                          {!event.is_all_day && event.start_time && (
                            <div className="text-sm opacity-75">
                              {formatTime(event.start_time, settings.time_format === '24hr')}{event.end_time && ` - ${formatTime(event.end_time, settings.time_format === '24hr')}`}
                            </div>
                          )}
                          {event.location && (
                            <div className="text-sm opacity-75">📍 {event.location}</div>
                          )}
                        </div>
                      </div>
                      {event.event_type === 'task' && !event.is_completed && (
                        <button
                          className="px-2 py-1 text-green-600 hover:text-green-800 border border-green-300 rounded"
                          onClick={(e) => {
                            e.stopPropagation();
                            completeTask(event.id);
                          }}
                        >
                          Mark Done
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Shifts Section */}
          {dayEntries.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Work Shifts</h3>
              <div className="space-y-3">
                {dayEntries.map(entry => {
                  const isSwipingThis = swipingShiftId === entry.id;
                  const swipeProgress = isSwipingThis && touchStart && touchEnd ? 
                    Math.max(0, Math.min(100, ((touchStart - touchEnd) / 100) * 100)) : 0;
                  
                  return (
                    <div
                      key={entry.id}
                      className={`p-4 border rounded-lg hover:bg-slate-50 transition-all duration-200 group relative shift-entry ${isSwipingThis ? 'swipe-indicator' : ''} ${selectedShifts.has(entry.id) ? 'ring-2 ring-blue-500 bg-blue-50' : ''}`}
                      style={{
                        transform: isSwipingThis ? `translateX(-${swipeProgress * 0.5}px)` : 'none',
                        opacity: isSwipingThis ? Math.max(0.7, 1 - (swipeProgress / 100)) : 1
                      }}
                      onTouchStart={(e) => !bulkSelectionMode && handleTouchStart(e, entry.id)}
                      onTouchMove={(e) => !bulkSelectionMode && handleTouchMove(e, entry.id)}
                      onTouchEnd={(e) => !bulkSelectionMode && handleTouchEnd(e, entry.id)}
                    >
                      {bulkSelectionMode && (
                        <div className="absolute top-2 left-2 z-30 bg-white rounded-full p-1 shadow-sm border border-slate-300">
                          <input
                            type="checkbox"
                            checked={selectedShifts.has(entry.id)}
                            onChange={() => toggleShiftSelection(entry.id)}
                            className="w-4 h-4 rounded border-gray-300 border-2 text-blue-600 focus:ring-blue-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      )}
                      
                      <div 
                        className={`flex-1 ${isAdmin() ? 'cursor-pointer' : 'cursor-default'} ${bulkSelectionMode ? 'ml-6' : ''}`}
                        onClick={() => {
                          if (!isAdmin()) return; // Staff cannot edit shifts
                          if (bulkSelectionMode) {
                            toggleShiftSelection(entry.id);
                          } else {
                            setSelectedShift(entry);
                            setShowShiftDialog(true);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className="text-xl font-bold text-slate-700">
                              {formatTime(entry.start_time, settings.time_format === '24hr')} - {formatTime(entry.end_time, settings.time_format === '24hr')}
                            </div>
                            <div>
                              {getShiftTypeBadge(entry)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-emerald-600">
                              {getPayDisplayText(entry, entry.staff_id)}
                            </div>
                            <div className="text-sm text-slate-600">
                              {entry.staff_name || 'Unassigned'}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Swipe indicator */}
                      {isSwipingThis && swipeProgress > 20 && (
                        <div className="absolute inset-0 flex items-center justify-center bg-red-100 border-2 border-red-300 rounded-lg">
                          <div className="text-red-600 font-bold">
                            Swipe left to delete
                          </div>
                        </div>
                      )}
                      
                      {/* Action buttons - Admin only */}
                      {!bulkSelectionMode && isAdmin() && (
                        <button
                          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-sm opacity-0 group-hover:opacity-100 mobile-delete-hover flex items-center justify-center hover:bg-red-600 transition-all z-20 shadow-sm border border-white"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm('Are you sure you want to delete this shift?')) {
                              deleteShift(entry.id);
                            }
                          }}
                          title="Delete shift"
                          style={{ fontSize: '12px', lineHeight: '1' }}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                <div className="text-lg font-bold text-emerald-700">
                  Daily Total ({getRateTypeLabel()}): {canViewPayInformation() ? formatCurrency(dayTotal) : '***'}
                </div>
              </div>
            </div>
          )}

          {dayEntries.length === 0 && dayEvents.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-4">📅</div>
              <div className="text-lg">No shifts or events scheduled for this day</div>
              <div className="mt-4 space-x-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setNewShift({
                      ...newShift,
                      date: formatDateString(selectedDate)
                    });
                    setShowAddShiftDialog(true);
                  }}
                >
                  Add Shift
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setNewEvent({
                      ...newEvent,
                      date: formatDateString(selectedDate)
                    });
                    setShowEventDialog(true);
                  }}
                >
                  Add Event
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderWeeklyView = () => {
    const startOfWeek = new Date(currentDate);
    const day = startOfWeek.getDay();
    
    let diff;
    if (settings.first_day_of_week === 'sunday') {
      diff = startOfWeek.getDate() - day; // Sunday start
    } else {
      diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Monday start
    }
    startOfWeek.setDate(diff);

    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      weekDays.push(day);
    }

    // Week day headers based on first day of week setting
    const weekHeaders = settings.first_day_of_week === 'sunday' 
      ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {/* Weekly View Header */}
        <div className="bg-slate-50 p-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => {
                  const newDate = new Date(currentDate);
                  newDate.setDate(newDate.getDate() - 7);
                  setCurrentDate(newDate);
                }}
              >
                Previous Week
              </Button>
              <h2 className="text-2xl font-bold text-slate-800">
                {startOfWeek.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - {weekDays[6].toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              </h2>
              <Button
                variant="outline"
                onClick={() => {
                  const newDate = new Date(currentDate);
                  newDate.setDate(newDate.getDate() + 7);
                  setCurrentDate(newDate);
                }}
              >
                Next Week
              </Button>
            </div>
          </div>
        </div>

        {/* Weekly Grid */}
        <div className="grid grid-cols-7 divide-x divide-slate-200">
          {weekDays.map((date, index) => {
            const dayEntries = getDayEntries(date);
            const dayEvents = getDayEvents(date);
            
            // Calculate day total based on user role - ONLY for assigned shifts
            const dayTotal = dayEntries.reduce((sum, entry) => {
              // Only count shifts that are assigned to staff members
              if (!entry.staff_id || !entry.staff_name) {
                return sum; // Skip unassigned shifts
              }
              
              if (isStaff() && entry.staff_id !== currentUser?.staff_id) {
                return sum; // Staff users don't see other staff's pay in totals
              }
              const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0;
              return sum + displayAmount;
            }, 0);
            
            const isToday = date.toDateString() === new Date().toDateString();

            return (
              <div key={index} className={`min-h-[400px] p-3 ${isToday ? 'bg-blue-50' : ''}`}>
                <div className={`text-center mb-3 ${isToday ? 'font-bold text-blue-600' : 'font-medium text-slate-700'}`}>
                  <div className="text-sm">
                    {weekHeaders[index]}
                  </div>
                  <div className={`text-lg ${isToday ? 'bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto' : ''}`}>
                    {date.getDate()}
                  </div>
                </div>

                {/* Quick Add Shift Button */}
                <div className="mb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      setNewShift({
                        ...newShift,
                        date: formatDateString(date)
                      });
                      setShowAddShiftDialog(true);
                    }}
                  >
                    + Add Shift
                  </Button>
                </div>

                <div className="space-y-1">
                  {/* Events */}
                  {dayEvents.map(event => (
                    <div
                      key={event.id}
                      className={`text-xs p-1 rounded cursor-pointer border ${getEventPriorityColor(event.priority)} ${event.is_completed ? 'line-through opacity-60' : ''}`}
                      onClick={() => {
                        setSelectedEvent(event);
                        setShowEventDialog(true);
                      }}
                    >
                      <div className="font-medium truncate">{getEventTypeIcon(event.event_type)} {event.title}</div>
                      {!event.is_all_day && event.start_time && (
                        <div className="opacity-75">{event.start_time}</div>
                      )}
                    </div>
                  ))}

                  {/* Shifts */}
                  {dayEntries.map(entry => (
                    <div
                      key={entry.id}
                      className={`text-xs p-1 rounded cursor-pointer hover:bg-slate-200 transition-colors border border-slate-200 group relative ${selectedShifts.has(entry.id) ? 'ring-1 ring-blue-500 bg-blue-50' : ''}`}
                    >
                      {bulkSelectionMode && (
                        <div className="absolute top-0 left-0 z-30 bg-white rounded p-0.5 shadow-sm border border-slate-300">
                          <input
                            type="checkbox"
                            checked={selectedShifts.has(entry.id)}
                            onChange={() => toggleShiftSelection(entry.id)}
                            className="w-3 h-3 rounded border-gray-300 border-2 text-blue-600 focus:ring-blue-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      )}
                      <div
                        className={`${bulkSelectionMode ? 'ml-3' : ''} ${isAdmin() ? 'cursor-pointer' : 'cursor-default'}`}
                        onClick={() => {
                          if (!isAdmin()) return; // Staff cannot edit shifts
                          if (bulkSelectionMode) {
                            toggleShiftSelection(entry.id);
                          } else {
                            setSelectedShift(entry);
                            setShowShiftDialog(true);
                          }
                        }}
                      >
                        <div className="font-medium">{formatTime(entry.start_time, settings.time_format === '24hr')}-{formatTime(entry.end_time, settings.time_format === '24hr')}</div>
                        <div className="text-slate-600 truncate">{entry.staff_name || 'Unassigned'}</div>
                        <div className="font-medium text-emerald-600">{getPayDisplayText(entry, entry.staff_id)}</div>
                      </div>
                      {/* Action buttons - Admin only */}
                      {!bulkSelectionMode && isAdmin() && (
                        <button
                          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 flex items-center justify-center hover:bg-red-600 transition-all z-10 shadow-sm border border-white"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm('Are you sure you want to delete this shift?')) {
                              deleteShift(entry.id);
                            }
                          }}
                          title="Delete shift"
                          style={{ fontSize: '8px', lineHeight: '1' }}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {dayTotal > 0 && (
                  <div className="mt-2 pt-1 border-t border-slate-200 text-xs font-bold text-emerald-700">
                    ${dayTotal.toFixed(0)} ({getRateTypeLabel()})
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Calendar View (Traditional Monthly Grid)
  const renderCalendarView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // Start from first day of week (Monday or Sunday) containing the first day
    const startDate = new Date(firstDay);
    const firstDayOfWeek = firstDay.getDay(); // 0 = Sunday, 1 = Monday, etc.
    
    let daysToSubtract;
    if (settings.first_day_of_week === 'sunday') {
      daysToSubtract = firstDayOfWeek; // Sunday = 0 system
    } else {
      daysToSubtract = (firstDayOfWeek + 6) % 7; // Convert to Monday = 0 system
    }
    
    startDate.setDate(startDate.getDate() - daysToSubtract);

    const weeks = [];
    const currentWeekDate = new Date(startDate);

    // Always generate exactly 6 weeks for a complete calendar view
    for (let weekNum = 0; weekNum < 6; weekNum++) {
      const week = [];
      for (let dayNum = 0; dayNum < 7; dayNum++) {
        // Create a clean date object to avoid timezone issues
        const dayDate = new Date(currentWeekDate.getFullYear(), currentWeekDate.getMonth(), currentWeekDate.getDate());
        week.push(dayDate);
        currentWeekDate.setDate(currentWeekDate.getDate() + 1);
      }
      weeks.push(week);
    }

    // Week day headers based on first day of week setting
    const weekHeaders = settings.first_day_of_week === 'sunday' 
      ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {/* Mobile-responsive week headers */}
        <div className="grid grid-cols-7 bg-slate-50">
          {weekHeaders.map(day => (
            <div key={day} className="p-2 sm:p-3 text-center font-semibold text-slate-700 border-r border-slate-200 last:border-r-0 text-xs sm:text-sm calendar-header">
              {day}
            </div>
          ))}
        </div>
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="calendar-grid">
            {week.map((date, dayIndex) => {
              const dateKey = `${weekIndex}-${dayIndex}-${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
              return (
                <div key={dateKey}>
                  {renderCalendarDay(date)}
                </div>
              );
            })}
          </div>
        ))}
        
        {/* Legend for different month indicators - Mobile responsive */}
        <div className="p-2 sm:p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-center space-x-3 sm:space-x-6 text-xs text-slate-600">
          <div className="flex items-center space-x-1 sm:space-x-2">
            <div className="w-2 h-2 sm:w-3 sm:h-3 bg-white border border-slate-300 rounded"></div>
            <span>Current</span>
          </div>
          <div className="flex items-center space-x-1 sm:space-x-2">
            <div className="w-2 h-2 sm:w-3 sm:h-3 bg-slate-100 border border-slate-300 rounded"></div>
            <span>Previous</span>
          </div>
          <div className="flex items-center space-x-1 sm:space-x-2">
            <div className="w-2 h-2 sm:w-3 sm:h-3 bg-slate-50 border border-slate-300 rounded"></div>
            <span>Next</span>
          </div>
        </div>
      </div>
    );
  };

  const renderMonthlyCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Get all days of the month
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    
    // Generate all days of the month
    const monthDays = [];
    for (let day = 1; day <= daysInMonth; day++) {
      monthDays.push(new Date(year, month, day));
    }

    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {/* Header with navigation */}
        <div className="bg-slate-50 p-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => navigateMonth(-1)}
              >
                Previous Month
              </Button>
              <h2 className="text-2xl font-bold text-slate-800">
                {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
              </h2>
              <Button
                variant="outline"
                onClick={() => navigateMonth(1)}
              >
                Next Month
              </Button>
            </div>
          </div>
        </div>

        {/* Horizontally scrollable month view */}
        <div className="overflow-x-auto">
          <div className="flex min-w-max">
            {monthDays.map((date, index) => {
              const dayEntries = getDayEntries(date);
              const dayEvents = getDayEvents(date);
              
              // Calculate day total based on user role - ONLY for assigned shifts
              const dayTotal = dayEntries.reduce((sum, entry) => {
                // Only count shifts that are assigned to staff members
                if (!entry.staff_id || !entry.staff_name) {
                  return sum; // Skip unassigned shifts
                }
                
                if (isStaff() && entry.staff_id !== currentUser?.staff_id) {
                  return sum; // Staff users don't see other staff's pay in totals
                }
                const displayAmount = getDisplayAmount(entry, entry.staff_id) || 0;
                return sum + displayAmount;
              }, 0);
              
              const isToday = date.toDateString() === getBrisbaneDate().toDateString();
              const dayOfWeek = (date.getDay() + 6) % 7; // Convert to Monday = 0
              
              // Get day names based on first day of week setting
              let dayNames;
              let adjustedDayOfWeek;
              
              if (settings.first_day_of_week === 'sunday') {
                dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                adjustedDayOfWeek = date.getDay(); // Sunday = 0
              } else {
                dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                adjustedDayOfWeek = (date.getDay() + 6) % 7; // Monday = 0
              }

              return (
                <div key={index} className={`min-h-[400px] p-3 border-r border-slate-200 last:border-r-0 min-w-[180px] ${isToday ? 'bg-blue-50' : ''}`}>
                  {/* Day header */}
                  <div className={`text-center mb-3 ${isToday ? 'font-bold text-blue-600' : 'font-medium text-slate-700'}`}>
                    <div className="text-sm">
                      {dayNames[adjustedDayOfWeek]}
                    </div>
                    <div className={`text-lg ${isToday ? 'bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto' : ''}`}>
                      {date.getDate()}
                    </div>
                  </div>

                  {/* Quick Add Shift Button */}
                  <div className="mb-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs"
                      onClick={() => {
                        setNewShift({
                          ...newShift,
                          date: formatDateString(date)
                        });
                        setShowAddShiftDialog(true);
                      }}
                    >
                      + Add Shift
                    </Button>
                  </div>

                  <div className="space-y-1">
                    {/* Events */}
                    {dayEvents.map(event => (
                      <div
                        key={event.id}
                        className={`text-xs p-1 rounded cursor-pointer border ${getEventPriorityColor(event.priority)} ${event.is_completed ? 'line-through opacity-60' : ''}`}
                        onClick={() => {
                          setSelectedEvent(event);
                          setShowEventDialog(true);
                        }}
                      >
                        <div className="font-medium truncate">{getEventTypeIcon(event.event_type)} {event.title}</div>
                        {!event.is_all_day && event.start_time && (
                          <div className="text-xs opacity-75">
                            {formatTime(event.start_time, settings.time_format === '24hr')}{event.end_time && ` - ${formatTime(event.end_time, settings.time_format === '24hr')}`}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Shifts */}
                    {dayEntries.map(entry => (
                      <div
                        key={entry.id}
                        className={`text-xs p-1 rounded cursor-pointer hover:bg-slate-200 transition-colors border border-slate-200 group relative ${selectedShifts.has(entry.id) ? 'ring-1 ring-blue-500 bg-blue-50' : ''}`}
                      >
                        {bulkSelectionMode && (
                          <div className="absolute top-0 left-0 z-30 bg-white rounded p-0.5 shadow-sm border border-slate-300">
                            <input
                              type="checkbox"
                              checked={selectedShifts.has(entry.id)}
                              onChange={() => toggleShiftSelection(entry.id)}
                              className="w-3 h-3 rounded border-gray-300 border-2 text-blue-600 focus:ring-blue-500"
                              onClick={(e) => e.stopPropagation()}
                            />
                          </div>
                        )}
                        <div
                          className={`${bulkSelectionMode ? 'ml-3' : ''} ${isAdmin() ? 'cursor-pointer' : 'cursor-default'}`}
                          onClick={() => {
                            if (!isAdmin()) return; // Staff cannot edit shifts
                            if (bulkSelectionMode) {
                              toggleShiftSelection(entry.id);
                            } else {
                              setSelectedShift(entry);
                              setShowShiftDialog(true);
                            }
                          }}
                        >
                          <div className="font-medium">{formatTime(entry.start_time, settings.time_format === '24hr')}-{formatTime(entry.end_time, settings.time_format === '24hr')}</div>
                          <div className="text-slate-600 truncate">{entry.staff_name || 'Unassigned'}</div>
                          <div className="font-medium text-emerald-600">{getPayDisplayText(entry, entry.staff_id)}</div>
                        </div>
                        {/* Action buttons - Admin only */}
                        {!bulkSelectionMode && isAdmin() && (
                          <button
                            className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 flex items-center justify-center hover:bg-red-600 transition-all z-10 shadow-sm border border-white"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm('Are you sure you want to delete this shift?')) {
                                deleteShift(entry.id);
                              }
                            }}
                            title="Delete shift"
                            style={{ fontSize: '8px', lineHeight: '1' }}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Day total */}
                  {dayTotal > 0 && (
                    <div className="mt-2 pt-1 border-t border-slate-200 text-xs font-bold text-emerald-700">
                      ${dayTotal.toFixed(0)} ({getRateTypeLabel()})
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const { staffTotals, totalHours, totalPay } = getWeeklyTotals();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {!isAuthenticated ? (
        // Login interface - this will be handled by the login dialog
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-slate-800 mb-4">Shift Roster & Pay Calculator</h1>
            <p className="text-slate-600">Please log in to continue</p>
          </div>
        </div>
      ) : (
        // Main application interface - only show when authenticated
        <div className="container mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Shift Roster & Pay Calculator</h1>
            <p className="text-slate-600">Professional workforce management system</p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="px-3 py-1">
              {settings.pay_mode === 'default' ? 'Default Pay' : 'SCHADS Award'}
            </Badge>
            {/* Profile Button */}
            {isAuthenticated && currentUser && (
              <Button
                variant="outline"
                onClick={() => {
                  if (isStaff()) {
                    setShowStaffSelfProfileDialog(true);
                  } else {
                    setShowProfileDialog(true);
                  }
                }}
                className="flex items-center space-x-2"
              >
                <User className="w-4 h-4" />
                <span>{currentUser.first_name || currentUser.username}</span>
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => setShowSettingsDialog(true)}
            >
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            {/* Logout Button */}
            {isAuthenticated && (
              <Button
                variant="outline"
                onClick={logout}
                className="text-red-600 hover:text-red-700"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            )}
          </div>
          
          {/* Quick Settings Toggle Buttons */}
          <div className="flex items-center justify-center space-x-3 mt-3 pt-3 border-t border-slate-200">
            {/* Mon First/Sun First button - Admin only */}
            {isAdmin() && (
              <Button
                variant={settings.first_day_of_week === 'monday' ? 'default' : 'outline'}
                size="sm"
                onClick={toggleFirstDayOfWeek}
                className="text-xs"
              >
                {settings.first_day_of_week === 'monday' ? '📅 Mon First' : '📅 Sun First'}
              </Button>
            )}
            
            <Button
              variant={settings.time_format === '24hr' ? 'default' : 'outline'}
              size="sm"
              onClick={toggleTimeFormat}
              className="text-xs"
            >
              {settings.time_format === '24hr' ? '🕐 24hr' : '🕐 12hr'}
            </Button>
            
            <Button
              variant={settings.dark_mode ? 'default' : 'outline'}
              size="sm"
              onClick={toggleDarkMode}
              className="text-xs"
            >
              {settings.dark_mode ? '🌙 Dark' : '☀️ Light'}
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="roster" className="flex items-center space-x-2">
              <CalendarIcon className="w-4 h-4" />
              <span>Roster</span>
            </TabsTrigger>
            <TabsTrigger value="shifts" className="flex items-center space-x-2">
              <Clock className="w-4 h-4" />
              <span>Shift Times</span>
            </TabsTrigger>
            <TabsTrigger value="availability" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Shift & Staff Availability</span>
            </TabsTrigger>
            <TabsTrigger value="clients" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Client Profiles</span>
            </TabsTrigger>
            <TabsTrigger value="staff" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Staff</span>
            </TabsTrigger>
            <TabsTrigger value="pay" className="flex items-center space-x-2">
              <DollarSign className="w-4 h-4" />
              <span>Pay Summary</span>
            </TabsTrigger>
            <TabsTrigger value="export" className="flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Export</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="roster" className="space-y-6">
            {/* View Mode Selector */}
            <Card>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
                    <Label className="font-medium text-sm">View:</Label>
                    <div className="flex flex-wrap gap-1 view-selector">
                      <Button
                        variant={viewMode === 'daily' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('daily')}
                        className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      >
                        Daily
                      </Button>
                      <Button
                        variant={viewMode === 'weekly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('weekly')}
                        className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      >
                        Weekly
                      </Button>
                      <Button
                        variant={viewMode === 'monthly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('monthly')}
                        className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      >
                        Monthly
                      </Button>
                      <Button
                        variant={viewMode === 'calendar' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('calendar')}
                        className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      >
                        Calendar
                      </Button>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs sm:text-sm px-2 sm:px-3 py-1.5 whitespace-nowrap"
                    onClick={() => {
                      setNewEvent({
                        ...newEvent,
                        date: currentDate.toISOString().split('T')[0]
                      });
                      setShowEventDialog(true);
                    }}
                  >
                    <Plus className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    <span className="hidden sm:inline">Add Event</span>
                    <span className="sm:hidden">Add</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Month Navigation - Mobile Responsive */}
            <Card>
              <CardContent className="p-3 sm:p-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0 month-navigation">
                  <div className="flex items-center space-x-2 sm:space-x-4 w-full sm:w-auto justify-center sm:justify-start">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      onClick={() => navigateMonth(-1)}
                    >
                      <span className="sm:hidden">← Prev</span>
                      <span className="hidden sm:inline">Previous Month</span>
                    </Button>
                    <h2 className="text-lg sm:text-2xl font-bold text-slate-800 text-center sm:text-left">
                      {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
                    </h2>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs sm:text-sm px-2 sm:px-3 py-1.5"
                      onClick={() => navigateMonth(1)}
                    >
                      <span className="sm:hidden">Next →</span>
                      <span className="hidden sm:inline">Next Month</span>
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {/* First row of buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {/* Admin-only roster management buttons */}
                        {isAdmin() && (
                          <Button
                            variant={bulkSelectionMode ? "default" : "outline"}
                            onClick={toggleBulkSelectionMode}
                            className={bulkSelectionMode ? "bg-blue-600 text-white" : ""}
                          >
                            {bulkSelectionMode ? (
                              <>
                                <Check className="w-4 h-4 mr-2" />
                                Exit Selection
                              </>
                            ) : (
                              <>
                                <CheckSquare className="w-4 h-4 mr-2" />
                                Select Multiple
                              </>
                            )}
                          </Button>
                        )}

                        {!bulkSelectionMode && isAdmin() && (
                          <>
                            <Button 
                              variant="outline"
                              onClick={() => {
                                setNewShift({
                                  ...newShift,
                                  date: formatDateString(currentDate)
                                });
                                setShowAddShiftDialog(true);
                              }}
                            >
                              <Plus className="w-4 h-4 mr-2" />
                              Add Shift
                            </Button>
                            <Button 
                              variant="outline" 
                              onClick={() => setShowSaveTemplateDialog(true)}
                            >
                              Save Template
                            </Button>
                          </>
                        )}

                        {bulkSelectionMode && isAdmin() && (
                          <>
                            <div className="text-sm text-slate-600 px-3 py-2 bg-blue-50 rounded-md border">
                              {selectedShifts.size} selected
                            </div>
                            <Button 
                              variant="outline" 
                              onClick={selectAllVisibleShifts}
                              disabled={selectedShifts.size === getVisibleShifts().length}
                            >
                              Select All
                            </Button>
                            <Button 
                              variant="outline" 
                              onClick={clearSelection}
                              disabled={selectedShifts.size === 0}
                            >
                              Clear Selection
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Second row of buttons */}
                    <div className="flex items-center justify-between">
                      {!bulkSelectionMode ? (
                        <div className="flex items-center space-x-2">
                          {/* Admin-only template and roster management buttons */}
                          {isAdmin() && (
                            <>
                              <Button 
                                variant="outline" 
                                onClick={() => setShowGenerateFromTemplateDialog(true)}
                              >
                                Load Template
                              </Button>
                              <Button 
                                variant="outline" 
                                onClick={() => setShowManageTemplatesDialog(true)}
                              >
                                Manage Templates
                              </Button>
                              <Button variant="outline" onClick={clearMonthlyRoster}>
                                Clear Roster
                              </Button>
                              <Button onClick={generateMonthlyRoster} className="bg-blue-600 hover:bg-blue-700 text-white">
                                Generate Roster
                              </Button>
                            </>
                          )}
                          {/* YTD Report - Admin sees full report, Staff sees personal YTD */}
                          <Button 
                            variant="outline" 
                            onClick={() => setShowYTDReportDialog(true)}
                            className="text-purple-600 hover:text-purple-700 border-purple-200 hover:border-purple-300"
                          >
                            📊 YTD Report
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          {/* Admin-only bulk actions */}
                          {isAdmin() && (
                            <>
                              <Button 
                                variant="destructive" 
                                onClick={bulkDeleteShifts}
                                disabled={selectedShifts.size === 0}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete Selected ({selectedShifts.size})
                              </Button>
                              <Button 
                                variant="outline" 
                                onClick={() => setShowBulkActionsDialog(true)}
                                disabled={selectedShifts.size === 0}
                              >
                                <Edit className="w-4 h-4 mr-2" />
                                Edit Selected
                              </Button>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Calendar Display - Different Views */}
            {viewMode === 'calendar' && renderCalendarView()}
            {viewMode === 'monthly' && renderMonthlyCalendar()}
            {viewMode === 'weekly' && renderWeeklyView()}
            {viewMode === 'daily' && renderDailyView()}
          </TabsContent>

          <TabsContent value="shifts" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <Clock className="w-5 h-5" />
                      <span>Default Shift Times</span>
                    </CardTitle>
                    <p className="text-slate-600">
                      {currentUser?.role === 'admin' 
                        ? 'Adjust the default start and end times for each shift. These times will be used when generating new rosters.'
                        : 'View the default start and end times for each shift type, including hours worked and pay rates.'
                      }
                    </p>
                  </div>
                  {/* Admin-only editing controls */}
                  {currentUser?.role === 'admin' && (
                    <div className="flex items-center space-x-2">
                      {shiftTemplates.length > 0 && (
                        <Button 
                          variant={bulkEditMode ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => {
                            setBulkEditMode(!bulkEditMode);
                            setSelectedTemplates(new Set());
                          }}
                        >
                          {bulkEditMode ? 'Exit Bulk Edit' : 'Bulk Edit'}
                        </Button>
                      )}
                      {shiftTemplates.length === 0 && (
                        <Button onClick={createDefaultShiftTemplates}>
                          <Plus className="w-4 h-4 mr-2" />
                          Create Default Templates
                        </Button>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Bulk Action Toolbar - Admin only */}
                {currentUser?.role === 'admin' && bulkEditMode && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-blue-700">
                          {selectedTemplates.size} template(s) selected
                        </span>
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline" onClick={selectAllTemplates}>
                            Select All
                          </Button>
                          <Button size="sm" variant="outline" onClick={clearTemplateSelection}>
                            Clear Selection
                          </Button>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setShowBulkEditDialog(true)}
                          disabled={selectedTemplates.size === 0}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Edit Selected
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={deleteSelectedTemplates}
                          disabled={selectedTemplates.size === 0}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete Selected
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {shiftTemplates.length === 0 ? (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-600 mb-2">No Shift Templates Found</h3>
                    <p className="text-slate-500 mb-4">
                      {currentUser?.role === 'admin' 
                        ? 'Create default shift templates to get started with roster generation.'
                        : 'No shift templates have been configured yet. Please contact your administrator.'
                      }
                    </p>
                    {currentUser?.role === 'admin' && (
                      <Button onClick={createDefaultShiftTemplates}>
                        <Plus className="w-4 h-4 mr-2" />
                        Create Default Templates
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, dayIndex) => {
                      const dayTemplates = shiftTemplates.filter(t => t.day_of_week === dayIndex);
                      return (
                        <div key={day} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-lg">{day}</h3>
                            {/* Admin-only Add Shift button */}
                            {currentUser?.role === 'admin' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => createShiftTemplateForDay(dayIndex)}
                              >
                                <Plus className="w-3 h-3 mr-1" />
                                Add Shift
                              </Button>
                            )}
                          </div>
                          {dayTemplates.length === 0 ? (
                            <div className="text-center py-4 text-slate-500">
                              No shifts configured for {day}
                            </div>
                          ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                              {dayTemplates.map((template, shiftIndex) => (
                                <Card key={template.id} className={`p-4 relative ${currentUser?.role === 'admin' && bulkEditMode && selectedTemplates.has(template.id) ? 'ring-2 ring-blue-500 bg-blue-50' : ''}`}>
                                  {/* Bulk Edit Checkbox - Admin only */}
                                  {currentUser?.role === 'admin' && bulkEditMode && (
                                    <div className="absolute top-2 left-2 z-10">
                                      <input
                                        type="checkbox"
                                        checked={selectedTemplates.has(template.id)}
                                        onChange={() => toggleTemplateSelection(template.id)}
                                        className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                      />
                                    </div>
                                  )}
                                  
                                  <div className={`space-y-3 ${currentUser?.role === 'admin' && bulkEditMode ? 'ml-6' : ''}`}>
                                    <div className="flex items-center justify-between">
                                      <h4 className="font-medium">
                                        {template.name || `Shift ${shiftIndex + 1}`}
                                        {template.is_sleepover && <Badge variant="secondary" className="ml-2">Sleepover</Badge>}
                                      </h4>
                                      
                                      {/* Edit buttons - Admin only */}
                                      {currentUser?.role === 'admin' && !bulkEditMode && (
                                        <div className="flex space-x-1">
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => {
                                              setSelectedTemplate(template);
                                              setShowTemplateDialog(true);
                                            }}
                                          >
                                            <Edit className="w-3 h-3" />
                                          </Button>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => cloneTemplate(template)}
                                            title="Clone template"
                                          >
                                            <Copy className="w-3 h-3" />
                                          </Button>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => {
                                              if (window.confirm('Are you sure you want to delete this shift template?')) {
                                                deleteTemplate(template.id);
                                              }
                                            }}
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                          >
                                            <Trash2 className="w-3 h-3" />
                                          </Button>
                                        </div>
                                      )}
                                    </div>
                                    
                                    {/* Shift time display */}
                                    <div className="text-sm text-slate-600">
                                      <div className="font-medium">
                                        {formatTime(template.start_time, settings.time_format === '24hr')} - {formatTime(template.end_time, settings.time_format === '24hr')}
                                      </div>
                                    </div>
                                    
                                    {/* Hours Information */}
                                    <div className="text-sm space-y-1">
                                      {(() => {
                                        // Calculate hours for this shift template
                                        const startMinutes = parseInt(template.start_time.split(':')[0]) * 60 + parseInt(template.start_time.split(':')[1]);
                                        const endMinutes = parseInt(template.end_time.split(':')[0]) * 60 + parseInt(template.end_time.split(':')[1]);
                                        let totalMinutes = endMinutes - startMinutes;
                                        if (totalMinutes < 0) totalMinutes += 24 * 60; // Handle overnight shifts
                                        const totalHours = totalMinutes / 60;
                                        
                                        return (
                                          <div className="flex justify-between text-blue-600">
                                            <span>Hours:</span>
                                            <span className="font-medium">{totalHours.toFixed(1)}h</span>
                                          </div>
                                        );
                                      })()}
                                    </div>

                                    {/* Pay Information - Enhanced for all users */}
                                    <div className="text-sm space-y-2 p-3 bg-slate-50 rounded-lg">
                                      {(() => {
                                        // Calculate shift details for pay display
                                        const startMinutes = parseInt(template.start_time.split(':')[0]) * 60 + parseInt(template.start_time.split(':')[1]);
                                        const endMinutes = parseInt(template.end_time.split(':')[0]) * 60 + parseInt(template.end_time.split(':')[1]);
                                        let totalMinutes = endMinutes - startMinutes;
                                        if (totalMinutes < 0) totalMinutes += 24 * 60; // Handle overnight shifts
                                        const totalHours = totalMinutes / 60;
                                        
                                        // Determine shift type (assuming weekday for template display)
                                        let shiftType = 'weekday_day';
                                        let shiftTypeBadge = 'Day';
                                        let badgeColor = 'bg-blue-100 text-blue-800';
                                        
                                        if (template.manual_shift_type) {
                                          shiftType = template.manual_shift_type;
                                          const typeMapping = {
                                            'weekday_day': { badge: 'Day', color: 'bg-blue-100 text-blue-800' },
                                            'weekday_evening': { badge: 'Evening', color: 'bg-purple-100 text-purple-800' },
                                            'weekday_night': { badge: 'Night', color: 'bg-slate-100 text-slate-800' },
                                            'saturday': { badge: 'Saturday', color: 'bg-orange-100 text-orange-800' },
                                            'sunday': { badge: 'Sunday', color: 'bg-red-100 text-red-800' },
                                            'public_holiday': { badge: 'Holiday', color: 'bg-green-100 text-green-800' }
                                          };
                                          if (typeMapping[shiftType]) {
                                            shiftTypeBadge = typeMapping[shiftType].badge;
                                            badgeColor = typeMapping[shiftType].color;
                                          }
                                        } else {
                                          // Auto-determine based on day of week first, then time
                                          if (template.day_of_week === 5) { // Saturday
                                            shiftType = 'saturday';
                                            shiftTypeBadge = 'Saturday';
                                            badgeColor = 'bg-orange-100 text-orange-800';
                                          } else if (template.day_of_week === 6) { // Sunday
                                            shiftType = 'sunday';
                                            shiftTypeBadge = 'Sunday';
                                            badgeColor = 'bg-red-100 text-red-800';
                                          } else if (endMinutes > 20 * 60) { // After 8 PM (weekdays only)
                                            shiftType = 'weekday_evening';
                                            shiftTypeBadge = 'Evening';
                                            badgeColor = 'bg-purple-100 text-purple-800';
                                          } else if (startMinutes < 6 * 60 || endMinutes <= 6 * 60) { // Before 6 AM or ends at/before 6 AM (weekdays only)
                                            shiftType = 'weekday_night'; 
                                            shiftTypeBadge = 'Night';
                                            badgeColor = 'bg-slate-100 text-slate-800';
                                          }
                                        }
                                        
                                        // Get hourly rate
                                        const hourlyRate = template.manual_hourly_rate || settings.rates[shiftType] || 42.00;
                                        const totalPay = template.is_sleepover ? 
                                          (settings.rates.sleepover_default || 175.00) : 
                                          (totalHours * hourlyRate);
                                        
                                        return (
                                          <div className="space-y-2">
                                            {/* Shift Type Badge */}
                                            <div className="flex justify-between items-center">
                                              <span className="text-slate-600">Shift Type:</span>
                                              <Badge variant="secondary" className={`text-xs ${badgeColor}`}>
                                                {shiftTypeBadge}
                                              </Badge>
                                            </div>
                                            
                                            {/* Hourly Rate */}
                                            <div className="flex justify-between">
                                              <span className="text-slate-600">Rate:</span>
                                              <span className="font-medium text-emerald-600">
                                                {template.is_sleepover ? 'Sleepover' : `$${hourlyRate.toFixed(2)}/hr`}
                                              </span>
                                            </div>
                                            
                                            {/* Total Pay */}
                                            <div className="flex justify-between border-t border-slate-200 pt-2">
                                              <span className="text-slate-700 font-medium">Total Pay:</span>
                                              <span className="font-bold text-emerald-600">
                                                {formatCurrency(totalPay)}
                                              </span>
                                            </div>
                                          </div>
                                        );
                                      })()}
                                    </div>
                                    
                                    {/* Badges for overrides */}
                                    <div className="flex flex-wrap gap-1">
                                      {template.manual_shift_type && (
                                        <Badge variant="outline" className="text-xs">
                                          Override: {template.manual_shift_type}
                                        </Badge>
                                      )}
                                      {template.manual_hourly_rate && (
                                        <Badge variant="outline" className="text-xs">
                                          Rate: ${template.manual_hourly_rate}/hr
                                        </Badge>
                                      )}
                                      {template.allow_overlap && (
                                        <Badge variant="outline" className="text-xs bg-yellow-100 text-yellow-800 border-yellow-200">
                                          2:1 Overlap
                                        </Badge>
                                      )}
                                    </div>
                                  </div>
                                </Card>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="clients" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Client Profile Management</span>
                  </CardTitle>
                  {/* Admin controls */}
                  {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                    <div className="flex space-x-2">
                      <Button onClick={() => {
                        setEditingClient(null);
                        setShowClientDialog(true);
                      }}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Client Profile
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => {
                          resetOCRStates();
                          setShowOCRDialog(true);
                        }}
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        Scan NDIS Plan
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {clients.length === 0 ? (
                  <div className="text-center py-8">
                    <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600">No client profiles found</p>
                    {isAdmin() && (
                      <p className="text-sm text-gray-500 mt-2">Click "Add Client Profile" to create the first client profile</p>
                    )}
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {clients.map(client => (
                      <div key={client.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-4">
                              <div>
                                <h3 className="font-semibold text-lg">{client.full_name}</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2 text-sm text-gray-600">
                                  <div>
                                    <strong>DOB:</strong> {client.date_of_birth}
                                    {client.age && <span> (Age: {client.age})</span>}
                                  </div>
                                  <div>
                                    <strong>Sex:</strong> {client.sex}
                                  </div>
                                  <div>
                                    <strong>Mobile:</strong> {client.mobile}
                                  </div>
                                </div>
                                <div className="mt-2 text-sm text-gray-600">
                                  <div><strong>Condition:</strong> {client.disability_condition}</div>
                                  <div><strong>Address:</strong> {client.address}</div>
                                </div>
                                
                                {/* NDIS Plan Summary - Admin/Supervisor Only */}
                                {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && client.current_ndis_plan && (
                                  <div className="mt-3 p-2 bg-blue-50 rounded border">
                                    <div className="text-sm">
                                      <strong>NDIS Plan:</strong> {client.current_ndis_plan.plan_type} (#{client.current_ndis_plan.ndis_number})
                                    </div>
                                    <div className="text-xs text-blue-600">
                                      Plan Period: {client.current_ndis_plan.plan_start_date} to {client.current_ndis_plan.plan_end_date}
                                    </div>
                                  </div>
                                )}

                                {/* Emergency Contacts Summary */}
                                {client.emergency_contacts && client.emergency_contacts.length > 0 && (
                                  <div className="mt-2 text-xs text-gray-500">
                                    <strong>Emergency Contacts:</strong> {client.emergency_contacts.length} contact{client.emergency_contacts.length !== 1 ? 's' : ''} on file
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedClient(client);
                                setShowClientProfileDialog(true);
                              }}
                            >
                              View Profile
                            </Button>
                            
                            {isAdmin() && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setEditingClient(client);
                                    setShowClientDialog(true);
                                  }}
                                >
                                  Edit
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => deleteClientProfile(client.id)}
                                >
                                  Delete
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="staff" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Staff Management</span>
                  </CardTitle>
                  {/* Admin controls */}
                  {isAdmin() && (
                    <div className="flex items-center space-x-2">
                      <Button 
                        onClick={syncStaffUsers}
                        variant="secondary"
                        className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                        title="Create missing user accounts for staff login"
                      >
                        🔧 Sync Staff Users
                      </Button>
                      <Button onClick={() => setShowStaffDialog(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Staff
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {staff
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map(member => (
                    <Card 
                      key={member.id} 
                      className="p-4 cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => {
                        if (currentUser?.role === 'admin') {
                          // Initialize comprehensive staff profile with all fields
                          const comprehensiveProfile = {
                            ...member,
                            // Basic Information
                            email: member.email || '',
                            phone: member.phone || '',
                            date_of_birth: member.date_of_birth || '',
                            
                            // Address Information
                            postal_address: member.postal_address || '',
                            
                            // Emergency Contact
                            emergency_contact_name: member.emergency_contact_name || '',
                            emergency_contact_phone: member.emergency_contact_phone || '',
                            emergency_contact_address: member.emergency_contact_address || '',
                            emergency_contact_relationship: member.emergency_contact_relationship || '',
                            
                            // Professional Information  
                            ndis_registration: member.ndis_registration || '',
                            blue_card_number: member.blue_card_number || '',
                            yellow_card_number: member.yellow_card_number || '',
                            first_aid_registration: member.first_aid_registration || '',
                            first_aid_expiry: member.first_aid_expiry || '',
                            
                            // Experience & Skills
                            disability_support_experience: member.disability_support_experience || [],
                            nursing_experience: member.nursing_experience || [],
                            manual_handling_certified: member.manual_handling_certified || false,
                            strengths: member.strengths || '',
                            weaknesses: member.weaknesses || '',
                            
                            // Transport & Licensing
                            has_license: member.has_license || false,
                            license_class: member.license_class || '',
                            can_drive_van: member.can_drive_van || false,
                            can_transport_wheelchair: member.can_transport_wheelchair || false,
                            
                            // Profile Photo
                            profile_photo_url: member.profile_photo_url || ''
                          };
                          
                          setSelectedStaffForProfile(comprehensiveProfile);
                          setShowStaffProfileDialog(true);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-blue-600 hover:text-blue-800">{member.name}</h3>
                          <Badge variant={member.active ? "default" : "secondary"}>
                            {member.active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                        {currentUser?.role === 'admin' && (
                          <div className="flex items-center space-x-2">
                            <div className="text-slate-400">
                              <Settings className="w-4 h-4" />
                            </div>
                            {member.active && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation(); // Prevent opening the profile dialog
                                  handleDeleteStaff(member);
                                }}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2"
                                title="Delete Staff Member"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pay" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Clock className="w-5 h-5" />
                    <span>
                      {currentUser?.role === 'admin' ? 'Total Hours' : 'My Hours'}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-800">
                    {(() => {
                      if (currentUser?.role === 'admin') {
                        return totalHours.toFixed(1);
                      } else if (currentUser?.role === 'staff') {
                        // Calculate only current staff member's hours
                        const myHours = Object.entries(staffTotals)
                          .filter(([name, totals]) => {
                            const staffMember = staff.find(s => s.name === name);
                            return staffMember && currentUser.staff_id === staffMember.id;
                          })
                          .reduce((sum, [name, totals]) => sum + totals.hours, 0);
                        return myHours.toFixed(1);
                      }
                      return '0.0';
                    })()}
                  </div>
                  <p className="text-slate-600">This week</p>
                </CardContent>
              </Card>

              {/* Total Pay Card - Only visible to admin */}
              {currentUser?.role === 'admin' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <DollarSign className="w-5 h-5" />
                      <span>Total Pay</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-emerald-600">{formatCurrency(totalPay)}</div>
                    <p className="text-slate-600">This week</p>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    {currentUser?.role === 'admin' ? (
                      <>
                        <Users className="w-5 h-5" />
                        <span>Staff Count</span>
                      </>
                    ) : (
                      <>
                        <DollarSign className="w-5 h-5" />
                        <span>My Pay</span>
                      </>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {currentUser?.role === 'admin' ? (
                    <>
                      <div className="text-3xl font-bold text-slate-800">{staff.length}</div>
                      <p className="text-slate-600">Active staff</p>
                    </>
                  ) : (
                    <>
                      <div className="text-3xl font-bold text-emerald-600">
                        {(() => {
                          const myPay = Object.entries(staffTotals)
                            .filter(([name, totals]) => {
                              const staffMember = staff.find(s => s.name === name);
                              return staffMember && currentUser.staff_id === staffMember.id;
                            })
                            .reduce((sum, [name, totals]) => sum + totals.pay, 0);
                          return formatCurrency(myPay);
                        })()}
                      </div>
                      <p className="text-slate-600">This week</p>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>
                  {currentUser?.role === 'admin' ? 'Weekly Staff Summary' : 'My Weekly Summary'}
                </CardTitle>
                {currentUser?.role === 'staff' && (
                  <p className="text-slate-600 text-sm">Your personal hours and pay information</p>
                )}
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>
                        {currentUser?.role === 'admin' ? 'Staff Member' : 'Name'}
                      </TableHead>
                      <TableHead>Hours Worked</TableHead>
                      {currentUser?.role === 'admin' && <TableHead>Gross Pay</TableHead>}
                      {currentUser?.role === 'staff' && <TableHead>My Pay</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(staffTotals)
                      .filter(([name, totals]) => {
                        // Admin can see all staff, staff can only see their own
                        if (currentUser?.role === 'admin') return true;
                        if (currentUser?.role === 'staff') {
                          // Find the staff member by matching name with current user
                          const staffMember = staff.find(s => s.name === name);
                          return staffMember && currentUser.staff_id === staffMember.id;
                        }
                        return false;
                      })
                      .map(([name, totals]) => (
                        <TableRow key={name}>
                          <TableCell className="font-medium">{name}</TableCell>
                          <TableCell>{totals.hours.toFixed(1)}</TableCell>
                          <TableCell className="font-medium text-emerald-600">
                            {currentUser?.role === 'admin' 
                              ? formatCurrency(totals.pay)
                              : formatCurrency(totals.pay) // Staff can see their own pay
                            }
                          </TableCell>
                        </TableRow>
                      ))}
                    {/* No data message for staff if they have no shifts */}
                    {currentUser?.role === 'staff' && 
                     Object.entries(staffTotals).filter(([name, totals]) => {
                       const staffMember = staff.find(s => s.name === name);
                       return staffMember && currentUser.staff_id === staffMember.id;
                     }).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-6 text-slate-500">
                          No shifts assigned for this week
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="availability" className="space-y-6">
            <div className="space-y-6">
              {/* Notifications Panel */}
              {notifications.filter(n => !n.is_read).length > 0 && (
                <Card className="border-blue-200 bg-blue-50">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Bell className="w-5 h-5 text-blue-600" />
                        <span className="text-blue-800">Notifications ({notifications.filter(n => !n.is_read).length})</span>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setShowNotifications(!showNotifications)}
                      >
                        {showNotifications ? 'Hide' : 'Show'}
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  {showNotifications && (
                    <CardContent>
                      <div className="space-y-3">
                        {notifications.filter(n => !n.is_read).map((notification) => (
                          <div key={notification.id} className="bg-white p-3 rounded-lg border">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-slate-800">{notification.title}</p>
                                <p className="text-sm text-slate-600 mt-1">{notification.message}</p>
                                <p className="text-xs text-slate-500 mt-2">
                                  {new Date(notification.created_at).toLocaleString()}
                                </p>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => markNotificationRead(notification.id)}
                              >
                                Mark Read
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  )}
                </Card>
              )}

              {/* Enhanced Unassigned Shifts Section with Tabbed Views */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Clock className="w-5 h-5" />
                    <span>Available Unassigned Shifts</span>
                  </CardTitle>
                  <p className="text-sm text-slate-600">
                    {isStaff() ? 'Request to fill any unassigned shifts below' : 'Shifts waiting for staff assignment'}
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* View Mode Selector for Unassigned Shifts */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <Label className="font-medium">View:</Label>
                      <div className="flex space-x-1">
                        <Button
                          variant={unassignedShiftsViewMode === 'daily' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setUnassignedShiftsViewMode('daily')}
                        >
                          Daily
                        </Button>
                        <Button
                          variant={unassignedShiftsViewMode === 'weekly' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setUnassignedShiftsViewMode('weekly')}
                        >
                          Weekly
                        </Button>
                        <Button
                          variant={unassignedShiftsViewMode === 'monthly' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setUnassignedShiftsViewMode('monthly')}
                        >
                          Monthly
                        </Button>
                        <Button
                          variant={unassignedShiftsViewMode === 'calendar' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setUnassignedShiftsViewMode('calendar')}
                        >
                          Calendar
                        </Button>
                        <Button
                          variant={unassignedShiftsViewMode === 'search' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setUnassignedShiftsViewMode('search')}
                        >
                          Search Date
                        </Button>
                      </div>
                    </div>
                    
                    {/* Date Navigation for Daily/Weekly/Monthly */}
                    {['daily', 'weekly', 'monthly'].includes(unassignedShiftsViewMode) && (
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const newDate = new Date(currentDate);
                            if (unassignedShiftsViewMode === 'daily') {
                              newDate.setDate(newDate.getDate() - 1);
                            } else if (unassignedShiftsViewMode === 'weekly') {
                              newDate.setDate(newDate.getDate() - 7);
                            } else if (unassignedShiftsViewMode === 'monthly') {
                              newDate.setMonth(newDate.getMonth() - 1);
                            }
                            setCurrentDate(newDate);
                          }}
                        >
                          ←
                        </Button>
                        <span className="text-sm font-medium text-slate-700 min-w-[120px] text-center">
                          {unassignedShiftsViewMode === 'daily' && currentDate.toLocaleDateString('en-AU')}
                          {unassignedShiftsViewMode === 'weekly' && `Week of ${currentDate.toLocaleDateString('en-AU')}`}
                          {unassignedShiftsViewMode === 'monthly' && currentDate.toLocaleDateString('en-AU', { month: 'long', year: 'numeric' })}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const newDate = new Date(currentDate);
                            if (unassignedShiftsViewMode === 'daily') {
                              newDate.setDate(newDate.getDate() + 1);
                            } else if (unassignedShiftsViewMode === 'weekly') {
                              newDate.setDate(newDate.getDate() + 7);
                            } else if (unassignedShiftsViewMode === 'monthly') {
                              newDate.setMonth(newDate.getMonth() + 1);
                            }
                            setCurrentDate(newDate);
                          }}
                        >
                          →
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Search Date Input */}
                  {unassignedShiftsViewMode === 'search' && (
                    <div className="flex items-center space-x-4">
                      <Label htmlFor="search-date">Select Date:</Label>
                      <Input
                        id="search-date"
                        type="date"
                        value={unassignedShiftsSearchDate}
                        onChange={(e) => setUnassignedShiftsSearchDate(e.target.value)}
                        className="w-48"
                      />
                    </div>
                  )}

                  {/* Filtered Unassigned Shifts Display */}
                  {(() => {
                    const filteredShifts = filterUnassignedShiftsByViewMode(
                      unassignedShifts, 
                      unassignedShiftsViewMode, 
                      currentDate, 
                      unassignedShiftsSearchDate
                    );
                    
                    if (filteredShifts.length === 0) {
                      return (
                        <div className="text-center py-8 text-slate-500">
                          <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                          <p>No unassigned shifts available for {unassignedShiftsViewMode} view</p>
                          {unassignedShifts.length > 0 && (
                            <p className="text-sm mt-1">
                              Try switching to a different view or date range. Total unassigned shifts: {unassignedShifts.length}
                            </p>
                          )}
                        </div>
                      );
                    }

                    if (unassignedShiftsViewMode === 'calendar' || ['weekly', 'monthly'].includes(unassignedShiftsViewMode)) {
                      // Group by date for multi-day views
                      const groupedShifts = groupUnassignedShiftsByDate(filteredShifts);
                      return (
                        <div className="space-y-4">
                          {Object.entries(groupedShifts).map(([date, shifts]) => (
                            <div key={date} className="border rounded-lg p-4">
                              <h4 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                                <CalendarIcon className="w-4 h-4" />
                                <span>{new Date(date).toLocaleDateString('en-AU', { 
                                  weekday: 'long', 
                                  year: 'numeric', 
                                  month: 'long', 
                                  day: 'numeric' 
                                })}</span>
                                <Badge variant="secondary" className="text-xs">
                                  {shifts.length} shift{shifts.length !== 1 ? 's' : ''}
                                </Badge>
                              </h4>
                              <div className="space-y-2">
                                {shifts.map((shift) => (
                                  <div key={shift.id} className="border rounded-lg p-3 hover:bg-slate-50 transition-colors">
                                    <div className="flex items-center justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center space-x-4">
                                          <div className="text-slate-600">
                                            {formatTime(shift.start_time, settings.time_format === '24hr')} - {formatTime(shift.end_time, settings.time_format === '24hr')}
                                          </div>
                                          <div className="flex items-center space-x-2">
                                            {getShiftTypeBadge(shift)}
                                            <Badge variant="outline" className="text-emerald-600">
                                              {getPayDisplayText(shift)}
                                            </Badge>
                                          </div>
                                        </div>
                                        <div className="text-sm text-slate-500 mt-1">
                                          {shift.hours_worked?.toFixed(1)} hours • {shift.is_sleepover ? 'Sleepover shift' : 'Regular shift'}
                                        </div>
                                      </div>
                                      {isStaff() && (
                                        <Button 
                                          onClick={() => {
                                            setSelectedUnassignedShift(shift);
                                            setShowShiftRequestDialog(true);
                                          }}
                                          size="sm"
                                          className="ml-4"
                                        >
                                          Request Shift
                                        </Button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    } else {
                      // Simple list for daily view
                      return (
                        <div className="space-y-3">
                          {filteredShifts.map((shift) => (
                            <div key={shift.id} className="border rounded-lg p-4 hover:bg-slate-50 transition-colors">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-4">
                                    <div className="text-lg font-medium text-slate-800">
                                      {formatDateString(shift.date)}
                                    </div>
                                    <div className="text-slate-600">
                                      {formatTime(shift.start_time, settings.time_format === '24hr')} - {formatTime(shift.end_time, settings.time_format === '24hr')}
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      {getShiftTypeBadge(shift)}
                                      <Badge variant="outline" className="text-emerald-600">
                                        {getPayDisplayText(shift)}
                                      </Badge>
                                    </div>
                                  </div>
                                  <div className="text-sm text-slate-500 mt-1">
                                    {shift.hours_worked?.toFixed(1)} hours • {shift.is_sleepover ? 'Sleepover shift' : 'Regular shift'}
                                  </div>
                                </div>
                                {isStaff() && (
                                  <Button 
                                    onClick={() => {
                                      setSelectedUnassignedShift(shift);
                                      setShowShiftRequestDialog(true);
                                    }}
                                    className="ml-4"
                                  >
                                    Request Shift
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    }
                  })()}
                </CardContent>
              </Card>

              {/* Enhanced Shift Requests Section with Admin CRUD */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-5 h-5" />
                      <span>{isStaff() ? 'My Shift Requests' : 'All Shift Requests'}</span>
                    </div>
                    {isAdmin() && (
                      <div className="flex items-center space-x-2">
                        <Button 
                          onClick={() => setShowAddShiftRequestDialog(true)}
                          size="sm"
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Add Request
                        </Button>
                        {shiftRequests.length > 0 && (
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={clearAllShiftRequests}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Clear All
                          </Button>
                        )}
                      </div>
                    )}
                  </CardTitle>
                  {isAdmin() && (
                    <p className="text-sm text-slate-600 mt-2">
                      Manage all staff shift requests - create, edit, approve, reject, or delete requests
                    </p>
                  )}
                </CardHeader>
                <CardContent>
                  {shiftRequests.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No shift requests</p>
                      {isAdmin() && (
                        <Button 
                          className="mt-3"
                          onClick={() => setShowAddShiftRequestDialog(true)}
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Create First Request
                        </Button>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {shiftRequests.map((request) => {
                        const shift = unassignedShifts.find(s => s.id === request.roster_entry_id) || {};
                        return (
                          <div key={request.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-4">
                                  <div className="font-medium text-slate-800">
                                    {request.staff_name}
                                  </div>
                                  <div className="text-slate-600">
                                    {shift.date ? formatDateString(shift.date) : 'N/A'} • 
                                    {shift.start_time && shift.end_time ? ` ${formatTime(shift.start_time)} - ${formatTime(shift.end_time)}` : ' Time TBD'}
                                  </div>
                                  <Badge variant={
                                    request.status === 'pending' ? 'secondary' :
                                    request.status === 'approved' ? 'default' : 'destructive'
                                  }>
                                    {request.status}
                                  </Badge>
                                </div>
                                {request.notes && (
                                  <p className="text-sm text-slate-600 mt-1">"{request.notes}"</p>
                                )}
                                {request.admin_notes && (
                                  <p className="text-sm text-blue-600 mt-1">Admin: "{request.admin_notes}"</p>
                                )}
                                <div className="text-xs text-slate-500 mt-2">
                                  Requested: {new Date(request.request_date).toLocaleString()}
                                </div>
                              </div>
                              
                              {/* Admin Action Buttons */}
                              <div className="flex flex-col space-y-2 ml-4">
                                {isAdmin() && request.status === 'pending' && (
                                  <div className="flex space-x-2">
                                    <Button 
                                      variant="outline"
                                      size="sm"
                                      onClick={() => {
                                        const notes = prompt('Admin notes (optional):');
                                        if (notes !== null) approveShiftRequest(request.id, notes);
                                      }}
                                    >
                                      Approve
                                    </Button>
                                    <Button 
                                      variant="destructive" 
                                      size="sm"
                                      onClick={() => {
                                        const notes = prompt('Reason for rejection:');
                                        if (notes) rejectShiftRequest(request.id, notes);
                                      }}
                                    >
                                      Reject
                                    </Button>
                                  </div>
                                )}
                                
                                {isAdmin() && (
                                  <div className="flex space-x-2">
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      onClick={() => {
                                        setEditingShiftRequest(request);
                                        setShowEditShiftRequestDialog(true);
                                      }}
                                    >
                                      <Edit className="w-4 h-4 mr-1" />
                                      Edit
                                    </Button>
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      onClick={() => deleteShiftRequest(request.id)}
                                    >
                                      <Trash2 className="w-4 h-4 mr-1" />
                                      Delete
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Enhanced Staff Availability Section with Admin CRUD */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <CalendarViewIcon className="w-5 h-5" />
                      <span>{isStaff() ? 'My Availability' : 'Staff Availability'}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button onClick={() => setShowAvailabilityDialog(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        {isStaff() ? 'Update My Availability' : 'Add Availability'}
                      </Button>
                      {isAdmin() && staffAvailability.length > 0 && (
                        <Button 
                          variant="destructive" 
                          size="sm"
                          onClick={clearAllStaffAvailability}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Clear All
                        </Button>
                      )}
                    </div>
                  </CardTitle>
                  <p className="text-sm text-slate-600">
                    {isStaff() ? 
                      'Manage your availability, time off requests, and preferred shifts' :
                      'View and manage all staff availability and preferences - edit, delete, or clear records'
                    }
                  </p>
                </CardHeader>
                <CardContent>
                  {staffAvailability.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <CalendarViewIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No availability records</p>
                      <Button 
                        className="mt-3"
                        onClick={() => setShowAvailabilityDialog(true)}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        {isStaff() ? 'Add My First Availability' : 'Create First Record'}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {staffAvailability.map((availability) => (
                        <div key={availability.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-4 mb-2">
                                <div className="font-medium text-slate-800">
                                  {availability.staff_name}
                                </div>
                                {getAvailabilityTypeBadge(availability.availability_type)}
                              </div>
                              
                              <div className="text-sm text-slate-600 space-y-1">
                                {availability.is_recurring ? (
                                  <p>🔄 Every {getDayOfWeekName(availability.day_of_week)}</p>
                                ) : (
                                  <p>📅 {availability.date_from === availability.date_to ? 
                                    formatAvailabilityDate(availability.date_from) :
                                    `${formatAvailabilityDate(availability.date_from)} - ${formatAvailabilityDate(availability.date_to)}`
                                  }</p>
                                )}
                                
                                {availability.start_time && availability.end_time && (
                                  <p>🕐 {formatTime(availability.start_time)} - {formatTime(availability.end_time)}</p>
                                )}
                                
                                {availability.notes && (
                                  <p className="text-slate-700">💬 {availability.notes}</p>
                                )}
                              </div>
                              
                              <div className="text-xs text-slate-500 mt-2">
                                Added: {new Date(availability.created_at).toLocaleDateString()}
                              </div>
                            </div>
                            
                            {/* Enhanced Action Buttons */}
                            <div className="flex flex-col space-y-2 ml-4">
                              {/* Admin or Own Record Actions */}
                              {(isAdmin() || (isStaff() && availability.staff_id === currentUser?.staff_id)) && (
                                <div className="flex space-x-2">
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    onClick={() => {
                                      setEditingStaffAvailability(availability);
                                      setShowEditStaffAvailabilityDialog(true);
                                    }}
                                  >
                                    <Edit className="w-4 h-4 mr-1" />
                                    Edit
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    onClick={() => deleteStaffAvailability(availability.id)}
                                  >
                                    <Trash2 className="w-4 h-4 mr-1" />
                                    Delete
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="export" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Download className="w-5 h-5" />
                  <span>Export Options</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-slate-600">Export roster and pay data in various formats:</p>
                
                {/* Month Selection for Export */}
                <div className="flex items-center space-x-4 p-3 bg-blue-50 rounded-lg border">
                  <label className="text-sm font-medium text-blue-800">Select Month:</label>
                  <input
                    type="month"
                    value={formatDateString(currentDate).substring(0, 7)} // YYYY-MM format
                    onChange={(e) => {
                      const [year, month] = e.target.value.split('-');
                      setCurrentDate(new Date(parseInt(year), parseInt(month) - 1, 1));
                    }}
                    className="px-3 py-1 border rounded text-sm"
                  />
                  <span className="text-xs text-blue-600">
                    {currentUser?.role === 'staff' ? 'Your shifts only' : 'All roster data'}
                  </span>
                </div>
                
                <div className="flex space-x-4">
                  <Button variant="outline" onClick={() => exportRosterData('pdf')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </Button>
                  <Button variant="outline" onClick={() => exportRosterData('excel')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export Excel
                  </Button>
                  <Button variant="outline" onClick={() => exportRosterData('csv')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export CSV
                  </Button>
                </div>
                
                <div className="text-xs text-slate-500 mt-2">
                  <p><strong>Export includes:</strong> Date, Staff Name, Hours, Pay Rates, Total Pay, Client Info</p>
                  {currentUser?.role === 'admin' && (
                    <p><strong>Admin only:</strong> NDIS billing charges and line item details</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Shift Assignment Dialog */}
        <Dialog open={showShiftDialog} onOpenChange={setShowShiftDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Edit Shift</DialogTitle>
            </DialogHeader>
            {selectedShift && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="start-time">Start Time</Label>
                    <Input
                      id="start-time"
                      type="time"
                      value={selectedShift.start_time}
                      onChange={(e) => {
                        setSelectedShift({
                          ...selectedShift,
                          start_time: e.target.value
                        });
                      }}
                    />
                  </div>
                  <div>
                    <Label htmlFor="end-time">End Time</Label>
                    <Input
                      id="end-time"
                      type="time"
                      value={selectedShift.end_time}
                      onChange={(e) => {
                        setSelectedShift({
                          ...selectedShift,
                          end_time: e.target.value
                        });
                      }}
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="shift-date">Date</Label>
                  <Input
                    id="shift-date"
                    type="date"
                    value={selectedShift.date}
                    onChange={(e) => {
                      setSelectedShift({
                        ...selectedShift,
                        date: e.target.value
                      });
                    }}
                  />
                </div>
                
                <div>
                  <Label htmlFor="staff-select">Assign Staff</Label>
                  <Select
                    value={selectedShift.staff_id || "unassigned"}
                    onValueChange={(staffId) => {
                      if (staffId === "unassigned") {
                        setSelectedShift({
                          ...selectedShift,
                          staff_id: null,
                          staff_name: null
                        });
                      } else {
                        const staff_member = staff.find(s => s.id === staffId);
                        const updatedShift = {
                          ...selectedShift,
                          staff_id: staffId,
                          staff_name: staff_member ? staff_member.name : null
                        };
                        setSelectedShift(updatedShift);
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select staff member" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">Unassigned</SelectItem>
                      {staff
                        .filter(member => member.active)
                        .sort((a, b) => a.name.localeCompare(b.name))
                        .map(member => (
                        <SelectItem key={member.id} value={member.id}>
                          {member.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {/* 2:1 Shift and Overlap Control */}
                <div className="space-y-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium">2:1 Shift (Two Staff Members)</Label>
                      <p className="text-xs text-slate-600">Allow multiple staff on the same shift time</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="is-2-to-1"
                        checked={selectedShift.is_2_to_1 || false}
                        onChange={(e) => {
                          setSelectedShift({
                            ...selectedShift,
                            is_2_to_1: e.target.checked,
                            allow_overlap: e.target.checked // Auto-enable overlap for 2:1 shifts
                          });
                        }}
                        className="rounded"
                      />
                      <Label htmlFor="is-2-to-1" className="text-sm">Enable 2:1</Label>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium">Allow Overlap</Label>
                      <p className="text-xs text-slate-600">Override overlap detection for this shift</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="allow-overlap"
                        checked={selectedShift.allow_overlap || false}
                        onChange={(e) => {
                          setSelectedShift({
                            ...selectedShift,
                            allow_overlap: e.target.checked
                          });
                        }}
                        className="rounded"
                      />
                      <Label htmlFor="allow-overlap" className="text-sm">Allow</Label>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <h4 className="font-medium text-slate-700">Pay Calculation & Overrides</h4>
                  
                  <div className="flex items-center space-x-4 p-3 bg-blue-50 rounded-lg">
                    <Switch
                      checked={selectedShift.manual_sleepover !== null ? selectedShift.manual_sleepover : selectedShift.is_sleepover}
                      onCheckedChange={(checked) => {
                        setSelectedShift({
                          ...selectedShift,
                          manual_sleepover: checked,
                          manual_shift_type: checked ? 'sleepover' : null
                        });
                      }}
                    />
                    <div>
                      <Label className="font-medium">Sleepover Shift</Label>
                      <p className="text-xs text-slate-600">$175 flat rate includes 2 hours wake time</p>
                    </div>
                  </div>
                  
                  {(selectedShift.manual_sleepover || selectedShift.is_sleepover) && (
                    <div>
                      <Label htmlFor="wake-hours">Additional Wake Hours (beyond 2 hours)</Label>
                      <div className="flex items-center space-x-2">
                        <Input
                          id="wake-hours"
                          type="number"
                          step="0.5"
                          min="0"
                          max="8"
                          placeholder="0"
                          value={selectedShift.wake_hours || ''}
                          onChange={(e) => {
                            const wakeHours = parseFloat(e.target.value) || 0;
                            setSelectedShift({
                              ...selectedShift,
                              wake_hours: wakeHours
                            });
                          }}
                        />
                        <span className="text-sm text-slate-600">hours</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Extra wake time paid at applicable hourly rate</p>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Shift Type Override</Label>
                      <Select
                        value={selectedShift.manual_shift_type || "auto"}
                        onValueChange={(value) => {
                          const manualType = value === "auto" ? null : value;
                          const isSleepover = value === "sleepover";
                          setSelectedShift({
                            ...selectedShift,
                            manual_shift_type: manualType,
                            manual_sleepover: isSleepover ? true : (manualType ? false : null)
                          });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Auto-detect" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="auto">Auto-detect</SelectItem>
                          <SelectItem value="weekday_day">Weekday Day ($42.00/hr)</SelectItem>
                          <SelectItem value="weekday_evening">Weekday Evening ($44.50/hr)</SelectItem>
                          <SelectItem value="weekday_night">Weekday Night ($48.50/hr)</SelectItem>
                          <SelectItem value="saturday">Saturday ($57.50/hr)</SelectItem>
                          <SelectItem value="sunday">Sunday ($74.00/hr)</SelectItem>
                          <SelectItem value="public_holiday">Public Holiday ($88.50/hr)</SelectItem>
                          <SelectItem value="sleepover">Sleepover ($175 + extra wake hours)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Custom Hourly Rate</Label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="Auto-calculated"
                          value={selectedShift.manual_hourly_rate || ''}
                          onChange={(e) => {
                            const manualRate = parseFloat(e.target.value) || null;
                            setSelectedShift({
                              ...selectedShift,
                              manual_hourly_rate: manualRate
                            });
                          }}
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Hours Worked</Label>
                      <div className="text-lg font-medium">{selectedShift.hours_worked.toFixed(1)}</div>
                    </div>
                    <div>
                      <Label>Current Shift Type</Label>
                      {getShiftTypeBadge(selectedShift)}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="manual-base-pay">Base Pay Override</Label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">$</span>
                        <Input
                          id="manual-base-pay"
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="Auto-calculated"
                          onChange={(e) => {
                            const manualPay = parseFloat(e.target.value) || null;
                            setSelectedShift({
                              ...selectedShift,
                              manual_base_pay: manualPay,
                              total_pay: (manualPay || selectedShift.base_pay) + selectedShift.sleepover_allowance
                            });
                          }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Leave empty for auto-calculation</p>
                    </div>
                    <div>
                      <Label>Sleepover Allowance</Label>
                      <div className="text-lg font-medium">
                        {selectedShift.sleepover_allowance > 0 ? formatCurrency(selectedShift.sleepover_allowance) : '-'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 bg-slate-50 p-3 rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span>Calculated Base Pay:</span>
                    <span className="font-medium">{formatCurrency(selectedShift.base_pay)}</span>
                  </div>
                  {selectedShift.sleepover_allowance > 0 && (
                    <div className="flex justify-between text-sm">
                      <span>Sleepover Allowance:</span>
                      <span className="font-medium">{formatCurrency(selectedShift.sleepover_allowance)}</span>
                    </div>
                  )}
                  <Separator />
                  <div className="flex justify-between font-bold">
                    <span>Total Pay:</span>
                    <span className="text-emerald-600">{getPayDisplayText(selectedShift)}</span>
                  </div>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowShiftDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={() => {
                    // Include all manual overrides and overlap controls in the update
                    const updates = {
                      date: selectedShift.date,
                      staff_id: selectedShift.staff_id,
                      staff_name: selectedShift.staff_name,
                      start_time: selectedShift.start_time,
                      end_time: selectedShift.end_time,
                      manual_shift_type: selectedShift.manual_shift_type || null,
                      manual_hourly_rate: selectedShift.manual_hourly_rate || null,
                      manual_sleepover: selectedShift.manual_sleepover,
                      wake_hours: selectedShift.wake_hours || null,
                      // 2:1 and overlap controls
                      is_2_to_1: selectedShift.is_2_to_1 || false,
                      allow_overlap: selectedShift.allow_overlap || false
                    };
                    
                    console.log('Saving shift with updates:', updates);
                    updateRosterEntry(selectedShift.id, updates);
                    setShowShiftDialog(false);
                  }}>
                    Save Changes
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Add Shift Dialog */}
        <Dialog open={showAddShiftDialog} onOpenChange={setShowAddShiftDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Shift</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="shift-date">Date</Label>
                <Input
                  id="shift-date"
                  type="date"
                  value={newShift.date}
                  onChange={(e) => setNewShift({...newShift, date: e.target.value})}
                />
              </div>
              
              <div>
                <Label htmlFor="shift-staff">Assign Staff (Optional)</Label>
                <Select
                  value={newShift.staff_id || 'unassigned'}
                  onValueChange={(value) => {
                    if (value === 'unassigned') {
                      setNewShift({
                        ...newShift, 
                        staff_id: null,
                        staff_name: null
                      });
                    } else {
                      const selectedStaff = staff.find(member => member.id === value);
                      setNewShift({
                        ...newShift, 
                        staff_id: value,
                        staff_name: selectedStaff?.name || null
                      });
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select staff member (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unassigned">No staff assigned</SelectItem>
                    {getSortedActiveStaff().map(member => (
                      <SelectItem key={member.id} value={member.id}>
                        {member.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="shift-start">Start Time</Label>
                  <Input
                    id="shift-start"
                    type="time"
                    value={newShift.start_time}
                    onChange={(e) => setNewShift({...newShift, start_time: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="shift-end">End Time</Label>
                  <Input
                    id="shift-end"
                    type="time"
                    value={newShift.end_time}
                    onChange={(e) => setNewShift({...newShift, end_time: e.target.value})}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={newShift.is_sleepover}
                  onCheckedChange={(checked) => setNewShift({...newShift, is_sleepover: checked})}
                />
                <Label>Sleepover Shift</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  checked={newShift.allow_overlap}
                  onCheckedChange={(checked) => setNewShift({...newShift, allow_overlap: checked})}
                />
                <Label>Allow Overlap (2:1 Shift - Multiple Staff)</Label>
              </div>
              
              <div className="text-sm text-slate-600 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p><strong>Allow Overlap:</strong> Check this option if you need to add a shift that overlaps with existing shifts (e.g., 2:1 shifts requiring multiple staff members). This will override the normal overlap prevention.</p>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowAddShiftDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={addIndividualShift}>
                  Add Shift
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Break Warning Dialog */}
        <Dialog open={showBreakWarning} onOpenChange={setShowBreakWarning}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2 text-amber-600">
                <Clock className="w-5 h-5" />
                <span>Shift Break Warning</span>
              </DialogTitle>
            </DialogHeader>
            {breakWarningData && (
              <div className="space-y-4">
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                        <Clock className="w-4 h-4 text-amber-600" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold text-amber-800 mb-1">
                        Insufficient Break Time
                      </h3>
                      <p className="text-sm text-amber-700 mb-2">
                        {breakWarningData.violation.message}
                      </p>
                      <div className="text-xs text-amber-600">
                        <strong>Shift Sequence:</strong><br />
                        {breakWarningData.violation.details}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-sm text-slate-600 space-y-2">
                  <p><strong>Policy:</strong> Staff must have at least 10 hours break between shifts.</p>
                  <p><strong>Exceptions:</strong> Sleepover shifts are exempt from this rule.</p>
                </div>

                <div className="bg-slate-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-slate-700 mb-1">Do you want to proceed?</p>
                  <p className="text-xs text-slate-600">
                    Approving this assignment may violate workplace safety regulations.
                  </p>
                </div>

                <div className="flex justify-end space-x-3">
                  <Button 
                    variant="outline" 
                    onClick={denyShiftAssignment}
                    className="border-amber-300 text-amber-700 hover:bg-amber-50"
                  >
                    Deny Assignment
                  </Button>
                  <Button 
                    onClick={approveShiftAssignment}
                    className="bg-amber-600 hover:bg-amber-700 text-white"
                  >
                    Approve Override
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Shift Template Edit Dialog */}
        <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Default Shift Template</DialogTitle>
            </DialogHeader>
            {selectedTemplate && (
              <div className="space-y-6">
                <div>
                  <Label>Day & Shift</Label>
                  <div className="text-sm text-slate-600 mb-4">
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][selectedTemplate.day_of_week]} - 
                    Template Shift
                  </div>
                </div>

                {/* Shift Name */}
                <div>
                  <Label htmlFor="template-name">Shift Name</Label>
                  <Input
                    id="template-name" 
                    value={selectedTemplate.name}
                    onChange={(e) => {
                      setSelectedTemplate({
                        ...selectedTemplate,
                        name: e.target.value
                      });
                    }}
                    placeholder="e.g., Morning Shift, Evening Shift, Night Shift"
                  />
                </div>

                {/* Time Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="template-start-time">Start Time</Label>
                    <Input
                      id="template-start-time"
                      type="time"
                      value={selectedTemplate.start_time}
                      onChange={(e) => {
                        setSelectedTemplate({
                          ...selectedTemplate,
                          start_time: e.target.value
                        });
                      }}
                    />
                  </div>
                  <div>
                    <Label htmlFor="template-end-time">End Time</Label>
                    <Input
                      id="template-end-time"
                      type="time"
                      value={selectedTemplate.end_time}
                      onChange={(e) => {
                        setSelectedTemplate({
                          ...selectedTemplate,
                          end_time: e.target.value
                        });
                      }}
                    />
                  </div>
                </div>

                {/* Sleepover Setting */}
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={selectedTemplate.is_sleepover}
                    onCheckedChange={(checked) => {
                      setSelectedTemplate({
                        ...selectedTemplate,
                        is_sleepover: checked
                      });
                    }}
                  />
                  <Label>Sleepover Shift</Label>
                </div>

                {/* Allow 2:1 Overlap Setting */}
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={selectedTemplate.allow_overlap || false}
                    onCheckedChange={(checked) => {
                      setSelectedTemplate({
                        ...selectedTemplate,
                        allow_overlap: checked
                      });
                    }}
                  />
                  <Label>Allow 2:1 Shift Overlapping</Label>
                </div>
                <div className="text-sm text-slate-500 mt-1">
                  Enable this to allow multiple staff to be assigned to the same shift time (useful for 2:1 support scenarios)
                </div>

                {/* Manual Shift Type Override */}
                <div>
                  <Label htmlFor="template-manual-shift-type">Manual Shift Type Override (Optional)</Label>
                  <Select 
                    value={selectedTemplate.manual_shift_type || 'auto'} 
                    onValueChange={(value) => {
                      setSelectedTemplate({
                        ...selectedTemplate,
                        manual_shift_type: value === 'auto' ? null : value
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Auto-detect shift type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">🤖 Auto-detect shift type</SelectItem>
                      <SelectItem value="weekday_day">☀️ Weekday Day (6am-8pm)</SelectItem>
                      <SelectItem value="weekday_evening">🌆 Weekday Evening (after 8pm)</SelectItem>
                      <SelectItem value="weekday_night">🌙 Weekday Night (overnight)</SelectItem>
                      <SelectItem value="saturday">📅 Saturday Rate</SelectItem>
                      <SelectItem value="sunday">📅 Sunday Rate</SelectItem>
                      <SelectItem value="public_holiday">🎉 Public Holiday Rate</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-sm text-slate-500 mt-1">
                    Override automatic shift type detection for this template
                  </div>
                </div>

                {/* Manual Hourly Rate Override */}
                <div>
                  <Label htmlFor="template-manual-rate">Manual Hourly Rate Override (Optional)</Label>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">$</span>
                    <Input
                      id="template-manual-rate"
                      type="number"
                      step="0.01"
                      min="0"
                      value={selectedTemplate.manual_hourly_rate || ''}
                      onChange={(e) => {
                        setSelectedTemplate({
                          ...selectedTemplate,
                          manual_hourly_rate: e.target.value ? parseFloat(e.target.value) : null
                        });
                      }}
                      placeholder="Leave blank for automatic rate"
                    />
                    <span className="text-sm text-slate-500">per hour</span>
                  </div>
                  <div className="text-sm text-slate-500 mt-1">
                    Override automatic hourly rate calculation for this template
                  </div>
                </div>

                <div className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg">
                  <strong>Note:</strong> Changes to default shift templates will only affect newly generated rosters. 
                  Existing roster entries can be edited individually. Manual overrides will be applied to all shifts created from this template.
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowTemplateDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={() => {
                    updateShiftTemplate(selectedTemplate.id, {
                      name: selectedTemplate.name,
                      start_time: selectedTemplate.start_time,
                      end_time: selectedTemplate.end_time,
                      is_sleepover: selectedTemplate.is_sleepover,
                      manual_shift_type: selectedTemplate.manual_shift_type,
                      manual_hourly_rate: selectedTemplate.manual_hourly_rate,
                      allow_overlap: selectedTemplate.allow_overlap || false
                    });
                    setShowTemplateDialog(false);
                  }}>
                    Save Changes
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Add Staff Dialog */}
        <Dialog open={showStaffDialog} onOpenChange={setShowStaffDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Staff Member</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="staff-name">Name</Label>
                <Input
                  id="staff-name"
                  value={newStaffName}
                  onChange={(e) => setNewStaffName(e.target.value)}
                  placeholder="Enter staff name"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowStaffDialog(false)} disabled={addingStaff}>
                  Cancel
                </Button>
                <Button onClick={addStaff} disabled={addingStaff}>
                  {addingStaff ? 'Adding...' : 'Add Staff'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Settings Dialog */}
        <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Settings</DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-medium">Pay Mode</Label>
                  <p className="text-sm text-slate-600">Switch between Default rates and SCHADS Award compliance</p>
                </div>
                <Switch
                  checked={settings.pay_mode === 'schads'}
                  onCheckedChange={(checked) => {
                    const newSettings = {
                      ...settings,
                      pay_mode: checked ? 'schads' : 'default'
                    };
                    updateSettings(newSettings);
                  }}
                />
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Regional & Time Settings</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Timezone</Label>
                    <Select
                      value={settings.timezone}
                      onValueChange={(value) => {
                        const newSettings = {
                          ...settings,
                          timezone: value
                        };
                        setSettings(newSettings);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Australia/Brisbane">Brisbane, Queensland (AEST UTC+10)</SelectItem>
                        <SelectItem value="Australia/Sydney">Sydney (AEDT UTC+11)</SelectItem>
                        <SelectItem value="Australia/Melbourne">Melbourne (AEDT UTC+11)</SelectItem>
                        <SelectItem value="Australia/Perth">Perth (AWST UTC+8)</SelectItem>
                        <SelectItem value="Australia/Adelaide">Adelaide (ACDT UTC+10:30)</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-slate-500 mt-1">Current: Brisbane, Queensland (AEST UTC+10)</p>
                  </div>
                  
                  <div>
                    <Label>Time Format</Label>
                    <Select
                      value={settings.time_format}
                      onValueChange={(value) => {
                        const newSettings = {
                          ...settings,
                          time_format: value
                        };
                        setSettings(newSettings);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="24hr">24 Hour (14:30)</SelectItem>
                        <SelectItem value="12hr">12 Hour (2:30 PM)</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-slate-500 mt-1">Display format for all shift times</p>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Pay Rates (Per Hour)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Weekday Day Rate (6am-8pm)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.weekday_day}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              weekday_day: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Starts at/after 6:00am, ends at/before 8:00pm</p>
                  </div>
                  <div>
                    <Label>Weekday Evening Rate (after 8pm)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.weekday_evening}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              weekday_evening: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Starts after 8:00pm OR extends past 8:00pm</p>
                  </div>
                  <div>
                    <Label>Weekday Night Rate (overnight)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.weekday_night}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              weekday_night: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Commences at/before midnight and finishes after midnight</p>
                  </div>
                  <div>
                    <Label>Saturday Rate (all hours)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.saturday}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              saturday: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Sunday Rate (all hours)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.sunday}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              sunday: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Public Holiday Rate (all hours)</Label>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">$</span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={settings.rates.public_holiday}
                        disabled={!isAdmin()}
                        readOnly={!isAdmin()}
                        onChange={(e) => {
                          const newSettings = {
                            ...settings,
                            rates: {
                              ...settings.rates,
                              public_holiday: parseFloat(e.target.value) || 0
                            }
                          };
                          setSettings(newSettings);
                        }}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Sleepover Allowances</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Sleepover Allowance (Default)</Label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={settings.rates.sleepover_default}
                          disabled={!isAdmin()}
                          readOnly={!isAdmin()}
                          onChange={(e) => {
                            const newSettings = {
                              ...settings,
                              rates: {
                                ...settings.rates,
                                sleepover_default: parseFloat(e.target.value) || 0
                              }
                            };
                            setSettings(newSettings);
                          }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">$175 per night includes 2 hours wake time</p>
                    </div>
                    <div>
                      <Label>Sleepover Allowance (SCHADS)</Label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={settings.rates.sleepover_schads}
                          disabled={!isAdmin()}
                          readOnly={!isAdmin()}
                          onChange={(e) => {
                            const newSettings = {
                              ...settings,
                              rates: {
                                ...settings.rates,
                                sleepover_schads: parseFloat(e.target.value) || 0
                              }
                            };
                            setSettings(newSettings);
                          }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">SCHADS Award compliant rate</p>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="text-sm font-semibold text-blue-800 mb-2">SCHADS Award Rules:</h4>
                  <ul className="text-xs text-blue-700 space-y-1">
                    <li>• <strong>Day:</strong> Starts at/after 6:00am and ends at/before 8:00pm</li>
                    <li>• <strong>Evening:</strong> Starts after 8:00pm OR any shift that extends past 8:00pm</li>
                    <li>• <strong>Night:</strong> Commences at/before midnight and finishes after midnight</li>
                    <li>• <strong>Sleepover:</strong> $175 includes 2 hours wake time, additional at hourly rate</li>
                  </ul>
                </div>
              </div>

              <Separator />

              {/* Bountiful Care Charge Rates Section - Admin Only */}
              {isAdmin() && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Bountiful Care Charge Rates (Per Hour)</h3>
                  <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
                    <p className="text-sm text-amber-800">
                      <strong>Note:</strong> These rates are charged for client billing and are displayed to Admin users only. Staff see their regular pay rates.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 gap-4">
                    {settings.ndis_charge_rates && Object.entries(settings.ndis_charge_rates).map(([key, rateInfo]) => (
                      <div key={key} className="border rounded-lg p-4 bg-slate-50">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <Label className="text-sm font-medium">Line Item Code</Label>
                            <Input
                              type="text"
                              value={rateInfo.line_item_code || ''}
                              disabled={!isAdmin()}
                              readOnly={!isAdmin()}
                              onChange={(e) => {
                                const newSettings = {
                                  ...settings,
                                  ndis_charge_rates: {
                                    ...settings.ndis_charge_rates,
                                    [key]: {
                                      ...rateInfo,
                                      line_item_code: e.target.value
                                    }
                                  }
                                };
                                setSettings(newSettings);
                              }}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label className="text-sm font-medium">Description</Label>
                            <Input
                              type="text"
                              value={rateInfo.description || ''}
                              disabled={!isAdmin()}
                              readOnly={!isAdmin()}
                              onChange={(e) => {
                                const newSettings = {
                                  ...settings,
                                  ndis_charge_rates: {
                                    ...settings.ndis_charge_rates,
                                    [key]: {
                                      ...rateInfo,
                                      description: e.target.value
                                    }
                                  }
                                };
                                setSettings(newSettings);
                              }}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label className="text-sm font-medium">Rate per Hour</Label>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="text-sm">$</span>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                value={rateInfo.rate || 0}
                                disabled={!isAdmin()}
                                readOnly={!isAdmin()}
                                onChange={(e) => {
                                  const newSettings = {
                                    ...settings,
                                    ndis_charge_rates: {
                                      ...settings.ndis_charge_rates,
                                      [key]: {
                                        ...rateInfo,
                                        rate: parseFloat(e.target.value) || 0
                                      }
                                    }
                                  };
                                  setSettings(newSettings);
                                }}
                              />
                            </div>
                          </div>
                        </div>
                        <div className="mt-2">
                          <p className="text-xs text-slate-600">
                            <strong>Shift Type:</strong> {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Bountiful Care Sleepover Rates */}
                  {settings.ndis_charge_rates && settings.ndis_charge_rates.sleepover_default && (
                    <div className="border rounded-lg p-4 bg-blue-50 border-blue-200">
                      <h4 className="text-sm font-semibold text-blue-800 mb-3">Bountiful Care Sleepover Charges</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Line Item Code</Label>
                          <Input
                            type="text"
                            value={settings.ndis_charge_rates.sleepover_default.line_item_code || ''}
                            disabled={!isAdmin()}
                            readOnly={!isAdmin()}
                            onChange={(e) => {
                              const newSettings = {
                                ...settings,
                                ndis_charge_rates: {
                                  ...settings.ndis_charge_rates,
                                  sleepover_default: {
                                    ...settings.ndis_charge_rates.sleepover_default,
                                    line_item_code: e.target.value
                                  }
                                }
                              };
                              setSettings(newSettings);
                            }}
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Description</Label>
                          <Input
                            type="text"
                            value={settings.ndis_charge_rates.sleepover_default.description || ''}
                            disabled={!isAdmin()}
                            readOnly={!isAdmin()}
                            onChange={(e) => {
                              const newSettings = {
                                ...settings,
                                ndis_charge_rates: {
                                  ...settings.ndis_charge_rates,
                                  sleepover_default: {
                                    ...settings.ndis_charge_rates.sleepover_default,
                                    description: e.target.value
                                  }
                                }
                              };
                              setSettings(newSettings);
                            }}
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Rate per Shift</Label>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-sm">$</span>
                            <Input
                              type="number"
                              step="0.01"
                              min="0"
                              value={settings.ndis_charge_rates.sleepover_default.rate || 0}
                              disabled={!isAdmin()}
                              readOnly={!isAdmin()}
                              onChange={(e) => {
                                const newSettings = {
                                  ...settings,
                                  ndis_charge_rates: {
                                    ...settings.ndis_charge_rates,
                                    sleepover_default: {
                                      ...settings.ndis_charge_rates.sleepover_default,
                                      rate: parseFloat(e.target.value) || 0
                                    }
                                  }
                                };
                                setSettings(newSettings);
                              }}
                            />
                          </div>
                        </div>
                      </div>
                      <p className="text-xs text-blue-700 mt-2">
                        <strong>Note:</strong> Sleepover charges are per-shift based, not hourly
                      </p>
                    </div>
                  )}
                </div>
              )}

              <Separator />

              {/* Maximum NDIS Pricing Guidelines Reference - Admin Only */}
              {isAdmin() && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Maximum NDIS Pricing Guidelines (Reference)</h3>
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <strong>Reference Only:</strong> These are the maximum NDIS rates for comparison. Bountiful Care rates above are used for actual billing calculations.
                    </p>
                  </div>

                  {/* SIL (Supported Independent Living) Rates */}
                  <div className="space-y-3">
                    <h4 className="text-md font-semibold text-slate-700">NDIS Rates for (SIL) - Supported Independent Living</h4>
                    <div className="grid grid-cols-1 gap-3">
                      {[
                        { code: "01_801_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Weekday Daytime", rate: 70.23 },
                        { code: "01_802_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Weekday Evening", rate: 77.38 },
                        { code: "01_803_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Weekday Night", rate: 78.81 },
                        { code: "01_804_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Saturday", rate: 98.83 },
                        { code: "01_805_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Sunday", rate: 127.43 },
                        { code: "01_806_0115_1_1", desc: "Assistance in Supported Independent Living - Standard - Public Holiday", rate: 156.03 },
                        { code: "01_832_0115_1_1", desc: "Assistance in Supported Independent Living - Night-Time Sleepover", rate: 297.60, unit: "per shift" }
                      ].map((item) => (
                        <div key={item.code} className="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-white border rounded-lg text-sm">
                          <div>
                            <span className="font-medium text-slate-600">Code:</span> <span className="font-mono text-sm">{item.code}</span>
                          </div>
                          <div>
                            <span className="font-medium text-slate-600">Description:</span> {item.desc}
                          </div>
                          <div>
                            <span className="font-medium text-slate-600">Price:</span> <span className="font-semibold text-green-600">${item.rate.toFixed(2)}</span> {item.unit || 'per hour'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Core Social Rates */}
                  <div className="space-y-3">
                    <h4 className="text-md font-semibold text-slate-700">NDIS Rates for (Core) Social</h4>
                    <div className="grid grid-cols-1 gap-3">
                      {[
                        { code: "04_102_0125_6_1", desc: "Access Community Social and Rec Activ - Standard - Public Holiday", rate: 156.03 },
                        { code: "04_103_0125_6_1", desc: "Access Community Social and Rec Activ - Standard - Weekday Evening", rate: 77.38 },
                        { code: "04_104_0125_6_1", desc: "Access Community Social and Rec Activ - Standard - Weekday Daytime", rate: 70.23 },
                        { code: "04_105_0125_6_1", desc: "Access Community Social and Rec Activ - Standard - Saturday", rate: 98.83 },
                        { code: "04_106_0125_6_1", desc: "Access Community Social and Rec Activ - Standard - Sunday", rate: 127.43 },
                        { code: "04_590_0125_6_1", desc: "Activity Based Transport", rate: 1.00, unit: "per km" }
                      ].map((item) => (
                        <div key={item.code} className="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-white border rounded-lg text-sm">
                          <div>
                            <span className="font-medium text-slate-600">Code:</span> <span className="font-mono text-sm">{item.code}</span>
                          </div>
                          <div>
                            <span className="font-medium text-slate-600">Description:</span> {item.desc}
                          </div>
                          <div>
                            <span className="font-medium text-slate-600">Price:</span> <span className="font-semibold text-green-600">${item.rate.toFixed(2)}</span> {item.unit || 'per hour'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <Separator />

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowSettingsDialog(false)}>
                  {isAdmin() ? 'Cancel' : 'Close'}
                </Button>
                {/* Save Settings button - Admin only */}
                {isAdmin() && (
                  <Button onClick={() => updateSettings(settings)}>
                    Save Settings
                  </Button>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Save Roster Template Dialog */}
        <Dialog open={showSaveTemplateDialog} onOpenChange={setShowSaveTemplateDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Save Current Roster as Template</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="template-name">Template Name</Label>
                <Input
                  id="template-name"
                  value={newTemplateName}
                  onChange={(e) => setNewTemplateName(e.target.value)}
                  placeholder="Enter template name (e.g., 'Standard Weekly Template')"
                />
              </div>
              <div className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg">
                <p><strong>This will save:</strong></p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>All shift times and patterns from current month</li>
                  <li>Day-of-week based placement (Monday shifts → all Mondays)</li>
                  <li>Sleepover status for each shift</li>
                </ul>
                <p className="mt-2"><strong>Note:</strong> Staff assignments are NOT saved in templates.</p>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowSaveTemplateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={saveCurrentRosterAsTemplate}>
                  Save Template
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Generate from Template Dialog */}
        <Dialog open={showGenerateFromTemplateDialog} onOpenChange={setShowGenerateFromTemplateDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Manage Roster Templates</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="roster-template">Select Template</Label>
                <Select 
                  value={selectedRosterTemplate || ''} 
                  onValueChange={setSelectedRosterTemplate}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a roster template" />
                  </SelectTrigger>
                  <SelectContent>
                    {rosterTemplates.map(template => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name}
                        {template.description && (
                          <span className="text-sm text-slate-500 ml-2">- {template.description}</span>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {rosterTemplates.length === 0 && (
                <div className="text-sm text-slate-600 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p><strong>No templates found.</strong></p>
                  <p>Create a roster first, then use "Save Template" to save it for future use.</p>
                </div>
              )}
              
              <div className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg">
                <p><strong>Template Actions:</strong></p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li><strong>Load:</strong> Generate roster for {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}</li>
                  <li><strong>Edit:</strong> Modify template name and description</li>
                  <li><strong>Delete:</strong> Permanently remove template</li>
                </ul>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowGenerateFromTemplateDialog(false)}>
                  Cancel
                </Button>
                {selectedRosterTemplate && (
                  <>
                    <Button 
                      variant="destructive" 
                      onClick={() => deleteRosterTemplate(selectedRosterTemplate)}
                    >
                      Delete Template
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => editRosterTemplate(selectedRosterTemplate)}
                    >
                      Edit Template
                    </Button>
                  </>
                )}
                <Button 
                  onClick={generateRosterFromTemplate}
                  disabled={!selectedRosterTemplate}
                >
                  Load Template
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Manage Templates Dialog */}
        <Dialog open={showManageTemplatesDialog} onOpenChange={setShowManageTemplatesDialog}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-slate-800">
                📋 Manage Roster Templates
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {rosterTemplates.length === 0 ? (
                <div className="text-center py-8">
                  <CalendarIcon className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">No Templates Found</h3>
                  <p className="text-slate-500 mb-4">Save your current roster as a template to get started.</p>
                  <Button onClick={() => {
                    setShowManageTemplatesDialog(false);
                    setShowSaveTemplateDialog(true);
                  }}>
                    Create First Template
                  </Button>
                </div>
              ) : (
                <>
                  <div className="text-sm text-slate-600 mb-4">
                    You have {rosterTemplates.length} saved roster template{rosterTemplates.length !== 1 ? 's' : ''}. 
                    Templates store shift patterns for easy reuse across different months.
                  </div>
                  
                  <div className="space-y-4">
                    {rosterTemplates.map(template => {
                      const shiftDetails = getTemplateShiftDetails(template);
                      const createdDate = template.created_at ? new Date(template.created_at).toLocaleDateString() : 'Unknown';
                      
                      return (
                        <Card key={template.id} className="border border-slate-200 hover:border-slate-300 transition-colors">
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <CardTitle className="text-lg font-semibold text-slate-800 mb-1">
                                  {template.name}
                                </CardTitle>
                                {template.description && (
                                  <p className="text-sm text-slate-600 mb-2">
                                    {template.description}
                                  </p>
                                )}
                                <div className="flex items-center space-x-4 text-xs text-slate-500">
                                  <span>📊 {shiftDetails.totalShifts} shift{shiftDetails.totalShifts !== 1 ? 's' : ''}</span>
                                  <span>📅 Created: {createdDate}</span>
                                </div>
                              </div>
                              <div className="flex space-x-2 ml-4">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedRosterTemplate(template.id);
                                    setShowManageTemplatesDialog(false);
                                    setShowGenerateFromTemplateDialog(true);
                                  }}
                                  className="text-green-600 hover:text-green-700 border-green-200 hover:border-green-300"
                                >
                                  Load
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => editRosterTemplate(template.id)}
                                  className="text-blue-600 hover:text-blue-700 border-blue-200 hover:border-blue-300"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => deleteRosterTemplate(template.id)}
                                  className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          </CardHeader>
                          
                          {shiftDetails.details.length > 0 && (
                            <CardContent className="pt-0">
                              <div className="bg-slate-50 rounded-lg p-3">
                                <h4 className="text-sm font-medium text-slate-700 mb-2">📋 Shift Schedule:</h4>
                                <div className="space-y-1 text-sm text-slate-600">
                                  {shiftDetails.details.map((detail, index) => (
                                    <div key={index} className="flex items-start">
                                      <span className="w-20 flex-shrink-0 font-medium">
                                        {detail.split(':')[0]}:
                                      </span>
                                      <span className="flex-1">
                                        {detail.split(':').slice(1).join(':').trim()}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              {/* Enhanced Totals Summary Section */}
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Weekly Totals */}
                      {(() => {
                        const weeklyTotals = getWeeklyTotals();
                        const weekStart = new Date(currentDate);
                        weekStart.setDate(currentDate.getDate() - currentDate.getDay() + 1); // Monday
                        const weekEnd = new Date(weekStart);
                        weekEnd.setDate(weekStart.getDate() + 6);
                        
                        return (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm font-medium text-slate-700">
                                📅 This Week ({weekStart.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' })} - {weekEnd.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' })})
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Total Hours:</span>
                                <span className="font-medium text-blue-600">{weeklyTotals.totalHours.toFixed(1)}h</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Total Pay:</span>
                                {currentUser?.role === 'admin' && (
                                  <span className="font-medium text-emerald-600">{formatCurrency(weeklyTotals.totalPay)}</span>
                                )}
                              </div>
                              <div className="pt-2 border-t border-slate-200">
                                <div className="text-xs text-slate-500 mb-1">Staff Breakdown:</div>
                                <div className="space-y-1 max-h-24 overflow-y-auto">
                                  {Object.entries(weeklyTotals.staffTotals).length === 0 ? (
                                    <div className="text-xs text-slate-400 italic">No assigned shifts</div>
                                  ) : (
                                    Object.entries(weeklyTotals.staffTotals).map(([name, totals]) => (
                                      <div key={name} className="flex justify-between text-xs">
                                        <span className="text-slate-600 truncate">{name}:</span>
                                        <div className="flex space-x-2">
                                          <span className="text-blue-600">{totals.hours.toFixed(1)}h</span>
                                          {currentUser?.role === 'admin' && (
                                            <span className="text-emerald-600">{formatCurrency(totals.pay)}</span>
                                          )}
                                        </div>
                                      </div>
                                    ))
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })()}

                      {/* Calendar Year Totals */}
                      {(() => {
                        const yearTotals = getYearToDateTotals(false); // Calendar year for admin
                        
                        return (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm font-medium text-slate-700">
                                📊 Calendar Year {yearTotals.startDate.getFullYear()}
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Total Hours:</span>
                                <span className="font-medium text-blue-600">{yearTotals.totalHours.toFixed(1)}h</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Gross Pay:</span>
                                {currentUser?.role === 'admin' && (
                                  <span className="font-medium text-emerald-600">{formatCurrency(yearTotals.totalPay)}</span>
                                )}
                              </div>
                              <div className="text-xs text-slate-500">
                                {yearTotals.startDate.toLocaleDateString('en-AU')} - {yearTotals.endDate.toLocaleDateString('en-AU')}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })()}

                      {/* Financial Year Totals */}
                      {(() => {
                        const fyTotals = getYearToDateTotals(true); // Financial year
                        
                        return (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm font-medium text-slate-700">
                                💰 Financial Year
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Total Hours:</span>
                                <span className="font-medium text-blue-600">{fyTotals.totalHours.toFixed(1)}h</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Gross Pay:</span>
                                {currentUser?.role === 'admin' && (
                                  <span className="font-medium text-emerald-600">{formatCurrency(fyTotals.totalPay)}</span>
                                )}
                              </div>
                              <div className="text-xs text-slate-500">
                                FY {fyTotals.startDate.getFullYear()}/{String(fyTotals.endDate.getFullYear()).slice(-2)}
                              </div>
                              <div className="text-xs text-slate-400">
                                {fyTotals.startDate.toLocaleDateString('en-AU')} - {fyTotals.endDate.toLocaleDateString('en-AU')}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })()}
                    </div>
                  </CardContent>
                          )}
                        </Card>
                      );
                    })}
                  </div>
                </>
              )}
              
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <div className="text-sm text-slate-500">
                  💡 Tip: Templates save shift patterns but not staff assignments
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setShowManageTemplatesDialog(false);
                      setShowSaveTemplateDialog(true);
                    }}
                  >
                    Save Current Roster
                  </Button>
                  <Button variant="outline" onClick={() => setShowManageTemplatesDialog(false)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Comprehensive Template Edit Dialog */}
        <Dialog open={showTemplateEditDialog} onOpenChange={setShowTemplateEditDialog}>
          <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-slate-800">
                🎯 Advanced Template Configuration
              </DialogTitle>
            </DialogHeader>
            {selectedRosterTemplateForEdit && (
              <div className="space-y-6">
                {/* Basic Template Information */}
                <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
                  <h3 className="text-lg font-semibold text-slate-800">📋 Template Details</h3>
                  
                  <div>
                    <Label htmlFor="template-name">Template Name</Label>
                    <Input
                      id="template-name"
                      value={selectedRosterTemplateForEdit.name}
                      onChange={(e) => setSelectedRosterTemplateForEdit({
                        ...selectedRosterTemplateForEdit,
                        name: e.target.value
                      })}
                      placeholder="Enter template name"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="template-description">Description (Optional)</Label>
                    <textarea
                      id="template-description"
                      className="w-full p-3 border rounded-md"
                      rows={3}
                      value={selectedRosterTemplateForEdit.description || ''}
                      onChange={(e) => setSelectedRosterTemplateForEdit({
                        ...selectedRosterTemplateForEdit,
                        description: e.target.value
                      })}
                      placeholder="Describe this template's purpose or usage..."
                    />
                  </div>
                </div>

                {/* Advanced 2:1 Shift Configuration */}
                <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="text-lg font-semibold text-blue-800 flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>2:1 Shift Support Configuration</span>
                  </h3>
                  
                  {/* Enable 2:1 Shift Toggle */}
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={selectedRosterTemplateForEdit.enable_2_1_shift || false}
                          onCheckedChange={(checked) => setSelectedRosterTemplateForEdit({
                            ...selectedRosterTemplateForEdit,
                            enable_2_1_shift: checked
                          })}
                        />
                        <Label className="font-medium text-slate-800">Enable 2:1 Shift (Two Staff Members)</Label>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        Allow multiple staff members to be assigned to the same shift time for enhanced support scenarios
                      </p>
                    </div>
                  </div>

                  {/* Allow Override Toggle */}
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={selectedRosterTemplateForEdit.allow_overlap_override || false}
                          onCheckedChange={(checked) => setSelectedRosterTemplateForEdit({
                            ...selectedRosterTemplateForEdit,
                            allow_overlap_override: checked
                          })}
                        />
                        <Label className="font-medium text-slate-800">Allow Override (Allow Overlap Detection)</Label>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        Override automatic overlap detection and allow manual scheduling conflicts when necessary
                      </p>
                    </div>
                  </div>
                </div>

                {/* Template Loading Behavior Configuration */}
                <div className="space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <h3 className="text-lg font-semibold text-amber-800 flex items-center space-x-2">
                    <Download className="w-5 h-5" />
                    <span>Template Loading Behavior</span>
                  </h3>

                  {/* Duplicate Entry Prevention */}
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={selectedRosterTemplateForEdit.prevent_duplicate_unassigned || true}
                          onCheckedChange={(checked) => setSelectedRosterTemplateForEdit({
                            ...selectedRosterTemplateForEdit,
                            prevent_duplicate_unassigned: checked
                          })}
                        />
                        <Label className="font-medium text-slate-800">Prevent Duplicate Unassigned Shifts</Label>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        <strong>Do NOT Allow</strong> duplicate entries when loading template if shifts are unassigned
                      </p>
                    </div>
                  </div>

                  {/* Different Staff Only */}
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={selectedRosterTemplateForEdit.allow_different_staff_only || true}
                          onCheckedChange={(checked) => setSelectedRosterTemplateForEdit({
                            ...selectedRosterTemplateForEdit,
                            allow_different_staff_only: checked
                          })}
                        />
                        <Label className="font-medium text-slate-800">Allow Different Staff Only</Label>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        <strong>Allow</strong> duplicates when loading template if staff is assigned but only for different staff members (not the same staff)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Configuration Summary */}
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="text-md font-semibold text-green-800 mb-2">📊 Configuration Summary</h4>
                  <div className="text-sm text-green-700 space-y-1">
                    <p>• <strong>2:1 Support:</strong> {selectedRosterTemplateForEdit.enable_2_1_shift ? '✅ Enabled - Multiple staff can work same shift' : '❌ Disabled - Single staff per shift'}</p>
                    <p>• <strong>Overlap Override:</strong> {selectedRosterTemplateForEdit.allow_overlap_override ? '✅ Enabled - Manual conflicts allowed' : '❌ Disabled - Strict overlap detection'}</p>
                    <p>• <strong>Unassigned Duplicates:</strong> {selectedRosterTemplateForEdit.prevent_duplicate_unassigned ? '🚫 Prevented - No duplicate unassigned shifts' : '✅ Allowed - Duplicate unassigned shifts permitted'}</p>
                    <p>• <strong>Assigned Duplicates:</strong> {selectedRosterTemplateForEdit.allow_different_staff_only ? '👥 Different Staff Only - Duplicates only with different staff' : '🔓 All Duplicates Allowed'}</p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setShowTemplateEditDialog(false);
                      setSelectedRosterTemplateForEdit(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    onClick={saveRosterTemplateEdits}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    💾 Save Template Configuration
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Year-to-Date Report Dialog */}
        <Dialog open={showYTDReportDialog} onOpenChange={setShowYTDReportDialog}>
          <DialogContent className="max-w-6xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-slate-800">
                📊 {isStaff() ? 'My Year-to-Date Report & Tax Summary' : 'Year-to-Date Report & Tax Calculator'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              {/* Report Type Toggle */}
              <div className="flex items-center justify-center space-x-4 p-4 bg-slate-50 rounded-lg">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="ytdReportType"
                    value="calendar"
                    checked={ytdReportType === 'calendar'}
                    onChange={(e) => setYTDReportType(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="font-medium">📅 Calendar Year</span>
                  <span className="text-sm text-slate-500">(Jan-Dec)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="ytdReportType"
                    value="financial"
                    checked={ytdReportType === 'financial'}
                    onChange={(e) => setYTDReportType(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="font-medium">💰 Financial Year</span>
                  <span className="text-sm text-slate-500">(Jul-Jun)</span>
                </label>
              </div>

              {(() => {
                const ytdData = getYearToDateTotals(ytdReportType === 'financial');
                
                return (
                  <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-slate-700">
                            📅 {ytdData.period}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-xs text-slate-500 mb-2">
                            {ytdData.startDate.toLocaleDateString('en-AU')} - {ytdData.endDate.toLocaleDateString('en-AU')}
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-slate-600">Total Hours:</span>
                              <span className="font-bold text-blue-600">{ytdData.totalHours.toFixed(1)}h</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-slate-600">Gross Pay:</span>
                              <span className="font-bold text-emerald-600">{formatCurrency(ytdData.totalPay)}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-slate-700">
                            👥 Total Staff
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-blue-600 mb-2">
                            {Object.keys(ytdData.staffTotals).length}
                          </div>
                          <div className="text-xs text-slate-500">
                            Active staff with assigned shifts this period
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-slate-700">
                            📊 Average
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-600">Per Staff:</span>
                              <span className="font-medium text-blue-600">
                                {Object.keys(ytdData.staffTotals).length > 0 
                                  ? (ytdData.totalHours / Object.keys(ytdData.staffTotals).length).toFixed(1) 
                                  : '0'}h
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-600">Pay/Hour:</span>
                              <span className="font-medium text-emerald-600">
                                {ytdData.totalHours > 0 
                                  ? formatCurrency(ytdData.totalPay / ytdData.totalHours) 
                                  : formatCurrency(0)}
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Individual Staff Breakdown */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg font-bold text-slate-800">
                          👤 Individual Staff Breakdown
                        </CardTitle>
                        <div className="text-sm text-slate-600">
                          Comprehensive hours, gross pay, and after-tax calculations for each staff member
                        </div>
                      </CardHeader>
                      <CardContent>
                        {Object.keys(ytdData.staffTotals).length === 0 ? (
                          <div className="text-center py-8">
                            <div className="text-slate-400 mb-2">📊</div>
                            <div className="text-lg font-semibold text-slate-600 mb-2">No Data Available</div>
                            <div className="text-slate-500">No assigned shifts found for the selected period.</div>
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b border-slate-200">
                                  <th className="text-left py-3 px-2 font-semibold text-slate-700">Staff Member</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">Hours Worked</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">Gross Pay</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">Est. Tax</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">Superannuation</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">After-Tax Pay</th>
                                  <th className="text-right py-3 px-2 font-semibold text-slate-700">Avg Rate</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(ytdData.staffTotals)
                                  .sort(([, a], [, b]) => b.hours - a.hours) // Sort by hours descending
                                  .map(([staffName, totals]) => {
                                    const staffMember = staff.find(s => s.name === staffName);
                                    const taxDetails = calculateAfterTaxPay(totals.grossPay, staffMember);
                                    const avgRate = totals.hours > 0 ? totals.grossPay / totals.hours : 0;
                                    
                                    return (
                                      <tr key={staffName} className="border-b border-slate-100 hover:bg-slate-50">
                                        <td className="py-3 px-2">
                                          <div className="font-medium text-slate-800">{staffName}</div>
                                          <div className="text-xs text-slate-500">
                                            {staffMember?.active ? '✅ Active' : '❌ Inactive'}
                                          </div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-medium text-blue-600">{totals.hours.toFixed(1)}h</div>
                                          <div className="text-xs text-slate-500">
                                            {((totals.hours / ytdData.totalHours) * 100).toFixed(1)}%
                                          </div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-medium text-emerald-600">{formatCurrency(totals.grossPay)}</div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-medium text-red-600">-{formatCurrency(taxDetails.tax)}</div>
                                          <div className="text-xs text-slate-500">
                                            {((taxDetails.tax / totals.grossPay) * 100).toFixed(1)}%
                                          </div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-medium text-orange-600">-{formatCurrency(taxDetails.totalSuper)}</div>
                                          <div className="text-xs text-slate-500">
                                            {((taxDetails.totalSuper / totals.grossPay) * 100).toFixed(1)}%
                                          </div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-bold text-green-600">{formatCurrency(taxDetails.afterTaxPay)}</div>
                                          <div className="text-xs text-slate-500">
                                            {((taxDetails.afterTaxPay / totals.grossPay) * 100).toFixed(1)}%
                                          </div>
                                        </td>
                                        <td className="text-right py-3 px-2">
                                          <div className="font-medium text-slate-700">{formatCurrency(avgRate)}/h</div>
                                        </td>
                                      </tr>
                                    );
                                  })}
                              </tbody>
                              <tfoot>
                                <tr className="border-t-2 border-slate-300 bg-slate-50">
                                  <td className="py-3 px-2 font-bold text-slate-800">TOTALS</td>
                                  <td className="text-right py-3 px-2 font-bold text-blue-600">
                                    {ytdData.totalHours.toFixed(1)}h
                                  </td>
                                  <td className="text-right py-3 px-2 font-bold text-emerald-600">
                                    {formatCurrency(ytdData.totalPay)}
                                  </td>
                                  <td className="text-right py-3 px-2 font-bold text-red-600">
                                    -{formatCurrency(Object.values(ytdData.staffTotals).reduce((sum, s) => {
                                      const staffMember = staff.find(st => st.name === Object.keys(ytdData.staffTotals).find(name => ytdData.staffTotals[name] === s));
                                      return sum + calculateAfterTaxPay(s.grossPay, staffMember).tax;
                                    }, 0))}
                                  </td>
                                  <td className="text-right py-3 px-2 font-bold text-orange-600">
                                    -{formatCurrency(Object.values(ytdData.staffTotals).reduce((sum, s) => {
                                      const staffMember = staff.find(st => st.name === Object.keys(ytdData.staffTotals).find(name => ytdData.staffTotals[name] === s));
                                      return sum + calculateAfterTaxPay(s.grossPay, staffMember).totalSuper;
                                    }, 0))}
                                  </td>
                                  <td className="text-right py-3 px-2 font-bold text-green-600">
                                    {formatCurrency(Object.values(ytdData.staffTotals).reduce((sum, s) => {
                                      const staffMember = staff.find(st => st.name === Object.keys(ytdData.staffTotals).find(name => ytdData.staffTotals[name] === s));
                                      return sum + calculateAfterTaxPay(s.grossPay, staffMember).afterTaxPay;
                                    }, 0))}
                                  </td>
                                  <td className="text-right py-3 px-2 font-bold text-slate-700">
                                    {ytdData.totalHours > 0 ? formatCurrency(ytdData.totalPay / ytdData.totalHours) : formatCurrency(0)}/h
                                  </td>
                                </tr>
                              </tfoot>
                            </table>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Tax Information */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg font-bold text-slate-800">
                          💡 Tax & Superannuation Information
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4 text-sm">
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <h4 className="font-semibold text-blue-800 mb-2">Australian Tax Brackets (2024-25)</h4>
                            <div className="space-y-1 text-blue-700">
                              <div>$0 - $18,200: <strong>0%</strong> (Tax-free threshold)</div>
                              <div>$18,201 - $45,000: <strong>19%</strong></div>
                              <div>$45,001 - $120,000: <strong>32.5%</strong></div>
                              <div>$120,001 - $180,000: <strong>37%</strong></div>
                              <div>$180,001+: <strong>45%</strong></div>
                            </div>
                          </div>
                          
                          <div className="bg-orange-50 p-4 rounded-lg">
                            <h4 className="font-semibold text-orange-800 mb-2">Superannuation</h4>
                            <div className="text-orange-700">
                              <div><strong>Mandatory Rate:</strong> 11.5% (default)</div>
                              <div><strong>Additional Contributions:</strong> Staff can set custom rates or dollar amounts</div>
                            </div>
                          </div>
                          
                          <div className="bg-slate-50 p-4 rounded-lg">
                            <h4 className="font-semibold text-slate-800 mb-2">Important Notes</h4>
                            <div className="text-slate-600 space-y-1">
                              <div>• Tax calculations are estimates based on annual income</div>
                              <div>• Does not include Medicare levy (2%) or other deductions</div>
                              <div>• Individual circumstances may affect actual tax liability</div>
                              <div>• Staff can configure custom tax brackets in their profiles</div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                );
              })()}

              <div className="flex justify-between items-center pt-4 border-t border-slate-200">
                <div className="text-sm text-slate-500">
                  💡 Tip: Export functionality coming soon - save this data for your records
                </div>
                <Button variant="outline" onClick={() => setShowYTDReportDialog(false)}>
                  Close Report
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Day Template Dialog */}
        <Dialog open={showDayTemplateDialog} onOpenChange={setShowDayTemplateDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {dayTemplateAction === 'save' ? 'Save Day as Template' : 'Load Day Template'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {selectedDateForTemplate && (
                <div className="text-sm text-slate-600 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p><strong>Selected Date:</strong> {selectedDateForTemplate.toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}</p>
                </div>
              )}

              {dayTemplateAction === 'save' && (
                <>
                  <div>
                    <Label htmlFor="day-template-name">Template Name</Label>
                    <Input
                      id="day-template-name"
                      value={newDayTemplateName}
                      onChange={(e) => setNewDayTemplateName(e.target.value)}
                      placeholder="Enter template name (e.g., 'Busy Monday', 'Light Friday')"
                    />
                  </div>
                  <div className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg">
                    <p><strong>This will save:</strong></p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>All shift times from this specific day</li>
                      <li>Sleepover status for each shift</li>
                      <li>Reusable template for any future date</li>
                    </ul>
                    <p className="mt-2"><strong>Note:</strong> Staff assignments are NOT saved in templates.</p>
                  </div>
                </>
              )}

              {dayTemplateAction === 'load' && (
                <>
                  <div>
                    <Label htmlFor="day-template-select">Select Day Template</Label>
                    <Select 
                      value={selectedDayTemplate || ''} 
                      onValueChange={setSelectedDayTemplate}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a day template" />
                      </SelectTrigger>
                      <SelectContent>
                        {dayTemplates.map(template => (
                          <SelectItem key={template.id} value={template.id}>
                            {template.name}
                            <span className="text-sm text-slate-500 ml-2">
                              ({template.shifts?.length || 0} shifts)
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {dayTemplates.length === 0 && (
                    <div className="text-sm text-slate-600 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p><strong>No day templates found.</strong></p>
                      <p>Save a day first by hovering over a calendar day and clicking the "S" button.</p>
                    </div>
                  )}
                  
                  <div className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg">
                    <p><strong>This will:</strong></p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>Add all shifts from the template to the selected date</li>
                      <li>Prevent overlaps with existing shifts</li>
                      <li>Create unassigned shifts (you assign staff manually)</li>
                    </ul>
                  </div>
                </>
              )}
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowDayTemplateDialog(false)}>
                  Cancel
                </Button>
                {dayTemplateAction === 'save' ? (
                  <Button onClick={saveDayAsTemplate}>
                    Save Day Template
                  </Button>
                ) : (
                  <Button 
                    onClick={applyDayTemplate}
                    disabled={!selectedDayTemplate}
                  >
                    Apply Template
                  </Button>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Calendar Event Dialog */}
        <Dialog open={showEventDialog} onOpenChange={setShowEventDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {selectedEvent ? 'Edit Event' : 'Add New Event'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="event-title">Title *</Label>
                  <Input
                    id="event-title"
                    value={selectedEvent ? selectedEvent.title : newEvent.title}
                    onChange={(e) => {
                      if (selectedEvent) {
                        setSelectedEvent({...selectedEvent, title: e.target.value});
                      } else {
                        setNewEvent({...newEvent, title: e.target.value});
                      }
                    }}
                    placeholder="Event title"
                  />
                </div>
                
                <div>
                  <Label htmlFor="event-date">Date *</Label>
                  <Input
                    id="event-date"
                    type="date"
                    value={selectedEvent ? selectedEvent.date : newEvent.date}
                    onChange={(e) => {
                      if (selectedEvent) {
                        setSelectedEvent({...selectedEvent, date: e.target.value});
                      } else {
                        setNewEvent({...newEvent, date: e.target.value});
                      }
                    }}
                  />
                </div>
                
                <div>
                  <Label htmlFor="event-type">Type</Label>
                  <Select 
                    value={selectedEvent ? selectedEvent.event_type : newEvent.event_type}
                    onValueChange={(value) => {
                      if (selectedEvent) {
                        setSelectedEvent({...selectedEvent, event_type: value});
                      } else {
                        setNewEvent({...newEvent, event_type: value});
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="appointment">📅 Appointment</SelectItem>
                      <SelectItem value="meeting">👥 Meeting</SelectItem>
                      <SelectItem value="task">✓ Task</SelectItem>
                      <SelectItem value="reminder">🔔 Reminder</SelectItem>
                      <SelectItem value="personal">👤 Personal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={selectedEvent ? selectedEvent.is_all_day : newEvent.is_all_day}
                  onCheckedChange={(checked) => {
                    if (selectedEvent) {
                      setSelectedEvent({...selectedEvent, is_all_day: checked});
                    } else {
                      setNewEvent({...newEvent, is_all_day: checked});
                    }
                  }}
                />
                <Label>All day event</Label>
              </div>

              {!(selectedEvent ? selectedEvent.is_all_day : newEvent.is_all_day) && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="event-start-time">Start Time</Label>
                    <Input
                      id="event-start-time"
                      type="time"
                      value={selectedEvent ? selectedEvent.start_time : newEvent.start_time}
                      onChange={(e) => {
                        if (selectedEvent) {
                          setSelectedEvent({...selectedEvent, start_time: e.target.value});
                        } else {
                          setNewEvent({...newEvent, start_time: e.target.value});
                        }
                      }}
                    />
                  </div>
                  <div>
                    <Label htmlFor="event-end-time">End Time</Label>
                    <Input
                      id="event-end-time"
                      type="time"
                      value={selectedEvent ? selectedEvent.end_time : newEvent.end_time}
                      onChange={(e) => {
                        if (selectedEvent) {
                          setSelectedEvent({...selectedEvent, end_time: e.target.value});
                        } else {
                          setNewEvent({...newEvent, end_time: e.target.value});
                        }
                      }}
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="event-priority">Priority</Label>
                  <Select 
                    value={selectedEvent ? selectedEvent.priority : newEvent.priority}
                    onValueChange={(value) => {
                      if (selectedEvent) {
                        setSelectedEvent({...selectedEvent, priority: value});
                      } else {
                        setNewEvent({...newEvent, priority: value});
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="event-reminder">Reminder (minutes)</Label>
                  <Input
                    id="event-reminder"
                    type="number"
                    value={selectedEvent ? selectedEvent.reminder_minutes : newEvent.reminder_minutes}
                    onChange={(e) => {
                      if (selectedEvent) {
                        setSelectedEvent({...selectedEvent, reminder_minutes: parseInt(e.target.value)});
                      } else {
                        setNewEvent({...newEvent, reminder_minutes: parseInt(e.target.value)});
                      }
                    }}
                    placeholder="15"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="event-location">Location</Label>
                <Input
                  id="event-location"
                  value={selectedEvent ? selectedEvent.location : newEvent.location}
                  onChange={(e) => {
                    if (selectedEvent) {
                      setSelectedEvent({...selectedEvent, location: e.target.value});
                    } else {
                      setNewEvent({...newEvent, location: e.target.value});
                    }
                  }}
                  placeholder="Event location"
                />
              </div>

              <div>
                <Label htmlFor="event-description">Description</Label>
                <Input
                  id="event-description"
                  value={selectedEvent ? selectedEvent.description : newEvent.description}
                  onChange={(e) => {
                    if (selectedEvent) {
                      setSelectedEvent({...selectedEvent, description: e.target.value});
                    } else {
                      setNewEvent({...newEvent, description: e.target.value});
                    }
                  }}
                  placeholder="Event description or notes"
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => {
                  setShowEventDialog(false);
                  setSelectedEvent(null);
                }}>
                  Cancel
                </Button>
                {selectedEvent && (
                  <Button variant="destructive" onClick={() => deleteCalendarEvent(selectedEvent.id)}>
                    Delete
                  </Button>
                )}
                <Button onClick={selectedEvent ? updateCalendarEvent : addCalendarEvent}>
                  {selectedEvent ? 'Update Event' : 'Add Event'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Bulk Actions Dialog */}
        <Dialog open={showBulkActionsDialog} onOpenChange={setShowBulkActionsDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Bulk Edit Selected Shifts</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="text-sm text-slate-600 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p><strong>Selected:</strong> {selectedShifts.size} shifts</p>
                <p>Choose which properties to update for all selected shifts.</p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="bulk-staff" className="w-4 h-4" />
                  <Label htmlFor="bulk-staff">Assign Staff Member</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="bulk-sleepover" className="w-4 h-4" />
                  <Label htmlFor="bulk-sleepover">Set Sleepover Status</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="bulk-shift-type" className="w-4 h-4" />
                  <Label htmlFor="bulk-shift-type">Override Shift Type</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="bulk-hourly-rate" className="w-4 h-4" />
                  <Label htmlFor="bulk-hourly-rate">Override Hourly Rate</Label>
                </div>
              </div>

              <div className="text-sm text-slate-500 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p><strong>Note:</strong> This is a preview of bulk editing functionality. Select the properties you want to modify and click "Apply Changes" to update all selected shifts at once.</p>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowBulkActionsDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={() => {
                  alert('Bulk editing functionality coming soon! For now, you can use bulk delete.');
                  setShowBulkActionsDialog(false);
                }}>
                  Apply Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Bulk Edit Templates Dialog */}
        <Dialog open={showBulkEditDialog} onOpenChange={setShowBulkEditDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Bulk Edit Shift Templates</DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-700">
                  <strong>Editing {selectedTemplates.size} selected template(s)</strong>
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Only fields you modify will be applied to the selected templates. Leave fields empty to keep existing values.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Time Settings */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Time Settings</h3>
                  
                  <div>
                    <Label htmlFor="bulk-start-time">Start Time</Label>
                    <Input
                      id="bulk-start-time"
                      type="time"
                      value={bulkEditData.start_time}
                      onChange={(e) => setBulkEditData({...bulkEditData, start_time: e.target.value})}
                      placeholder="Keep existing time"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="bulk-end-time">End Time</Label>
                    <Input
                      id="bulk-end-time"
                      type="time"
                      value={bulkEditData.end_time}
                      onChange={(e) => setBulkEditData({...bulkEditData, end_time: e.target.value})}
                      placeholder="Keep existing time"
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={bulkEditData.is_sleepover}
                      onCheckedChange={(checked) => setBulkEditData({...bulkEditData, is_sleepover: checked})}
                    />
                    <Label>Sleepover Shift</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={bulkEditData.allow_overlap || false}
                      onCheckedChange={(checked) => setBulkEditData({...bulkEditData, allow_overlap: checked})}
                    />
                    <Label>Allow 2:1 Shift Overlapping</Label>
                  </div>
                </div>

                {/* Advanced Settings */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Advanced Settings</h3>
                  
                  <div>
                    <Label htmlFor="bulk-shift-type">Manual Shift Type Override</Label>
                    <Select
                      value={bulkEditData.shift_type_override || 'auto'}
                      onValueChange={(value) => setBulkEditData({...bulkEditData, shift_type_override: value === 'auto' ? '' : value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Keep existing type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">No Override (Auto-detect)</SelectItem>
                        <SelectItem value="weekday_day">Weekday Day</SelectItem>
                        <SelectItem value="weekday_evening">Weekday Evening</SelectItem>
                        <SelectItem value="weekday_night">Weekday Night</SelectItem>
                        <SelectItem value="saturday">Saturday</SelectItem>
                        <SelectItem value="sunday">Sunday</SelectItem>
                        <SelectItem value="public_holiday">Public Holiday</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="bulk-day-change">Move to Different Day</Label>
                    <Select
                      value={bulkEditData.day_of_week.toString() || 'keep'}
                      onValueChange={(value) => setBulkEditData({...bulkEditData, day_of_week: value === 'keep' ? '' : value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Keep current day" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="keep">Keep Current Day</SelectItem>
                        <SelectItem value="0">Monday</SelectItem>
                        <SelectItem value="1">Tuesday</SelectItem>
                        <SelectItem value="2">Wednesday</SelectItem>
                        <SelectItem value="3">Thursday</SelectItem>
                        <SelectItem value="4">Friday</SelectItem>
                        <SelectItem value="5">Saturday</SelectItem>
                        <SelectItem value="6">Sunday</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Action Options */}
              <div className="space-y-3">
                <h3 className="font-semibold text-lg">Action Options</h3>
                <div className="flex space-x-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="apply-selected"
                      name="apply-to"
                      value="selected"
                      checked={bulkEditData.apply_to === 'selected'}
                      onChange={(e) => setBulkEditData({...bulkEditData, apply_to: e.target.value})}
                      className="w-4 h-4"
                    />
                    <Label htmlFor="apply-selected">Apply to Selected Templates Only</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="apply-all"
                      name="apply-to"
                      value="all"
                      checked={bulkEditData.apply_to === 'all'}
                      onChange={(e) => setBulkEditData({...bulkEditData, apply_to: e.target.value})}
                      className="w-4 h-4"
                    />
                    <Label htmlFor="apply-all">Apply to All Templates</Label>
                  </div>
                </div>
              </div>

              <div className="text-sm text-amber-600 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p><strong>⚠️ Warning:</strong> Bulk editing will modify multiple shift templates at once. This action cannot be undone. Please review your changes carefully before applying.</p>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowBulkEditDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={applyBulkEdit} disabled={selectedTemplates.size === 0}>
                  Apply Bulk Edit to {selectedTemplates.size} Template(s)
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* User Profile Dialog */}
        <Dialog open={showProfileDialog} onOpenChange={setShowProfileDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <User className="w-5 h-5" />
                <span>My Profile</span>
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              {/* User Info */}
              <div className="flex items-center space-x-4 p-4 bg-slate-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  {currentUser?.first_name?.charAt(0) || currentUser?.username?.charAt(0) || 'U'}
                </div>
                <div>
                  <h3 className="font-semibold text-lg">{currentUser?.first_name || currentUser?.username}</h3>
                  <p className="text-slate-600 capitalize">{currentUser?.role || 'User'}</p>
                </div>
              </div>

              {/* Editable Personal Details */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-700">Personal Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Username</Label>
                    <Input 
                      value={currentUser?.username || ''}
                      disabled
                      className="bg-gray-100"
                    />
                    <p className="text-xs text-gray-500 mt-1">Username cannot be changed</p>
                  </div>
                  <div>
                    <Label className="text-sm">First Name</Label>
                    <Input 
                      value={profileData.first_name || currentUser?.first_name || ''}
                      onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                      placeholder="Enter first name"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Last Name</Label>
                    <Input 
                      value={profileData.last_name || currentUser?.last_name || ''}
                      onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                      placeholder="Enter last name"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Email Address</Label>
                    <Input 
                      type="email"
                      value={profileData.email || currentUser?.email || ''}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      placeholder="Enter email address"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Phone Number</Label>
                    <Input 
                      type="tel"
                      value={profileData.phone || currentUser?.phone || ''}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      placeholder="Enter phone number"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Role</Label>
                    <Input 
                      value={currentUser?.role || 'User'}
                      disabled
                      className="bg-gray-100 capitalize"
                    />
                    <p className="text-xs text-gray-500 mt-1">Role assigned by administrator</p>
                  </div>
                </div>
                
                <div>
                  <Label className="text-sm">Address</Label>
                  <AddressAutocomplete
                    value={profileData.address || currentUser?.address || ''}
                    onChange={(value) => setProfileData({ ...profileData, address: value })}
                    placeholder="Start typing your address..."
                  />
                </div>
              </div>

              {/* Account Information */}
              <div className="space-y-3">
                <h4 className="font-medium text-slate-700">Account Information</h4>
                <div className="grid grid-cols-1 gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Account Status:</span>
                    <Badge variant="outline" className="bg-green-50 text-green-700">Active</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Last Login:</span>
                    <span className="font-medium">{currentUser?.last_login ? new Date(currentUser.last_login).toLocaleString() : 'Just now'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Member Since:</span>
                    <span className="font-medium">{currentUser?.created_at ? new Date(currentUser.created_at).toLocaleDateString() : 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col space-y-2">
                <Button
                  onClick={async () => {
                    try {
                      // Save profile updates
                      const response = await axios.put(`${API_BASE_URL}/api/users/me`, profileData);
                      setCurrentUser({ ...currentUser, ...response.data });
                      alert('✅ Profile updated successfully!');
                    } catch (error) {
                      console.error('Error updating profile:', error);
                      alert(`❌ Error updating profile: ${error.response?.data?.detail || error.message}`);
                    }
                  }}
                  className="w-full"
                >
                  Save Profile Changes
                </Button>
                <Button
                  onClick={() => {
                    setShowProfileDialog(false);
                    setShowChangePinDialog(true);
                  }}
                  variant="outline"
                  className="w-full"
                >
                  Change PIN
                </Button>
                <Button variant="outline" onClick={() => setShowProfileDialog(false)}>
                  Close
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Staff Profile Dialog (Admin) - Comprehensive */}
        {currentUser?.role === 'admin' && (
          <Dialog open={showStaffProfileDialog} onOpenChange={setShowStaffProfileDialog}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Staff Profile - {selectedStaffForProfile?.name}</span>
                </DialogTitle>
              </DialogHeader>
              {selectedStaffForProfile && (
                <div className="space-y-6">
                  {/* Staff Basic Info & Photo */}
                  <div className="flex items-start space-x-6 p-4 bg-slate-50 rounded-lg">
                    <div className="flex-shrink-0">
                      {selectedStaffForProfile.profile_photo_url ? (
                        <img 
                          src={selectedStaffForProfile.profile_photo_url} 
                          alt={selectedStaffForProfile.name}
                          className="w-24 h-24 rounded-full object-cover border-2 border-gray-300"
                        />
                      ) : (
                        <div className="w-24 h-24 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                          {selectedStaffForProfile.name.charAt(0)}
                        </div>
                      )}
                      <div className="mt-2">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          id="profile-photo-upload"
                          onChange={(e) => {
                            // TODO: Handle profile photo upload
                            console.log('Profile photo selected:', e.target.files[0]);
                          }}
                        />
                        <label htmlFor="profile-photo-upload" className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
                          Upload Photo
                        </label>
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-xl mb-2">{selectedStaffForProfile.name}</h3>
                      <Badge variant={selectedStaffForProfile.active ? "default" : "secondary"}>
                        {selectedStaffForProfile.active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </div>

                  {/* Tabbed Content */}
                  <div className="space-y-4">
                    {/* Basic Information */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Basic Information</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Full Name</Label>
                          <Input 
                            value={selectedStaffForProfile.name}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              name: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Date of Birth</Label>
                          <Input 
                            type="date"
                            value={selectedStaffForProfile.date_of_birth}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              date_of_birth: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Email Address</Label>
                          <Input 
                            type="email"
                            value={selectedStaffForProfile.email}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              email: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Best Contact Phone</Label>
                          <Input 
                            type="tel"
                            value={selectedStaffForProfile.phone}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              phone: e.target.value
                            })}
                          />
                        </div>
                        <div className="md:col-span-2">
                          <Label className="text-sm font-medium">Postal Address</Label>
                          <Input 
                            value={selectedStaffForProfile.postal_address}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              postal_address: e.target.value
                            })}
                            placeholder="Street Address, City, State, Postcode"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Emergency Contact */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Emergency Contact</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Emergency Contact Name</Label>
                          <Input 
                            value={selectedStaffForProfile.emergency_contact_name}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              emergency_contact_name: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Emergency Contact Phone</Label>
                          <Input 
                            type="tel"
                            value={selectedStaffForProfile.emergency_contact_phone}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              emergency_contact_phone: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Relationship to Staff</Label>
                          <Input 
                            value={selectedStaffForProfile.emergency_contact_relationship}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              emergency_contact_relationship: e.target.value
                            })}
                            placeholder="e.g., Parent, Spouse, Sibling"
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Emergency Contact Address</Label>
                          <Input 
                            value={selectedStaffForProfile.emergency_contact_address}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              emergency_contact_address: e.target.value
                            })}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Professional Information */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Professional Information</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium">NDIS Registration Number</Label>
                          <Input 
                            value={selectedStaffForProfile.ndis_registration}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              ndis_registration: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Blue Card Number</Label>
                          <Input 
                            value={selectedStaffForProfile.blue_card_number}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              blue_card_number: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Yellow Card Number</Label>
                          <Input 
                            value={selectedStaffForProfile.yellow_card_number}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              yellow_card_number: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">First Aid Registration Number</Label>
                          <Input 
                            value={selectedStaffForProfile.first_aid_registration}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              first_aid_registration: e.target.value
                            })}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">First Aid Expiry Date</Label>
                          <Input 
                            type="date"
                            value={selectedStaffForProfile.first_aid_expiry}
                            onChange={(e) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              first_aid_expiry: e.target.value
                            })}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Transport & Licensing */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Transport & Licensing</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="has-license"
                              checked={selectedStaffForProfile.has_license}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                has_license: e.target.checked
                              })}
                              className="rounded"
                            />
                            <Label htmlFor="has-license" className="text-sm">Has Current Driver's License</Label>
                          </div>
                          {selectedStaffForProfile.has_license && (
                            <div>
                              <Label className="text-sm font-medium">License Class</Label>
                              <Select 
                                value={selectedStaffForProfile.license_class}
                                onValueChange={(value) => setSelectedStaffForProfile({
                                  ...selectedStaffForProfile,
                                  license_class: value
                                })}
                              >
                                <SelectTrigger>
                                  <SelectValue placeholder="Select license class" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="C">Class C (Car)</SelectItem>
                                  <SelectItem value="LR">LR (Light Rigid)</SelectItem>
                                  <SelectItem value="MR">MR (Medium Rigid)</SelectItem>
                                  <SelectItem value="HR">HR (Heavy Rigid)</SelectItem>
                                  <SelectItem value="HC">HC (Heavy Combination)</SelectItem>
                                  <SelectItem value="MC">MC (Multi-Combination)</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          )}
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="can-drive-van"
                              checked={selectedStaffForProfile.can_drive_van}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                can_drive_van: e.target.checked
                              })}
                              className="rounded"
                            />
                            <Label htmlFor="can-drive-van" className="text-sm">Can Drive Van for Client Transport</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="can-transport-wheelchair"
                              checked={selectedStaffForProfile.can_transport_wheelchair}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                can_transport_wheelchair: e.target.checked
                              })}
                              className="rounded"
                            />
                            <Label htmlFor="can-transport-wheelchair" className="text-sm">Can Transport Power Wheelchairs</Label>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Experience & Skills */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Experience & Skills</h4>
                      <div className="space-y-4">
                        <div>
                          <Label className="text-sm font-medium mb-3 block">Disability Support Experience</Label>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {[
                              'Personal Care', 'Meal Preparation', 'Medication Management', 
                              'Community Access', 'Behavioral Support', 'Mobility Assistance',
                              'Communication Support', 'Daily Living Skills', 'Social Support'
                            ].map((skill) => (
                              <div key={skill} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`disability-${skill}`}
                                  checked={selectedStaffForProfile.disability_support_experience?.includes(skill) || false}
                                  onChange={(e) => {
                                    const currentExp = selectedStaffForProfile.disability_support_experience || [];
                                    if (e.target.checked) {
                                      setSelectedStaffForProfile({
                                        ...selectedStaffForProfile,
                                        disability_support_experience: [...currentExp, skill]
                                      });
                                    } else {
                                      setSelectedStaffForProfile({
                                        ...selectedStaffForProfile,
                                        disability_support_experience: currentExp.filter(s => s !== skill)
                                      });
                                    }
                                  }}
                                  className="rounded"
                                />
                                <Label htmlFor={`disability-${skill}`} className="text-xs">{skill}</Label>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium mb-3 block">Nursing & Manual Handling</Label>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {[
                              'Manual Handling Certified', 'Wound Care', 'Medication Administration',
                              'Vital Signs Monitoring', 'Catheter Care', 'Stoma Care',
                              'Diabetic Care', 'Epilepsy Management', 'CPR Certified'
                            ].map((skill) => (
                              <div key={skill} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`nursing-${skill}`}
                                  checked={selectedStaffForProfile.nursing_experience?.includes(skill) || false}
                                  onChange={(e) => {
                                    const currentExp = selectedStaffForProfile.nursing_experience || [];
                                    if (e.target.checked) {
                                      setSelectedStaffForProfile({
                                        ...selectedStaffForProfile,
                                        nursing_experience: [...currentExp, skill]
                                      });
                                    } else {
                                      setSelectedStaffForProfile({
                                        ...selectedStaffForProfile,
                                        nursing_experience: currentExp.filter(s => s !== skill)
                                      });
                                    }
                                  }}
                                  className="rounded"
                                />
                                <Label htmlFor={`nursing-${skill}`} className="text-xs">{skill}</Label>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <Label className="text-sm font-medium">Strengths</Label>
                            <textarea 
                              value={selectedStaffForProfile.strengths}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                strengths: e.target.value
                              })}
                              rows={3}
                              className="w-full p-2 border border-gray-300 rounded-md text-sm"
                              placeholder="List key strengths and abilities..."
                            />
                          </div>
                          <div>
                            <Label className="text-sm font-medium">Areas for Development</Label>
                            <textarea 
                              value={selectedStaffForProfile.weaknesses}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                weaknesses: e.target.value
                              })}
                              rows={3}
                              className="w-full p-2 border border-gray-300 rounded-md text-sm"
                              placeholder="Areas where additional training or support may be beneficial..."
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Access Control Section */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-slate-700 text-lg border-b pb-2">Access Control & Privileges</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <Label className="text-sm font-medium">Account Status</Label>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={selectedStaffForProfile.active}
                              onChange={(e) => setSelectedStaffForProfile({
                                ...selectedStaffForProfile,
                                active: e.target.checked
                              })}
                              className="rounded"
                            />
                            <span className="text-sm">{selectedStaffForProfile.active ? 'Active' : 'Inactive'}</span>
                          </div>
                        </div>

                        <div className="space-y-3">
                          <Label className="text-sm font-medium">Role & Permissions</Label>
                          <Select 
                            value={selectedStaffForProfile.role || 'staff'}
                            onValueChange={(value) => setSelectedStaffForProfile({
                              ...selectedStaffForProfile,
                              role: value
                            })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="staff">Staff - Basic Access</SelectItem>
                              <SelectItem value="supervisor">Supervisor - Can manage shifts</SelectItem>
                              <SelectItem value="admin">Admin - Full Access</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* View Controls */}
                      <div className="space-y-3">
                        <Label className="text-sm font-medium">View Controls</Label>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Can view other staff schedules</span>
                            <input type="checkbox" defaultChecked={false} className="rounded" />
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Can view pay information</span>
                            <input type="checkbox" defaultChecked={false} className="rounded" />
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Can request shift changes</span>
                            <input type="checkbox" defaultChecked={true} className="rounded" />
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Can view full roster</span>
                            <input type="checkbox" defaultChecked={false} className="rounded" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-between pt-4 border-t">
                    <Button variant="outline" onClick={() => setShowStaffProfileDialog(false)}>
                      Cancel
                    </Button>
                    <div className="flex space-x-2">
                      <Button variant="outline" onClick={resetStaffPin}>
                        Reset PIN
                      </Button>
                      <Button onClick={saveStaffProfile}>
                        Save Changes
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        )}

        {/* Staff Self-Profile Dialog - Comprehensive */}
        {isStaff() && (
          <Dialog open={showStaffSelfProfileDialog} onOpenChange={setShowStaffSelfProfileDialog}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <User className="w-5 h-5" />
                  <span>My Profile - {currentUser?.first_name || currentUser?.username}</span>
                </DialogTitle>
              </DialogHeader>
              {currentUser && (
                <div className="space-y-6">
                  {/* Profile Photo & Basic Info */}
                  <div className="flex items-start space-x-6 p-4 bg-slate-50 rounded-lg">
                    <div className="flex-shrink-0">
                      {currentUser.profile_photo_url ? (
                        <img 
                          src={currentUser.profile_photo_url} 
                          alt={currentUser.first_name || currentUser.username}
                          className="w-24 h-24 rounded-full object-cover border-2 border-gray-300"
                        />
                      ) : (
                        <div className="w-24 h-24 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                          {(currentUser.first_name || currentUser.username || 'U').charAt(0)}
                        </div>
                      )}
                      <div className="mt-2">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          id="self-profile-photo-upload"
                          onChange={(e) => {
                            // TODO: Handle profile photo upload
                            console.log('Self profile photo selected:', e.target.files[0]);
                          }}
                        />
                        <label htmlFor="self-profile-photo-upload" className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
                          Upload Photo
                        </label>
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-800">{currentUser.first_name || currentUser.username}</h3>
                      <p className="text-slate-600">{currentUser.role === 'staff' ? 'Staff Member' : 'User'}</p>
                      <Badge variant={currentUser.is_active ? 'default' : 'secondary'} className="mt-2">
                        {currentUser.is_active ? '✅ Active' : '❌ Inactive'}
                      </Badge>
                    </div>
                  </div>

                  {/* Basic Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="self-first-name">First Name</Label>
                      <Input
                        id="self-first-name"
                        value={currentUser.first_name || ''}
                        onChange={(e) => setCurrentUser({...currentUser, first_name: e.target.value})}
                        placeholder="Enter first name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-last-name">Last Name</Label>
                      <Input
                        id="self-last-name"
                        value={currentUser.last_name || ''}
                        onChange={(e) => setCurrentUser({...currentUser, last_name: e.target.value})}
                        placeholder="Enter last name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-dob">Date of Birth</Label>
                      <Input
                        id="self-dob"
                        type="date"
                        value={currentUser.date_of_birth || ''}
                        onChange={(e) => setCurrentUser({...currentUser, date_of_birth: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-email">Email Address</Label>
                      <Input
                        id="self-email"
                        type="email"
                        value={currentUser.email || ''}
                        onChange={(e) => setCurrentUser({...currentUser, email: e.target.value})}
                        placeholder="Enter email address"
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-phone">Best Contact Phone</Label>
                      <Input
                        id="self-phone"
                        type="tel"
                        value={currentUser.phone || ''}
                        onChange={(e) => setCurrentUser({...currentUser, phone: e.target.value})}
                        placeholder="Enter phone number"
                      />
                    </div>
                  </div>

                  {/* Address Information */}
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-slate-800">Postal Address</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <Label htmlFor="self-street-address">Street Address</Label>
                        <AddressAutocomplete
                          value={currentUser.street_address || ''}
                          onChange={(value) => setCurrentUser({...currentUser, street_address: value})}
                          placeholder="Enter street address"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-city">City</Label>
                        <Input
                          id="self-city"
                          value={currentUser.city || ''}
                          onChange={(e) => setCurrentUser({...currentUser, city: e.target.value})}
                          placeholder="Enter city"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-state">State</Label>
                        <Select value={currentUser.state || ''} onValueChange={(value) => setCurrentUser({...currentUser, state: value})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select state" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="NSW">NSW</SelectItem>
                            <SelectItem value="VIC">VIC</SelectItem>
                            <SelectItem value="QLD">QLD</SelectItem>
                            <SelectItem value="WA">WA</SelectItem>
                            <SelectItem value="SA">SA</SelectItem>
                            <SelectItem value="TAS">TAS</SelectItem>
                            <SelectItem value="ACT">ACT</SelectItem>
                            <SelectItem value="NT">NT</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="self-postcode">Postcode</Label>
                        <Input
                          id="self-postcode"
                          value={currentUser.postcode || ''}
                          onChange={(e) => setCurrentUser({...currentUser, postcode: e.target.value})}
                          placeholder="Enter postcode"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Emergency Contact */}
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-slate-800">Emergency Contact</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="self-emergency-name">Emergency Contact Name</Label>
                        <Input
                          id="self-emergency-name"
                          value={currentUser.emergency_contact_name || ''}
                          onChange={(e) => setCurrentUser({...currentUser, emergency_contact_name: e.target.value})}
                          placeholder="Enter emergency contact name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-emergency-phone">Emergency Contact Phone</Label>
                        <Input
                          id="self-emergency-phone"
                          type="tel"
                          value={currentUser.emergency_contact_phone || ''}
                          onChange={(e) => setCurrentUser({...currentUser, emergency_contact_phone: e.target.value})}
                          placeholder="Enter emergency contact phone"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-emergency-relationship">Relationship to Staff</Label>
                        <Select 
                          value={currentUser.emergency_contact_relationship || ''} 
                          onValueChange={(value) => setCurrentUser({...currentUser, emergency_contact_relationship: value})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select relationship" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Parent">Parent</SelectItem>
                            <SelectItem value="Spouse">Spouse</SelectItem>
                            <SelectItem value="Sibling">Sibling</SelectItem>
                            <SelectItem value="Child">Child</SelectItem>
                            <SelectItem value="Friend">Friend</SelectItem>
                            <SelectItem value="Other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="self-emergency-address">Emergency Contact Address</Label>
                        <Input
                          id="self-emergency-address"
                          value={currentUser.emergency_contact_address || ''}
                          onChange={(e) => setCurrentUser({...currentUser, emergency_contact_address: e.target.value})}
                          placeholder="Enter emergency contact address"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Professional Information */}
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-slate-800">Professional Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="self-ndis-number">NDIS Registration Number</Label>
                        <Input
                          id="self-ndis-number"
                          value={currentUser.ndis_registration_number || ''}
                          onChange={(e) => setCurrentUser({...currentUser, ndis_registration_number: e.target.value})}
                          placeholder="Enter NDIS registration number"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-blue-card">Blue Card Number</Label>
                        <Input
                          id="self-blue-card"
                          value={currentUser.blue_card_number || ''}
                          onChange={(e) => setCurrentUser({...currentUser, blue_card_number: e.target.value})}
                          placeholder="Enter blue card number"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-yellow-card">Yellow Card Number</Label>
                        <Input
                          id="self-yellow-card"
                          value={currentUser.yellow_card_number || ''}
                          onChange={(e) => setCurrentUser({...currentUser, yellow_card_number: e.target.value})}
                          placeholder="Enter yellow card number"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-first-aid-reg">First Aid Registration Number</Label>
                        <Input
                          id="self-first-aid-reg"
                          value={currentUser.first_aid_registration_number || ''}
                          onChange={(e) => setCurrentUser({...currentUser, first_aid_registration_number: e.target.value})}
                          placeholder="Enter first aid registration number"
                        />
                      </div>
                      <div>
                        <Label htmlFor="self-first-aid-expiry">First Aid Expiry Date</Label>
                        <Input
                          id="self-first-aid-expiry"
                          type="date"
                          value={currentUser.first_aid_expiry_date || ''}
                          onChange={(e) => setCurrentUser({...currentUser, first_aid_expiry_date: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Transport & Licensing */}
                  <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-slate-800">Transport & Licensing</h4>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="self-has-license"
                          checked={currentUser.has_drivers_license || false}
                          onCheckedChange={(checked) => setCurrentUser({...currentUser, has_drivers_license: checked})}
                        />
                        <Label htmlFor="self-has-license">Has Current Driver's License</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="self-can-drive-van"
                          checked={currentUser.can_drive_van || false}
                          onCheckedChange={(checked) => setCurrentUser({...currentUser, can_drive_van: checked})}
                        />
                        <Label htmlFor="self-can-drive-van">Can Drive Van for Client Transport</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="self-can-transport-wheelchair"
                          checked={currentUser.can_transport_power_wheelchairs || false}
                          onCheckedChange={(checked) => setCurrentUser({...currentUser, can_transport_power_wheelchairs: checked})}
                        />
                        <Label htmlFor="self-can-transport-wheelchair">Can Transport Power Wheelchairs</Label>
                      </div>
                    </div>
                  </div>

                  {/* Skills & Experience Sections */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Disability Support Experience */}
                    <div className="space-y-4">
                      <h4 className="text-lg font-semibold text-slate-800">Disability Support Experience</h4>
                      <div className="space-y-3">
                        {['personal_care', 'medication_management', 'behavioral_support', 'communication_support', 'social_support', 'meal_preparation', 'community_access', 'mobility_assistance', 'daily_living_skills'].map((skill) => (
                          <div key={skill} className="flex items-center space-x-2">
                            <Switch
                              id={`self-${skill}`}
                              checked={currentUser[skill] || false}
                              onCheckedChange={(checked) => setCurrentUser({...currentUser, [skill]: checked})}
                            />
                            <Label htmlFor={`self-${skill}`}>
                              {skill.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Nursing & Manual Handling */}
                    <div className="space-y-4">
                      <h4 className="text-lg font-semibold text-slate-800">Nursing & Manual Handling</h4>
                      <div className="space-y-3">
                        {['manual_handling_certified', 'medication_administration', 'catheter_care', 'diabetic_care', 'cpr_certified', 'wound_care', 'vital_signs_monitoring', 'stoma_care', 'epilepsy_management'].map((skill) => (
                          <div key={skill} className="flex items-center space-x-2">
                            <Switch
                              id={`self-${skill}`}
                              checked={currentUser[skill] || false}
                              onCheckedChange={(checked) => setCurrentUser({...currentUser, [skill]: checked})}
                            />
                            <Label htmlFor={`self-${skill}`}>
                              {skill.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Text Areas for Strengths, Weaknesses, Areas for Development */}
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="self-strengths">Strengths</Label>
                      <p className="text-sm text-slate-600 mb-2">List key strengths and abilities...</p>
                      <textarea
                        id="self-strengths"
                        className="w-full p-3 border rounded-md min-h-20"
                        value={currentUser.strengths || ''}
                        onChange={(e) => setCurrentUser({...currentUser, strengths: e.target.value})}
                        placeholder="Describe your key strengths and abilities..."
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-weaknesses">Weaknesses</Label>
                      <p className="text-sm text-slate-600 mb-2">List areas you feel uncomfortable with or need support...</p>
                      <textarea
                        id="self-weaknesses"
                        className="w-full p-3 border rounded-md min-h-20"
                        value={currentUser.weaknesses || ''}
                        onChange={(e) => setCurrentUser({...currentUser, weaknesses: e.target.value})}
                        placeholder="Describe areas you feel uncomfortable with or tasks you find challenging..."
                      />
                    </div>
                    <div>
                      <Label htmlFor="self-development-areas">Areas for Development</Label>
                      <p className="text-sm text-slate-600 mb-2">Areas where additional training or support may be beneficial...</p>
                      <textarea
                        id="self-development-areas"
                        className="w-full p-3 border rounded-md min-h-20"
                        value={currentUser.areas_for_development || ''}
                        onChange={(e) => setCurrentUser({...currentUser, areas_for_development: e.target.value})}
                        placeholder="Describe areas where you would like additional training or support..."
                      />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-end space-x-2 pt-4 border-t">
                    <Button variant="outline" onClick={() => setShowStaffSelfProfileDialog(false)}>
                      Cancel
                    </Button>
                    <Button onClick={async () => {
                      try {
                        const response = await axios.put(`${API_BASE_URL}/api/users/me`, currentUser, {
                          headers: { 'Authorization': `Bearer ${authToken}` }
                        });
                        console.log('Profile updated:', response.data);
                        setCurrentUser(response.data);
                        setShowStaffSelfProfileDialog(false);
                        alert('✅ Profile updated successfully!');
                      } catch (error) {
                        console.error('Error updating profile:', error);
                        alert(`❌ Error updating profile: ${error.response?.data?.detail || error.message}`);
                      }
                    }}>
                      Save Changes
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        )}

        </div>
      )}
      
      {/* Authentication Dialogs - Always available */}
      {/* Login Dialog */}
      <Dialog open={showLoginDialog && !isAuthenticated} onOpenChange={() => {}}>
        <DialogContent className="max-w-md" closable={false}>
          <DialogHeader>
            <DialogTitle className="text-center">
              🔐 Shift Roster Login
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-center text-sm text-slate-600">
              <p>Welcome to the Workforce Management System</p>
              <p>Please enter your credentials to continue</p>
            </div>

            {authError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {authError}
              </div>
            )}

            <div className="space-y-3">
              {useDropdown && availableUsers.length > 0 ? (
                <div>
                  <Label htmlFor="userSelect">Select User</Label>
                  <select
                    id="userSelect"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-900"
                    value={loginData.username}
                    onChange={(e) => {
                      console.log('Dropdown selection changed to:', e.target.value);
                      setLoginData({ ...loginData, username: e.target.value });
                    }}
                  >
                    <option value="">Choose a user...</option>
                    {availableUsers.map((user, index) => (
                      <option key={index} value={user.username}>
                        {user.displayName}
                      </option>
                    ))}
                  </select>
                  <div className="mt-1 text-xs text-slate-500">
                    Don't see your name? 
                    <button 
                      type="button"
                      className="ml-1 text-blue-600 hover:text-blue-800 underline"
                      onClick={() => {
                        console.log('Switching to manual input');
                        setUseDropdown(false);
                      }}
                    >
                      Type username manually
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter username"
                    value={loginData.username}
                    onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                  />
                  {availableUsers.length > 0 && (
                    <div className="mt-1 text-xs text-slate-500">
                      Prefer a dropdown? 
                      <button 
                        type="button"
                        className="ml-1 text-blue-600 hover:text-blue-800 underline"
                        onClick={() => {
                          console.log('Switching to dropdown, available users:', availableUsers);
                          setUseDropdown(true);
                        }}
                      >
                        Select from list
                      </button>
                    </div>
                  )}
                </div>
              )}
              <div>
                <Label htmlFor="pin">PIN (4 or 6 digits)</Label>
                <Input
                  id="pin"
                  type="password"
                  placeholder="Enter PIN"
                  value={loginData.pin}
                  onChange={(e) => setLoginData({ ...loginData, pin: e.target.value })}
                />
              </div>
            </div>

            <div className="text-xs text-slate-500 p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <p><strong>Default Login:</strong></p>
              <p>• Admin: Username "Admin", PIN "0000"</p>
              <p>• New Staff: PIN "888888" (must change on first login)</p>
            </div>

            <Button 
              onClick={login} 
              className="w-full"
              disabled={!loginData.username || !loginData.pin}
            >
              Sign In
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Change PIN Dialog */}
      <Dialog open={showChangePinDialog} onOpenChange={setShowChangePinDialog}>
        <DialogContent className="max-w-md" closable={!currentUser?.is_first_login}>
          <DialogHeader>
            <DialogTitle className="text-center">
              🔐 Change Your PIN
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-center text-sm text-slate-600">
              <p>For security, please change your default PIN</p>
              <p>Choose a secure 4 or 6 digit PIN</p>
            </div>

            {authError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {authError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <Label htmlFor="current-pin">Current PIN</Label>
                <Input
                  id="current-pin"
                  type="password"
                  placeholder="Enter current PIN"
                  value={changePinData.current_pin}
                  onChange={(e) => setChangePinData({ ...changePinData, current_pin: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="new-pin">New PIN (4 or 6 digits)</Label>
                <Input
                  id="new-pin"
                  type="password"
                  placeholder="Enter new PIN"
                  value={changePinData.new_pin}
                  onChange={(e) => setChangePinData({ ...changePinData, new_pin: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="confirm-pin">Confirm New PIN</Label>
                <Input
                  id="confirm-pin"
                  type="password"
                  placeholder="Confirm new PIN"
                  value={changePinData.confirm_pin}
                  onChange={(e) => setChangePinData({ ...changePinData, confirm_pin: e.target.value })}
                />
              </div>
            </div>

            <div className="text-xs text-slate-500 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p><strong>PIN Requirements:</strong></p>
              <p>• Must be exactly 4 or 6 digits</p>
              <p>• Numeric characters only</p>
              <p>• Choose something secure but memorable</p>
            </div>

            <div className="flex space-x-2">
              {!currentUser?.is_first_login && (
                <Button 
                  variant="outline" 
                  onClick={() => setShowChangePinDialog(false)}
                  className="flex-1"
                >
                  Skip for Now
                </Button>
              )}
              <Button 
                onClick={changePin} 
                className={currentUser?.is_first_login ? "w-full" : "flex-1"}
                disabled={!changePinData.current_pin || !changePinData.new_pin || !changePinData.confirm_pin}
              >
                Change PIN
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Shift Request Dialog */}
      <Dialog open={showShiftRequestDialog} onOpenChange={setShowShiftRequestDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Request Shift</DialogTitle>
          </DialogHeader>
          {selectedUnassignedShift && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-lg">
                <h3 className="font-medium text-slate-800 mb-2">Shift Details</h3>
                <div className="text-sm text-slate-600 space-y-1">
                  <p><strong>Date:</strong> {formatDateString(selectedUnassignedShift.date)}</p>
                  <p><strong>Time:</strong> {formatTime(selectedUnassignedShift.start_time)} - {formatTime(selectedUnassignedShift.end_time)}</p>
                  <p><strong>Hours:</strong> {selectedUnassignedShift.hours_worked?.toFixed(1)} hours</p>
                  <p><strong>Pay:</strong> {getPayDisplayText(selectedUnassignedShift)}</p>
                  <div className="flex items-center space-x-2 mt-2">
                    {getShiftTypeBadge(selectedUnassignedShift)}
                  </div>
                </div>
              </div>
              
              <div>
                <Label htmlFor="shift-request-notes">Additional Notes (Optional)</Label>
                <textarea
                  id="shift-request-notes"
                  className="w-full p-3 border rounded-md mt-1"
                  rows={3}
                  placeholder="Add any notes about your request..."
                  value={selectedUnassignedShift.requestNotes || ''}
                  onChange={(e) => setSelectedUnassignedShift({
                    ...selectedUnassignedShift,
                    requestNotes: e.target.value
                  })}
                />
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowShiftRequestDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={() => submitShiftRequest(selectedUnassignedShift.id, selectedUnassignedShift.requestNotes)}>
                  Submit Request
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Staff Availability Dialog */}
      <Dialog open={showAvailabilityDialog} onOpenChange={setShowAvailabilityDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {isStaff() ? 'Update My Availability' : 'Add Staff Availability'}
            </DialogTitle>
            {isAdmin() && (
              <p className="text-sm text-slate-600 mt-2">
                Create availability records for any staff member including Available, Unavailable, Time Off Requests, and Preferred Shifts
              </p>
            )}
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Availability Type</Label>
              <Select 
                value={newAvailability.availability_type} 
                onValueChange={(value) => setNewAvailability({...newAvailability, availability_type: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="available">✅ Available</SelectItem>
                  <SelectItem value="unavailable">❌ Unavailable</SelectItem>
                  <SelectItem value="time_off_request">🏖️ Time Off Request</SelectItem>
                  <SelectItem value="preferred_shifts">⭐ Preferred Shifts</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Staff Selection - Admin Only */}
            {isAdmin() && (
              <div>
                <Label>Select Staff Member *</Label>
                <Select 
                  value={newAvailability.staff_id} 
                  onValueChange={(value) => setNewAvailability({...newAvailability, staff_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose staff member..." />
                  </SelectTrigger>
                  <SelectContent>
                    {staff.filter(s => s.active).map((staffMember) => (
                      <SelectItem key={staffMember.id} value={staffMember.id}>
                        👤 {staffMember.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-slate-600 mt-1">
                  As an Admin, you can create availability records for any staff member
                </p>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Switch
                id="is-recurring"
                checked={newAvailability.is_recurring}
                onCheckedChange={(checked) => setNewAvailability({...newAvailability, is_recurring: checked})}
              />
              <Label htmlFor="is-recurring">Recurring (every week)</Label>
            </div>

            {newAvailability.is_recurring ? (
              <div>
                <Label>Day of Week</Label>
                <Select 
                  value={newAvailability.day_of_week?.toString() || ''} 
                  onValueChange={(value) => setNewAvailability({...newAvailability, day_of_week: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select day" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Monday</SelectItem>
                    <SelectItem value="1">Tuesday</SelectItem>
                    <SelectItem value="2">Wednesday</SelectItem>
                    <SelectItem value="3">Thursday</SelectItem>
                    <SelectItem value="4">Friday</SelectItem>
                    <SelectItem value="5">Saturday</SelectItem>
                    <SelectItem value="6">Sunday</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="date-from">From Date</Label>
                  <Input
                    id="date-from"
                    type="date"
                    value={newAvailability.date_from}
                    onChange={(e) => setNewAvailability({...newAvailability, date_from: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="date-to">To Date (leave blank for single day)</Label>
                  <Input
                    id="date-to"
                    type="date"
                    value={newAvailability.date_to}
                    onChange={(e) => setNewAvailability({...newAvailability, date_to: e.target.value})}
                  />
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start-time">Start Time (optional)</Label>
                <Input
                  id="start-time"
                  type="time"
                  value={newAvailability.start_time}
                  onChange={(e) => setNewAvailability({...newAvailability, start_time: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="end-time">End Time (optional)</Label>
                <Input
                  id="end-time"
                  type="time"
                  value={newAvailability.end_time}
                  onChange={(e) => setNewAvailability({...newAvailability, end_time: e.target.value})}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="availability-notes">Notes</Label>
              <textarea
                id="availability-notes"
                className="w-full p-3 border rounded-md mt-1"
                rows={3}
                placeholder="Add any additional notes..."
                value={newAvailability.notes}
                onChange={(e) => setNewAvailability({...newAvailability, notes: e.target.value})}
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAvailabilityDialog(false)}>
                Cancel
              </Button>
              <Button 
                onClick={() => createStaffAvailability(newAvailability)}
                disabled={
                  // For admin users, staff_id is required
                  (isAdmin() && !newAvailability.staff_id) ||
                  // Date validation for non-recurring availability
                  (!newAvailability.is_recurring && !newAvailability.date_from) ||
                  // Day validation for recurring availability
                  (newAvailability.is_recurring && newAvailability.day_of_week === null)
                }
              >
                {isAdmin() ? 'Add Staff Availability' : 'Save My Availability'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Shift Request Dialog (Admin Only) */}
      <Dialog open={showAddShiftRequestDialog} onOpenChange={setShowAddShiftRequestDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New Shift Request</DialogTitle>
            <p className="text-sm text-slate-600 mt-2">
              Create a shift request on behalf of a staff member
            </p>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Select Staff Member *</Label>
              <Select 
                value={newShiftRequest.staff_id} 
                onValueChange={(value) => {
                  const selectedStaff = staff.find(s => s.id === value);
                  setNewShiftRequest({
                    ...newShiftRequest, 
                    staff_id: value,
                    staff_name: selectedStaff?.name || ''
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose staff member..." />
                </SelectTrigger>
                <SelectContent>
                  {staff.filter(s => s.active).map((staffMember) => (
                    <SelectItem key={staffMember.id} value={staffMember.id}>
                      👤 {staffMember.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Select Shift *</Label>
              <Select 
                value={newShiftRequest.roster_entry_id} 
                onValueChange={(value) => setNewShiftRequest({...newShiftRequest, roster_entry_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose unassigned shift..." />
                </SelectTrigger>
                <SelectContent>
                  {unassignedShifts.map((shift) => (
                    <SelectItem key={shift.id} value={shift.id}>
                      📅 {formatDateString(shift.date)} • 
                      🕐 {formatTime(shift.start_time)} - {formatTime(shift.end_time)} • 
                      💰 {getPayDisplayText(shift)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="request-notes">Staff Notes</Label>
              <textarea
                id="request-notes"
                className="w-full p-3 border rounded-md mt-1"
                rows={3}
                placeholder="Notes from the staff member about this request..."
                value={newShiftRequest.notes}
                onChange={(e) => setNewShiftRequest({...newShiftRequest, notes: e.target.value})}
              />
            </div>

            <div>
              <Label htmlFor="admin-notes">Admin Notes (Optional)</Label>
              <textarea
                id="admin-notes"
                className="w-full p-3 border rounded-md mt-1"
                rows={2}
                placeholder="Admin notes about this request..."
                value={newShiftRequest.admin_notes}
                onChange={(e) => setNewShiftRequest({...newShiftRequest, admin_notes: e.target.value})}
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAddShiftRequestDialog(false)}>
                Cancel
              </Button>
              <Button 
                onClick={() => createShiftRequest(newShiftRequest)}
                disabled={!newShiftRequest.staff_id || !newShiftRequest.roster_entry_id}
              >
                Create Request
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Shift Request Dialog (Admin Only) */}
      <Dialog open={showEditShiftRequestDialog} onOpenChange={setShowEditShiftRequestDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Shift Request</DialogTitle>
            <p className="text-sm text-slate-600 mt-2">
              Modify the shift request details
            </p>
          </DialogHeader>
          {editingShiftRequest && (
            <div className="space-y-4">
              <div>
                <Label>Staff Member</Label>
                <Select 
                  value={editingShiftRequest.staff_id} 
                  onValueChange={(value) => {
                    const selectedStaff = staff.find(s => s.id === value);
                    setEditingShiftRequest({
                      ...editingShiftRequest, 
                      staff_id: value,
                      staff_name: selectedStaff?.name || ''
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {staff.filter(s => s.active).map((staffMember) => (
                      <SelectItem key={staffMember.id} value={staffMember.id}>
                        👤 {staffMember.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Shift</Label>
                <Select 
                  value={editingShiftRequest.roster_entry_id} 
                  onValueChange={(value) => setEditingShiftRequest({...editingShiftRequest, roster_entry_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {unassignedShifts.map((shift) => (
                      <SelectItem key={shift.id} value={shift.id}>
                        📅 {formatDateString(shift.date)} • 
                        🕐 {formatTime(shift.start_time)} - {formatTime(shift.end_time)} • 
                        💰 {getPayDisplayText(shift)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Status</Label>
                <Select 
                  value={editingShiftRequest.status} 
                  onValueChange={(value) => setEditingShiftRequest({...editingShiftRequest, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">⏳ Pending</SelectItem>
                    <SelectItem value="approved">✅ Approved</SelectItem>
                    <SelectItem value="rejected">❌ Rejected</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="edit-request-notes">Staff Notes</Label>
                <textarea
                  id="edit-request-notes"
                  className="w-full p-3 border rounded-md mt-1"
                  rows={3}
                  placeholder="Notes from the staff member about this request..."
                  value={editingShiftRequest.notes}
                  onChange={(e) => setEditingShiftRequest({...editingShiftRequest, notes: e.target.value})}
                />
              </div>

              <div>
                <Label htmlFor="edit-admin-notes">Admin Notes</Label>
                <textarea
                  id="edit-admin-notes"
                  className="w-full p-3 border rounded-md mt-1"
                  rows={2}
                  placeholder="Admin notes about this request..."
                  value={editingShiftRequest.admin_notes}
                  onChange={(e) => setEditingShiftRequest({...editingShiftRequest, admin_notes: e.target.value})}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowEditShiftRequestDialog(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={() => updateShiftRequest(editingShiftRequest.id, editingShiftRequest)}
                  disabled={!editingShiftRequest.staff_id || !editingShiftRequest.roster_entry_id}
                >
                  Update Request
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Staff Availability Dialog */}
      <Dialog open={showEditStaffAvailabilityDialog} onOpenChange={setShowEditStaffAvailabilityDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Staff Availability</DialogTitle>
            <p className="text-sm text-slate-600 mt-2">
              Modify the availability record details
            </p>
          </DialogHeader>
          {editingStaffAvailability && (
            <div className="space-y-4">
              {/* Staff Selection - Admin Only */}
              {isAdmin() && (
                <div>
                  <Label>Staff Member</Label>
                  <Select 
                    value={editingStaffAvailability.staff_id} 
                    onValueChange={(value) => {
                      const selectedStaff = staff.find(s => s.id === value);
                      setEditingStaffAvailability({
                        ...editingStaffAvailability, 
                        staff_id: value,
                        staff_name: selectedStaff?.name || ''
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {staff.filter(s => s.active).map((staffMember) => (
                        <SelectItem key={staffMember.id} value={staffMember.id}>
                          👤 {staffMember.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div>
                <Label>Availability Type</Label>
                <Select 
                  value={editingStaffAvailability.availability_type} 
                  onValueChange={(value) => setEditingStaffAvailability({...editingStaffAvailability, availability_type: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="available">✅ Available</SelectItem>
                    <SelectItem value="unavailable">❌ Unavailable</SelectItem>
                    <SelectItem value="time_off_request">🏖️ Time Off Request</SelectItem>
                    <SelectItem value="preferred_shifts">⭐ Preferred Shifts</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-is-recurring"
                  checked={editingStaffAvailability.is_recurring}
                  onCheckedChange={(checked) => setEditingStaffAvailability({...editingStaffAvailability, is_recurring: checked})}
                />
                <Label htmlFor="edit-is-recurring">Recurring (every week)</Label>
              </div>

              {editingStaffAvailability.is_recurring ? (
                <div>
                  <Label>Day of Week</Label>
                  <Select 
                    value={editingStaffAvailability.day_of_week?.toString() || ''} 
                    onValueChange={(value) => setEditingStaffAvailability({...editingStaffAvailability, day_of_week: parseInt(value)})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select day" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Monday</SelectItem>
                      <SelectItem value="1">Tuesday</SelectItem>
                      <SelectItem value="2">Wednesday</SelectItem>
                      <SelectItem value="3">Thursday</SelectItem>
                      <SelectItem value="4">Friday</SelectItem>
                      <SelectItem value="5">Saturday</SelectItem>
                      <SelectItem value="6">Sunday</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="edit-date-from">From Date</Label>
                    <Input
                      id="edit-date-from"
                      type="date"
                      value={editingStaffAvailability.date_from}
                      onChange={(e) => setEditingStaffAvailability({...editingStaffAvailability, date_from: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-date-to">To Date (leave blank for single day)</Label>
                    <Input
                      id="edit-date-to"
                      type="date"
                      value={editingStaffAvailability.date_to}
                      onChange={(e) => setEditingStaffAvailability({...editingStaffAvailability, date_to: e.target.value})}
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit-start-time">Start Time (optional)</Label>
                  <Input
                    id="edit-start-time"
                    type="time"
                    value={editingStaffAvailability.start_time}
                    onChange={(e) => setEditingStaffAvailability({...editingStaffAvailability, start_time: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-end-time">End Time (optional)</Label>
                  <Input
                    id="edit-end-time"
                    type="time"
                    value={editingStaffAvailability.end_time}
                    onChange={(e) => setEditingStaffAvailability({...editingStaffAvailability, end_time: e.target.value})}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="edit-availability-notes">Notes</Label>
                <textarea
                  id="edit-availability-notes"
                  className="w-full p-3 border rounded-md mt-1"
                  rows={3}
                  placeholder="Add any additional notes..."
                  value={editingStaffAvailability.notes}
                  onChange={(e) => setEditingStaffAvailability({...editingStaffAvailability, notes: e.target.value})}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowEditStaffAvailabilityDialog(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={() => updateStaffAvailability(editingStaffAvailability.id, editingStaffAvailability)}
                  disabled={
                    // Date validation for non-recurring availability
                    (!editingStaffAvailability.is_recurring && !editingStaffAvailability.date_from) ||
                    // Day validation for recurring availability
                    (editingStaffAvailability.is_recurring && editingStaffAvailability.day_of_week === null)
                  }
                >
                  Update Availability
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Comprehensive Overlap Management Dialog */}
      <Dialog open={showOverlapDialog} onOpenChange={setShowOverlapDialog}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-800 flex items-center space-x-2">
              ⚠️ <span>Overlapping Shifts Detected</span>
            </DialogTitle>
          </DialogHeader>
          {overlapData && (
            <div className="space-y-6">
              {/* Summary Information */}
              <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                <h3 className="text-lg font-semibold text-amber-800 mb-2">📊 Generation Summary</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><strong>Month:</strong> {new Date(overlapData.month + '-01').toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                    <p><strong>Type:</strong> {overlapData.type === 'shift-templates' ? 'Shift Times Templates' : 'Roster Template'}</p>
                  </div>
                  <div>
                    <p><strong>Shifts Created:</strong> {overlapData.response.entries_created || 0}</p>
                    <p><strong>Overlaps Detected:</strong> {overlapData.response.overlaps_detected || 0}</p>
                  </div>
                </div>
              </div>

              {/* Overlap Details */}
              {overlapData.response.overlap_details && overlapData.response.overlap_details.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-800">⚠️ Overlapping Shifts Details</h3>
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {overlapData.response.overlap_details.map((overlap, index) => (
                      <div key={index} className="p-3 bg-red-50 rounded-lg border border-red-200">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-red-800">
                              📅 {formatDateString(overlap.date)} • 
                              🕐 {formatTime(overlap.start_time)} - {formatTime(overlap.end_time)}
                            </p>
                            {overlap.name && (
                              <p className="text-sm text-red-600 mt-1">Shift: {overlap.name}</p>
                            )}
                            {overlap.reason && (
                              <p className="text-xs text-red-500 mt-1">Reason: {overlap.reason}</p>
                            )}
                          </div>
                          <Badge variant="destructive" className="ml-3">
                            Overlap
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                  {overlapData.response.overlaps_detected > overlapData.response.overlap_details.length && (
                    <p className="text-sm text-slate-600 text-center">
                      ... and {overlapData.response.overlaps_detected - overlapData.response.overlap_details.length} more overlapping shifts
                    </p>
                  )}
                </div>
              )}

              {/* Template Configuration Display */}
              {overlapData.response.template_config && (
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="text-md font-semibold text-blue-800 mb-2">🎯 Template Configuration</h4>
                  <div className="text-sm text-blue-700 space-y-1">
                    <p>• <strong>2:1 Support:</strong> {overlapData.response.template_config.enable_2_1_shift ? '✅ Enabled - Multiple staff can work same shift' : '❌ Disabled - Single staff per shift'}</p>
                    <p>• <strong>Overlap Override:</strong> {overlapData.response.template_config.allow_overlap_override ? '✅ Enabled - Manual conflicts allowed' : '❌ Disabled - Strict overlap detection'}</p>
                    <p>• <strong>Unassigned Duplicates:</strong> {overlapData.response.template_config.prevent_duplicate_unassigned ? '🚫 Prevented' : '✅ Allowed'}</p>
                    <p>• <strong>Assigned Duplicates:</strong> {overlapData.response.template_config.allow_different_staff_only ? '👥 Different Staff Only' : '🔓 All Duplicates Allowed'}</p>
                  </div>
                </div>
              )}

              {/* Action Explanation */}
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                <h4 className="text-md font-semibold text-slate-800 mb-2">🤔 What would you like to do?</h4>
                <div className="space-y-3 text-sm text-slate-600">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                      ✓
                    </div>
                    <div>
                      <p className="font-medium text-green-700">Publish All Shifts (Including Overlaps)</p>
                      <p>This will create <strong>ALL</strong> shifts from the template, including the {overlapData.response.overlaps_detected} overlapping ones. Useful for 2:1 support scenarios or when you want to manually manage overlaps later.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                      ⚠
                    </div>
                    <div>
                      <p className="font-medium text-orange-700">Skip Overlapping Shifts</p>
                      <p>This will publish only the <strong>{overlapData.response.entries_created}</strong> non-overlapping shifts that were successfully created. The {overlapData.response.overlaps_detected} overlapping shifts will be skipped to prevent conflicts.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowOverlapDialog(false);
                    setOverlapData(null);
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  variant="secondary"
                  onClick={handleSkipOverlapShifts}
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                >
                  ⚠️ Skip Overlaps & Publish ({overlapData.response.entries_created} shifts)
                </Button>
                <Button 
                  onClick={handlePublishAllShifts}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  ✅ Publish All Including Overlaps
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Client Profile Add/Edit Dialog */}
      <Dialog open={showClientDialog} onOpenChange={setShowClientDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-800">
              {editingClient ? '✏️ Edit Client Profile' : '👤 Add New Client Profile'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-700">📋 Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Full Name *</Label>
                  <Input
                    value={editingClient ? editingClient.full_name : newClient.full_name}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (editingClient) {
                        setEditingClient({...editingClient, full_name: value});
                      } else {
                        setNewClient({...newClient, full_name: value});
                      }
                    }}
                    placeholder="Full name"
                  />
                </div>
                <div>
                  <Label>Date of Birth *</Label>
                  <Input
                    value={editingClient ? editingClient.date_of_birth : newClient.date_of_birth}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (editingClient) {
                        setEditingClient({...editingClient, date_of_birth: value});
                      } else {
                        setNewClient({...newClient, date_of_birth: value});
                      }
                    }}
                    placeholder="DD/MM/YYYY"
                  />
                </div>
                <div>
                  <Label>Sex *</Label>
                  <Select
                    value={editingClient ? editingClient.sex : newClient.sex}
                    onValueChange={(value) => {
                      if (editingClient) {
                        setEditingClient({...editingClient, sex: value});
                      } else {
                        setNewClient({...newClient, sex: value});
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Mobile *</Label>
                  <Input
                    value={editingClient ? editingClient.mobile : newClient.mobile}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (editingClient) {
                        setEditingClient({...editingClient, mobile: value});
                      } else {
                        setNewClient({...newClient, mobile: value});
                      }
                    }}
                    placeholder="Mobile number"
                  />
                </div>
              </div>
              
              <div>
                <Label>Disability or Medical Condition *</Label>
                <Input
                  value={editingClient ? editingClient.disability_condition : newClient.disability_condition}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (editingClient) {
                      setEditingClient({...editingClient, disability_condition: value});
                    } else {
                      setNewClient({...newClient, disability_condition: value});
                    }
                  }}
                  placeholder="Primary disability or medical condition"
                />
              </div>
              
              <div>
                <Label>Address *</Label>
                <Input
                  value={editingClient ? editingClient.address : newClient.address}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (editingClient) {
                      setEditingClient({...editingClient, address: value});
                    } else {
                      setNewClient({...newClient, address: value});
                    }
                  }}
                  placeholder="Full address"
                />
              </div>
            </div>

            {/* Emergency Contacts */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-700">🚨 Emergency Contacts</h3>
              {(editingClient ? editingClient.emergency_contacts : newClient.emergency_contacts).map((contact, index) => (
                <div key={index} className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Emergency Contact {index + 1}</h4>
                    {index > 0 && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => {
                          const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                          contacts.splice(index, 1);
                          if (editingClient) {
                            setEditingClient({...editingClient, emergency_contacts: contacts});
                          } else {
                            setNewClient({...newClient, emergency_contacts: contacts});
                          }
                        }}
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={contact.name}
                        onChange={(e) => {
                          const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                          contacts[index].name = e.target.value;
                          if (editingClient) {
                            setEditingClient({...editingClient, emergency_contacts: contacts});
                          } else {
                            setNewClient({...newClient, emergency_contacts: contacts});
                          }
                        }}
                        placeholder="Contact name"
                      />
                    </div>
                    <div>
                      <Label>Relationship</Label>
                      <Input
                        value={contact.relationship}
                        onChange={(e) => {
                          const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                          contacts[index].relationship = e.target.value;
                          if (editingClient) {
                            setEditingClient({...editingClient, emergency_contacts: contacts});
                          } else {
                            setNewClient({...newClient, emergency_contacts: contacts});
                          }
                        }}
                        placeholder="e.g., Mother, Father, Sibling"
                      />
                    </div>
                    <div>
                      <Label>Mobile</Label>
                      <Input
                        value={contact.mobile}
                        onChange={(e) => {
                          const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                          contacts[index].mobile = e.target.value;
                          if (editingClient) {
                            setEditingClient({...editingClient, emergency_contacts: contacts});
                          } else {
                            setNewClient({...newClient, emergency_contacts: contacts});
                          }
                        }}
                        placeholder="Mobile number"
                      />
                    </div>
                    <div>
                      <Label>Address</Label>
                      <Input
                        value={contact.address}
                        onChange={(e) => {
                          const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                          contacts[index].address = e.target.value;
                          if (editingClient) {
                            setEditingClient({...editingClient, emergency_contacts: contacts});
                          } else {
                            setNewClient({...newClient, emergency_contacts: contacts});
                          }
                        }}
                        placeholder="Full address"
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              <Button
                variant="outline"
                onClick={() => {
                  const contacts = editingClient ? [...editingClient.emergency_contacts] : [...newClient.emergency_contacts];
                  contacts.push({ name: '', relationship: '', mobile: '', address: '' });
                  if (editingClient) {
                    setEditingClient({...editingClient, emergency_contacts: contacts});
                  } else {
                    setNewClient({...newClient, emergency_contacts: contacts});
                  }
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Emergency Contact
              </Button>
            </div>

            {/* Dialog Actions */}
            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowClientDialog(false);
                  setEditingClient(null);
                }}
              >
                Cancel
              </Button>
              <Button 
                onClick={() => {
                  const clientData = editingClient || newClient;
                  if (editingClient) {
                    updateClientProfile(editingClient.id, clientData);
                  } else {
                    createClientProfile(clientData);
                  }
                }}
              >
                {editingClient ? 'Update Client' : 'Create Client'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Client Profile View Dialog */}
      <Dialog open={showClientProfileDialog} onOpenChange={setShowClientProfileDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-800">
              👤 {selectedClient?.full_name} - Complete Profile
            </DialogTitle>
          </DialogHeader>
          {selectedClient && (
            <div className="space-y-6 pt-4">
              
              {/* Client Information Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-700">📋 Personal Information</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Full Name:</strong> {selectedClient.full_name}</div>
                    <div><strong>Date of Birth:</strong> {selectedClient.date_of_birth} {selectedClient.age && `(Age: ${selectedClient.age})`}</div>
                    <div><strong>Sex:</strong> {selectedClient.sex}</div>
                    <div><strong>Condition:</strong> {selectedClient.disability_condition}</div>
                    <div><strong>Mobile:</strong> {selectedClient.mobile}</div>
                    <div><strong>Address:</strong> {selectedClient.address}</div>
                  </div>
                </div>

                {/* Emergency Contacts */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-700">🚨 Emergency Contacts</h3>
                  {selectedClient.emergency_contacts && selectedClient.emergency_contacts.length > 0 ? (
                    <div className="space-y-3">
                      {selectedClient.emergency_contacts.map((contact, index) => (
                        <div key={index} className="p-3 bg-red-50 rounded-lg border text-sm">
                          <div className="font-semibold">{contact.name}</div>
                          <div><strong>Relationship:</strong> {contact.relationship}</div>
                          <div><strong>Mobile:</strong> {contact.mobile}</div>
                          <div><strong>Address:</strong> {contact.address}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No emergency contacts on file</p>
                  )}
                </div>
              </div>

              {/* NDIS Plan Information - Admin/Supervisor Only */}
              {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && selectedClient.current_ndis_plan && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-700">💼 NDIS Plan Details</h3>
                  
                  {/* Plan Overview */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-600">Plan Information</h4>
                      <div className="space-y-2 text-sm">
                        <div><strong>Plan Type:</strong> {selectedClient.current_ndis_plan.plan_type}</div>
                        <div><strong>NDIS Number:</strong> {selectedClient.current_ndis_plan.ndis_number}</div>
                        <div><strong>Plan Period:</strong> {selectedClient.current_ndis_plan.plan_start_date} to {selectedClient.current_ndis_plan.plan_end_date}</div>
                        <div><strong>Management:</strong> {selectedClient.current_ndis_plan.plan_management?.replace(/_/g, ' ')}</div>
                      </div>
                    </div>

                    {/* Plan Manager Details */}
                    {selectedClient.current_ndis_plan.plan_manager && (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-slate-600">Plan Manager</h4>
                        <div className="space-y-2 text-sm">
                          <div><strong>Provider:</strong> {selectedClient.current_ndis_plan.plan_manager.provider_name}</div>
                          <div><strong>Contact Person:</strong> {selectedClient.current_ndis_plan.plan_manager.contact_person}</div>
                          <div><strong>Phone:</strong> {selectedClient.current_ndis_plan.plan_manager.phone}</div>
                          <div><strong>Email:</strong> {selectedClient.current_ndis_plan.plan_manager.email}</div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Funding Categories */}
                  {selectedClient.current_ndis_plan.funding_categories && selectedClient.current_ndis_plan.funding_categories.length > 0 && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-slate-600">💰 Funding Categories</h4>
                      <div className="grid gap-4">
                        {selectedClient.current_ndis_plan.funding_categories.map((category, index) => (
                          <div key={index} className="p-4 border rounded-lg bg-blue-50">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-semibold text-blue-800">{category.category_name}</h5>
                              <Badge className="bg-blue-100 text-blue-800">
                                {category.funding_period?.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                              <div>
                                <strong>Total:</strong> ${category.total_amount?.toLocaleString() || '0'}
                              </div>
                              <div>
                                <strong>Spent:</strong> ${category.spent_amount?.toLocaleString() || '0'}
                              </div>
                              <div>
                                <strong>Remaining:</strong> ${((category.total_amount || 0) - (category.spent_amount || 0)).toLocaleString()}
                              </div>
                            </div>
                            {category.description && (
                              <div className="mt-2 text-xs text-blue-700">
                                <strong>Description:</strong> {category.description}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Client Biography Section */}
              {selectedClient.biography && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-700">📖 Client Biography</h3>
                    {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openClientBiographyDialog(selectedClient)}
                        className="text-xs"
                      >
                        ✏️ Edit BIO
                      </Button>
                    )}
                  </div>
                  
                  {/* Strengths */}
                  {selectedClient.biography.strengths && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-slate-600">💪 His Strengths</h4>
                      <p className="text-sm text-slate-700 bg-green-50 p-3 rounded-lg border">
                        {selectedClient.biography.strengths}
                      </p>
                    </div>
                  )}

                  {/* Living Arrangements */}
                  {selectedClient.biography.living_arrangements && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-slate-600">🏠 Living Arrangements, Relationships & Supports</h4>
                      <p className="text-sm text-slate-700 bg-blue-50 p-3 rounded-lg border whitespace-pre-wrap">
                        {selectedClient.biography.living_arrangements}
                      </p>
                    </div>
                  )}

                  {/* Daily Life */}
                  {selectedClient.biography.daily_life && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-slate-600">🌅 Daily Life</h4>
                      <p className="text-sm text-slate-700 bg-yellow-50 p-3 rounded-lg border whitespace-pre-wrap">
                        {selectedClient.biography.daily_life}
                      </p>
                    </div>
                  )}

                  {/* Goals */}
                  {selectedClient.biography.goals && selectedClient.biography.goals.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-600">🎯 His Goals</h4>
                      <div className="space-y-3">
                        {selectedClient.biography.goals.map((goal, index) => (
                          <div key={index} className="p-4 bg-purple-50 rounded-lg border">
                            <h5 className="font-semibold text-purple-800 mb-2">{goal.title}</h5>
                            <div className="space-y-2 text-sm">
                              <div>
                                <strong className="text-purple-700">Goal:</strong>
                                <p className="text-slate-700 mt-1">{goal.description}</p>
                              </div>
                              <div>
                                <strong className="text-purple-700">How to achieve:</strong>
                                <p className="text-slate-700 mt-1">{goal.how_to_achieve}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Support Providers - Admin/Supervisor Only */}
                  {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && selectedClient.biography.supports && selectedClient.biography.supports.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-600">🤝 Current Support Providers</h4>
                      <div className="grid gap-3">
                        {selectedClient.biography.supports.map((support, index) => (
                          <div key={index} className="p-3 bg-orange-50 rounded-lg border text-sm">
                            <div className="space-y-2">
                              <div>
                                <strong className="text-orange-700">Description:</strong>
                                <p className="text-slate-700">{support.description}</p>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                                <div>
                                  <strong>Provider:</strong> {support.provider}
                                </div>
                                <div>
                                  <strong>Frequency:</strong> {support.frequency}
                                </div>
                                <div>
                                  <strong>Type:</strong> {support.type}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Additional Information */}
                  {selectedClient.biography.additional_info && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-slate-600">ℹ️ Additional Information</h4>
                      <p className="text-sm text-slate-700 bg-gray-50 p-3 rounded-lg border whitespace-pre-wrap">
                        {selectedClient.biography.additional_info}
                      </p>
                    </div>
                  )}

                  {/* No Biography Message */}
                  {!selectedClient.biography.strengths && !selectedClient.biography.living_arrangements && 
                   !selectedClient.biography.daily_life && (!selectedClient.biography.goals || selectedClient.biography.goals.length === 0) && (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">No biography information available</p>
                      {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                        <Button
                          onClick={() => openClientBiographyDialog(selectedClient)}
                          variant="outline"
                          size="sm"
                        >
                          📝 Add Biography Information
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Dialog Actions */}
              <div className="flex justify-end space-x-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowClientProfileDialog(false)}>
                  Close
                </Button>
                {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                  <>
                    <Button 
                      variant="outline"
                      onClick={() => {
                        // Set current client for OCR update
                        setCurrentClient(selectedClient);
                        resetOCRStates();
                        setShowOCRDialog(true);
                      }}
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Upload NDIS Plan
                    </Button>
                    <Button 
                      onClick={() => {
                        setEditingClient(selectedClient);
                        setShowClientProfileDialog(false);
                        setShowClientDialog(true);
                      }}
                    >
                      Edit Profile
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* OCR Document Upload Dialog */}
      <Dialog open={showOCRDialog} onOpenChange={setShowOCRDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-slate-800">
              📄 Scan NDIS Plan Document
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {!ocrProcessing && !ocrResults && (
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Upload NDIS plan documents (PDF or images) to automatically extract client information. 
                  <br />
                  <span className="font-medium text-blue-600">✨ Multiple files supported for batch processing!</span>
                  <br />
                  <span className="text-xs text-purple-600">📱 iPhone/iPad users: PDF uploads fully supported</span>
                </p>
                
                {/* File Upload Area */}
                <div 
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
                  onDrop={handleOCRDrop}
                  onDragOver={handleOCRDragOver}
                  onClick={() => document.getElementById('ocrFileInput').click()}
                >
                  <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-lg font-medium text-gray-700 mb-2">
                    Drop your NDIS plan documents here
                  </p>
                  <p className="text-sm text-gray-500 mb-2">
                    or click to browse files
                  </p>
                  <p className="text-xs text-blue-600 font-medium mb-2">
                    📁 Select multiple files for batch processing
                  </p>
                  <p className="text-xs text-gray-400">
                    Supports: PDF, JPG, PNG, TIFF, BMP, HEIF/HEIC (max 50MB each)
                  </p>
                </div>
                
                <input
                  id="ocrFileInput"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp,.heif,.heic,application/pdf,image/*"
                  onChange={handleOCRFileSelect}
                  className="hidden"
                  multiple
                />
              </div>
            )}

            {ocrProcessing && (
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                  <span className="text-sm font-medium">
                    {selectedFile && Array.isArray(selectedFile) 
                      ? `Processing ${selectedFile.length} documents... (${processedFileCount}/${totalFileCount} complete)` 
                      : 'Processing document...'}
                  </span>
                </div>
                
                {/* Detailed Progress for Large Batches */}
                {selectedFile && Array.isArray(selectedFile) && selectedFile.length > 5 && (
                  <div className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">Batch Progress:</span>
                      <span className="text-blue-600">{processedFileCount}/{totalFileCount} files</span>
                    </div>
                    <div className="text-xs text-gray-600">
                      <p>⏱️ Large batches may take several minutes to complete</p>
                      <p>🔄 Processing files sequentially for best results</p>
                      {selectedFile.length > 20 && (
                        <p className="text-orange-600">⚠️ Very large batch - this may take 10+ minutes</p>
                      )}
                    </div>
                  </div>
                )}
                
                {/* File List for smaller batches */}
                {selectedFile && Array.isArray(selectedFile) && selectedFile.length > 1 && selectedFile.length <= 5 && (
                  <div className="text-xs text-gray-600">
                    <p className="font-medium mb-1">Files to process:</p>
                    <ul className="space-y-1 max-h-20 overflow-y-auto">
                      {selectedFile.map((file, index) => (
                        <li key={index} className="flex items-center space-x-2">
                          <span className={`w-2 h-2 rounded-full ${
                            index < processedFileCount ? 'bg-green-400' : 
                            index === processedFileCount ? 'bg-blue-400 animate-pulse' : 'bg-gray-300'
                          }`}></span>
                          <span className={`truncate ${
                            index < processedFileCount ? 'text-green-600 line-through' : 
                            index === processedFileCount ? 'text-blue-600 font-medium' : ''
                          }`}>
                            {file.name}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                    style={{ width: `${Math.max(ocrProgress, 5)}%` }}
                  >
                    {ocrProgress > 15 && (
                      <span className="text-xs text-white font-medium">
                        {ocrProgress.toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex justify-between text-xs text-gray-500">
                  <span>
                    {ocrProgress.toFixed(1)}% complete
                  </span>
                  {selectedFile && Array.isArray(selectedFile) && (
                    <span>
                      {processedFileCount}/{selectedFile.length} files processed
                    </span>
                  )}
                </div>
                
                {/* Cancel button for long operations */}
                {selectedFile && Array.isArray(selectedFile) && selectedFile.length > 10 && (
                  <div className="pt-2 border-t">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        const confirmCancel = window.confirm(
                          `⚠️ Cancel processing?\n\n${processedFileCount} of ${selectedFile.length} files have been processed.\n\nCanceling now will lose progress on remaining files.`
                        );
                        if (confirmCancel) {
                          resetOCRStates();
                          setShowOCRDialog(false);
                        }
                      }}
                      className="w-full"
                    >
                      Cancel Processing
                    </Button>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => {
                resetOCRStates();
                setShowOCRDialog(false);
              }}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* OCR Results Review Dialog */}
      <Dialog open={showOCRReviewDialog} onOpenChange={setShowOCRReviewDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-slate-800">
              ✅ Document Processed - Review Extracted Data
            </DialogTitle>
          </DialogHeader>
          {extractedClientData && (
            <div className="space-y-6">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <CheckSquare className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-800">
                    {ocrResults?.type === 'multiple' 
                      ? `${ocrResults.successfulFiles} of ${ocrResults.totalFiles} documents processed successfully!`
                      : 'Document successfully processed!'}
                  </span>
                </div>
                <p className="text-sm text-green-700">
                  Overall Confidence Score: {extractedClientData.confidence_score?.toFixed(1) || 0}%
                </p>
                
                {/* Multiple files summary */}
                {ocrResults?.type === 'multiple' && (
                  <div className="mt-3 space-y-2">
                    {ocrResults.failedFiles > 0 && (
                      <p className="text-sm text-orange-700">
                        ⚠️ {ocrResults.failedFiles} file(s) failed to process
                      </p>
                    )}
                    
                    {extractedClientData.sources && extractedClientData.sources.length > 1 && (
                      <div>
                        <p className="text-sm text-green-700 font-medium">Data sources:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {extractedClientData.sources.map((source, index) => (
                            <span key={index} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                              📄 {source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Extracted Data Preview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold text-slate-700">👤 Personal Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-start p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Full Name:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.full_name || 'Not found'}</span>
                        {extractedClientData.fieldSources?.full_name && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.full_name}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Date of Birth:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.date_of_birth || 'Not found'}</span>
                        {extractedClientData.fieldSources?.date_of_birth && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.date_of_birth}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Address:</span>
                      <div className="text-right">
                        <span className="text-sm text-right">{extractedClientData.address || 'Not found'}</span>
                        {extractedClientData.fieldSources?.address && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.address}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Mobile:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.mobile || 'Not found'}</span>
                        {extractedClientData.fieldSources?.mobile && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.mobile}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Disability:</span>
                      <div className="text-right">
                        <span className="text-sm text-right">{extractedClientData.disability_condition || 'Not found'}</span>
                        {extractedClientData.fieldSources?.disability_condition && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.disability_condition}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-slate-700">💼 NDIS Plan Details</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-start p-2 bg-blue-50 rounded">
                      <span className="text-sm font-medium">NDIS Number:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.ndis_number || 'Not found'}</span>
                        {extractedClientData.fieldSources?.ndis_number && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.ndis_number}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-blue-50 rounded">
                      <span className="text-sm font-medium">Plan Start:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.plan_start_date || 'Not found'}</span>
                        {extractedClientData.fieldSources?.plan_start_date && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.plan_start_date}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between items-start p-2 bg-blue-50 rounded">
                      <span className="text-sm font-medium">Plan End:</span>
                      <div className="text-right">
                        <span className="text-sm">{extractedClientData.plan_end_date || 'Not found'}</span>
                        {extractedClientData.fieldSources?.plan_end_date && (
                          <p className="text-xs text-gray-500 mt-1">📄 {extractedClientData.fieldSources.plan_end_date}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-2">What would you like to do with this data?</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <Button 
                      onClick={() => applyOCRToClient()}
                      className="w-full"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create New Client
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => {
                        if (currentClient) {
                          // Update existing client
                          applyOCRToClient(currentClient.id);
                        } else {
                          // Show client selection (for future enhancement)
                          alert('Please select a client to update from the client list first.');
                          setShowOCRReviewDialog(false);
                        }
                      }}
                      className="w-full"
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      {currentClient ? `Update ${currentClient.full_name}` : 'Update Existing Client'}
                    </Button>
                  </div>
                </div>

                {/* Raw text preview (collapsible) */}
                <div className="border rounded-lg">
                  <div className="p-3 bg-gray-50 border-b">
                    <h4 className="font-medium text-sm text-gray-700">📄 Processing Results</h4>
                  </div>
                  <div className="p-3">
                    {ocrResults?.type === 'multiple' ? (
                      <div className="space-y-3">
                        <div className="text-sm text-gray-600">
                          <strong>Batch Processing Summary:</strong>
                        </div>
                        <div className="grid grid-cols-1 gap-2">
                          {ocrResults.individualResults?.map((result, index) => (
                            <div key={index} className={`p-2 rounded text-xs ${
                              result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                            } border`}>
                              <div className="flex items-center justify-between">
                                <span className="font-medium">
                                  {result.success ? '✅' : '❌'} {result.filename}
                                </span>
                                {result.success && result.data?.confidence_score && (
                                  <span className="text-gray-500">
                                    {result.data.confidence_score.toFixed(1)}% confidence
                                  </span>
                                )}
                              </div>
                              {!result.success && result.error && (
                                <p className="text-red-600 mt-1">{result.error}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="max-h-32 overflow-y-auto text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded">
                        {ocrResults?.extracted_text?.slice(0, 500)}
                        {ocrResults?.extracted_text?.length > 500 && '...'}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4 border-t">
                <Button variant="outline" onClick={() => {
                  setShowOCRReviewDialog(false);
                  resetOCRStates();
                }}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Client Biography Edit Dialog */}
      <Dialog open={showClientBiographyDialog} onOpenChange={setShowClientBiographyDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-800">
              📖 Edit Biography - {editingClientBiography?.full_name}
            </DialogTitle>
          </DialogHeader>
          {editingClientBiography && (
            <div className="space-y-6 pt-4">
              
              {/* Role-based access notice */}
              {currentUser?.role === 'staff' && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>Note:</strong> Staff users can edit strengths, daily life, and additional info. 
                    Goals and supports are managed by Admin/Supervisor users.
                  </p>
                </div>
              )}

              {/* Strengths */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">💪 His Strengths</label>
                <textarea
                  className="w-full p-3 border rounded-lg resize-none"
                  rows="3"
                  placeholder="Describe the client's strengths, interests, and abilities..."
                  value={clientBiographyData.strengths}
                  onChange={(e) => setClientBiographyData(prev => ({
                    ...prev,
                    strengths: e.target.value
                  }))}
                />
              </div>

              {/* Living Arrangements - Admin/Supervisor only */}
              {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">🏠 Living Arrangements, Relationships & Supports</label>
                  <textarea
                    className="w-full p-3 border rounded-lg resize-none"
                    rows="6"
                    placeholder="Describe living situation, relationships, support network..."
                    value={clientBiographyData.living_arrangements}
                    onChange={(e) => setClientBiographyData(prev => ({
                      ...prev,
                      living_arrangements: e.target.value
                    }))}
                  />
                </div>
              )}

              {/* Daily Life */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">🌅 Daily Life</label>
                <textarea
                  className="w-full p-3 border rounded-lg resize-none"
                  rows="6"
                  placeholder="Describe typical daily activities, routines, interests..."
                  value={clientBiographyData.daily_life}
                  onChange={(e) => setClientBiographyData(prev => ({
                    ...prev,
                    daily_life: e.target.value
                  }))}
                />
              </div>

              {/* Goals - Admin/Supervisor only */}
              {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-semibold text-slate-700">🎯 His Goals</label>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={addGoalToBiography}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Goal
                    </Button>
                  </div>
                  <div className="space-y-4">
                    {clientBiographyData.goals.map((goal, index) => (
                      <div key={index} className="p-4 border rounded-lg bg-purple-50">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-medium text-purple-800">Goal {index + 1}</span>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => removeGoalFromBiography(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <label className="text-xs font-medium text-slate-600">Goal Title</label>
                            <input
                              type="text"
                              className="w-full mt-1 p-2 border rounded text-sm"
                              placeholder="Brief title for this goal..."
                              value={goal.title}
                              onChange={(e) => updateGoalInBiography(index, 'title', e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="text-xs font-medium text-slate-600">Goal Description</label>
                            <textarea
                              className="w-full mt-1 p-2 border rounded text-sm resize-none"
                              rows="2"
                              placeholder="What does the client want to achieve..."
                              value={goal.description}
                              onChange={(e) => updateGoalInBiography(index, 'description', e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="text-xs font-medium text-slate-600">How to Achieve</label>
                            <textarea
                              className="w-full mt-1 p-2 border rounded text-sm resize-none"
                              rows="2"
                              placeholder="Steps and strategies to work towards this goal..."
                              value={goal.how_to_achieve}
                              onChange={(e) => updateGoalInBiography(index, 'how_to_achieve', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                    {clientBiographyData.goals.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        <p>No goals added yet</p>
                        <p className="text-sm">Click "Add Goal" to create the client's first goal</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Support Providers - Admin/Supervisor only */}
              {(isAdmin() || (currentUser && currentUser.role === 'supervisor')) && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-semibold text-slate-700">🤝 Current Support Providers</label>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={addSupportToBiography}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Support
                    </Button>
                  </div>
                  <div className="space-y-4">
                    {clientBiographyData.supports.map((support, index) => (
                      <div key={index} className="p-4 border rounded-lg bg-orange-50">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-medium text-orange-800">Support Provider {index + 1}</span>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => removeSupportFromBiography(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <label className="text-xs font-medium text-slate-600">Description</label>
                            <textarea
                              className="w-full mt-1 p-2 border rounded text-sm resize-none"
                              rows="2"
                              placeholder="What support does this provider offer..."
                              value={support.description}
                              onChange={(e) => updateSupportInBiography(index, 'description', e.target.value)}
                            />
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div>
                              <label className="text-xs font-medium text-slate-600">Provider</label>
                              <input
                                type="text"
                                className="w-full mt-1 p-2 border rounded text-sm"
                                placeholder="Provider name & contact..."
                                value={support.provider}
                                onChange={(e) => updateSupportInBiography(index, 'provider', e.target.value)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-slate-600">Frequency</label>
                              <input
                                type="text"
                                className="w-full mt-1 p-2 border rounded text-sm"
                                placeholder="How often..."
                                value={support.frequency}
                                onChange={(e) => updateSupportInBiography(index, 'frequency', e.target.value)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-slate-600">Type</label>
                              <select
                                className="w-full mt-1 p-2 border rounded text-sm"
                                value={support.type}
                                onChange={(e) => updateSupportInBiography(index, 'type', e.target.value)}
                              >
                                <option value="">Select type...</option>
                                <option value="Mainstream">Mainstream</option>
                                <option value="NDIS">NDIS</option>
                                <option value="Informal">Informal</option>
                                <option value="Community">Community</option>
                              </select>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {clientBiographyData.supports.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        <p>No support providers added yet</p>
                        <p className="text-sm">Click "Add Support" to record support providers</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Additional Information */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">ℹ️ Additional Information</label>
                <textarea
                  className="w-full p-3 border rounded-lg resize-none"
                  rows="3"
                  placeholder="Any other relevant information about the client..."
                  value={clientBiographyData.additional_info}
                  onChange={(e) => setClientBiographyData(prev => ({
                    ...prev,
                    additional_info: e.target.value
                  }))}
                />
              </div>

              {/* Dialog Actions */}
              <div className="flex justify-end space-x-2 pt-4 border-t">
                <Button 
                  variant="outline" 
                  onClick={() => setShowClientBiographyDialog(false)}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={() => updateClientBiography(editingClientBiography.id, clientBiographyData)}
                >
                  Save Biography
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
    </div>
  );
}

export default App;