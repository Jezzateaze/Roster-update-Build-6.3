import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar } from './components/ui/calendar';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Switch } from './components/ui/switch';
import { Separator } from './components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Users, Calendar as CalendarIcon, Settings, DollarSign, Clock, Download, Plus, Edit, Trash2, Check, CheckSquare } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Helper function for timezone-safe date formatting
const formatDateString = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

function App() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [staff, setStaff] = useState([]);
  const [shiftTemplates, setShiftTemplates] = useState([]);
  const [rosterEntries, setRosterEntries] = useState([]);
  const [settings, setSettings] = useState({
    pay_mode: 'default',
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
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showBreakWarning, setShowBreakWarning] = useState(false);
  const [breakWarningData, setBreakWarningData] = useState(null);
  const [showAddShiftDialog, setShowAddShiftDialog] = useState(false);
  const [rosterTemplates, setRosterTemplates] = useState([]);
  const [showRosterTemplateDialog, setShowRosterTemplateDialog] = useState(false);
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
  const [viewMode, setViewMode] = useState('monthly'); // 'daily', 'weekly', 'monthly'
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
  
  // Touch/swipe handling for mobile
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  const [swipingShiftId, setSwipingShiftId] = useState(null);
  
  // Bulk selection functionality
  const [selectedShifts, setSelectedShifts] = useState(new Set());
  const [bulkSelectionMode, setBulkSelectionMode] = useState(false);
  const [showBulkActionsDialog, setShowBulkActionsDialog] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (currentDate) {
      fetchRosterData();
    }
  }, [currentDate]);

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
      
      fetchRosterData();
      
      let message = `Generated roster for ${currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}`;
      if (response.data.entries_created) {
        message += `\n${response.data.entries_created} shifts created`;
      }
      if (response.data.overlaps_detected) {
        message += `\n${response.data.overlaps_detected} overlapping shifts were skipped`;
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
      
      setShowGenerateFromTemplateDialog(false);
      setSelectedRosterTemplate(null);
      fetchRosterData();
      
      let message = response.data.message;
      if (response.data.overlaps_detected) {
        message += `\n\nNote: ${response.data.overlaps_detected} overlapping shifts were skipped to prevent conflicts.`;
      }
      alert(message);
    } catch (error) {
      console.error('Error generating roster from template:', error);
      alert(`Error generating roster: ${error.response?.data?.detail || error.message}`);
    }
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
    
    const newName = prompt('Enter new template name:', template.name);
    if (!newName || newName.trim() === '') return;
    
    const newDescription = prompt('Enter new description (optional):', template.description || '');
    
    try {
      const updatedTemplate = {
        ...template,
        name: newName.trim(),
        description: newDescription?.trim() || template.description
      };
      
      await axios.put(`${API_BASE_URL}/api/roster-templates/${templateId}`, updatedTemplate);
      fetchInitialData(); // Reload templates
      alert('Template updated successfully');
    } catch (error) {
      console.error('Error updating roster template:', error);
      alert(`Error updating template: ${error.response?.data?.detail || error.message}`);
    }
  };

  const openDayTemplateDialog = (date, action) => {
    setSelectedDateForTemplate(date);
    setDayTemplateAction(action);
    setShowDayTemplateDialog(true);
    
    if (action === 'save') {
      // Suggest template name based on date
      const dayName = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][date.getDay()];
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
    if (!newStaffName.trim()) return;
    
    try {
      const newStaff = {
        name: newStaffName,
        active: true
      };
      await axios.post(`${API_BASE_URL}/api/staff`, newStaff);
      setNewStaffName('');
      setShowStaffDialog(false);
      fetchInitialData();
    } catch (error) {
      console.error('Error adding staff:', error);
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

  // Helper function to get alphabetically sorted active staff
  const getSortedActiveStaff = () => {
    return staff
      .filter(member => member.is_active)
      .sort((a, b) => a.name.localeCompare(b.name));
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
    const endHour = parseInt(entry.end_time.split(':')[0]);
    
    // Simple logic for weekdays
    if (startHour < 6 || (endHour <= startHour && endHour > 0)) { // Night or overnight
      return <Badge variant="secondary" className="bg-purple-100 text-purple-800">Night</Badge>;
    } else if (startHour >= 20) { // Evening start
      return <Badge variant="secondary" className="bg-orange-100 text-orange-800">Evening</Badge>;
    } else { // Day
      return <Badge variant="secondary" className="bg-green-100 text-green-800">Day</Badge>;
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(amount);
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
      if (entry.staff_name) {
        if (!staffTotals[entry.staff_name]) {
          staffTotals[entry.staff_name] = { hours: 0, pay: 0 };
        }
        staffTotals[entry.staff_name].hours += entry.hours_worked;
        staffTotals[entry.staff_name].pay += entry.total_pay;
        totalHours += entry.hours_worked;
        totalPay += entry.total_pay;
      }
    });

    return { staffTotals, totalHours, totalPay };
  };

  const renderCalendarDay = (date) => {
    const dayEntries = getDayEntries(date);
    const dayEvents = getDayEvents(date);
    const dayTotal = dayEntries.reduce((sum, entry) => sum + entry.total_pay, 0);
    
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
    
    return (
      <div className={`min-h-[200px] p-2 border-r border-b border-slate-200 ${backgroundClass} group hover:bg-slate-50 transition-colors relative`}>
        <div className={`font-medium text-sm mb-3 flex items-center justify-between ${textClass}`}>
          <span>{date.getDate()}</span>
          <div className="flex items-center space-x-1">
            {!isCurrentMonth && (
              <span className="text-xs text-slate-400">
                {isPreviousMonth ? 'Prev' : 'Next'}
              </span>
            )}
            {/* Day Template Buttons - Only show for current month */}
            {isCurrentMonth && (
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <button
                  className="w-4 h-4 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors flex items-center justify-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    openDayTemplateDialog(date, 'save');
                  }}
                  title={`Save ${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][date.getDay()]} as template`}
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
                  title={`Load template to ${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][date.getDay()]}`}
                  style={{ fontSize: '8px' }}
                >
                  L
                </button>
              </div>
            )}
          </div>
        </div>
        
        <div className="space-y-1">
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
                      {event.start_time}{event.end_time && ` - ${event.end_time}`}
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
          
          {/* Shift Entries */}
          {dayEntries.map(entry => (
            <div
              key={entry.id}
              className="text-xs p-2 rounded cursor-pointer hover:bg-slate-200 transition-colors group/shift relative border border-slate-100"
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
                  if (bulkSelectionMode) {
                    toggleShiftSelection(entry.id);
                  } else {
                    setSelectedShift(entry);
                    setShowShiftDialog(true);
                  }
                }}
              >
                <div className="font-medium flex items-center justify-between">
                  <span className={`${isCurrentMonth ? '' : 'opacity-75'} font-semibold`}>
                    {entry.start_time}-{entry.end_time}
                  </span>
                  {!bulkSelectionMode && (
                    <Edit className="w-3 h-3 opacity-0 group-hover/shift:opacity-100 transition-opacity" />
                  )}
                </div>
                <div className={`text-slate-600 mt-1 ${isCurrentMonth ? '' : 'opacity-75'}`}>
                  {entry.staff_name || 'Unassigned'}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <div className={isCurrentMonth ? '' : 'opacity-75'}>
                    {getShiftTypeBadge(entry)}
                  </div>
                  <span className={`font-medium text-emerald-600 ${isCurrentMonth ? '' : 'opacity-75'}`}>
                    {formatCurrency(entry.total_pay)}
                  </span>
                </div>
              </div>
              {!bulkSelectionMode && (
                <button
                  className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover/shift:opacity-100 flex items-center justify-center hover:bg-red-600 transition-all z-10 shadow-sm border border-white"
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    deleteShift(entry.id);
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
          <div className={`mt-3 pt-2 border-t border-slate-200 text-xs font-bold text-emerald-700 ${isCurrentMonth ? '' : 'opacity-75'}`}>
            Total: ${dayTotal.toFixed(0)}
          </div>
        )}
        
        {!isCurrentMonth && dayEntries.length === 0 && dayEvents.length === 0 && (
          <div className="text-xs text-slate-400 italic mt-2">
            {isPreviousMonth ? 'Previous month' : 'Next month'}
          </div>
        )}
      </div>
    );
  };

  const renderDailyView = () => {
    const selectedDate = selectedSingleDate || currentDate;
    const dayEntries = getDayEntries(selectedDate);
    const dayEvents = getDayEvents(selectedDate);
    const dayTotal = dayEntries.reduce((sum, entry) => sum + entry.total_pay, 0);
    
    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {/* Daily View Header */}
        <div className="bg-slate-50 p-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => {
                  const newDate = new Date(selectedDate);
                  newDate.setDate(newDate.getDate() - 1);
                  setSelectedSingleDate(newDate);
                }}
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
                onClick={() => {
                  const newDate = new Date(selectedDate);
                  newDate.setDate(newDate.getDate() + 1);
                  setSelectedSingleDate(newDate);
                }}
              >
                Next Day
              </Button>
            </div>
            <Button
              variant="outline"
              onClick={() => setSelectedSingleDate(new Date())}
            >
              Today
            </Button>
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
                              {event.start_time}{event.end_time && ` - ${event.end_time}`}
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
                        className={`flex-1 cursor-pointer ${bulkSelectionMode ? 'ml-6' : ''}`}
                        onClick={() => {
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
                              {entry.start_time} - {entry.end_time}
                            </div>
                            <div>
                              {getShiftTypeBadge(entry)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-emerald-600">
                              {formatCurrency(entry.total_pay)}
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
                      
                      {/* Delete button */}
                      {!bulkSelectionMode && (
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
                  Daily Total: {formatCurrency(dayTotal)}
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
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Monday start
    startOfWeek.setDate(diff);

    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      weekDays.push(day);
    }

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
            const dayTotal = dayEntries.reduce((sum, entry) => sum + entry.total_pay, 0);
            const isToday = date.toDateString() === new Date().toDateString();

            return (
              <div key={index} className={`min-h-[400px] p-3 ${isToday ? 'bg-blue-50' : ''}`}>
                <div className={`text-center mb-3 ${isToday ? 'font-bold text-blue-600' : 'font-medium text-slate-700'}`}>
                  <div className="text-sm">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index]}
                  </div>
                  <div className={`text-lg ${isToday ? 'bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto' : ''}`}>
                    {date.getDate()}
                  </div>
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
                        className={`${bulkSelectionMode ? 'ml-3' : ''}`}
                        onClick={() => {
                          if (bulkSelectionMode) {
                            toggleShiftSelection(entry.id);
                          } else {
                            setSelectedShift(entry);
                            setShowShiftDialog(true);
                          }
                        }}
                      >
                        <div className="font-medium">{entry.start_time}-{entry.end_time}</div>
                        <div className="text-slate-600 truncate">{entry.staff_name || 'Unassigned'}</div>
                        <div className="font-medium text-emerald-600">{formatCurrency(entry.total_pay)}</div>
                      </div>
                      {!bulkSelectionMode && (
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
                    ${dayTotal.toFixed(0)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderMonthlyCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // Start from Monday of the week containing the first day
    const startDate = new Date(firstDay);
    const firstDayOfWeek = firstDay.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const daysToSubtract = (firstDayOfWeek + 6) % 7; // Convert to Monday = 0 system
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

    return (
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="grid grid-cols-7 bg-slate-50">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
            <div key={day} className="p-3 text-center font-semibold text-slate-700 border-r border-slate-200 last:border-r-0">
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
        
        {/* Legend for different month indicators */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-center space-x-6 text-xs text-slate-600">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-white border border-slate-300 rounded"></div>
            <span>Current Month</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-slate-100 border border-slate-300 rounded"></div>
            <span>Previous Month</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-slate-50 border border-slate-300 rounded"></div>
            <span>Next Month</span>
          </div>
        </div>
      </div>
    );
  };

  const { staffTotals, totalHours, totalPay } = getWeeklyTotals();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
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
            <Button
              variant="outline"
              onClick={() => setShowSettingsDialog(true)}
            >
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="roster" className="flex items-center space-x-2">
              <CalendarIcon className="w-4 h-4" />
              <span>Roster</span>
            </TabsTrigger>
            <TabsTrigger value="shifts" className="flex items-center space-x-2">
              <Clock className="w-4 h-4" />
              <span>Shift Times</span>
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
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Label className="font-medium">View:</Label>
                    <div className="flex space-x-1">
                      <Button
                        variant={viewMode === 'daily' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('daily')}
                      >
                        Daily
                      </Button>
                      <Button
                        variant={viewMode === 'weekly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('weekly')}
                      >
                        Weekly
                      </Button>
                      <Button
                        variant={viewMode === 'monthly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setViewMode('monthly')}
                      >
                        Monthly
                      </Button>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setNewEvent({
                        ...newEvent,
                        date: currentDate.toISOString().split('T')[0]
                      });
                      setShowEventDialog(true);
                    }}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Event
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Month Navigation */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        const newDate = new Date(currentDate);
                        newDate.setMonth(newDate.getMonth() - 1);
                        setCurrentDate(newDate);
                      }}
                    >
                      Previous Month
                    </Button>
                    <h2 className="text-2xl font-bold text-slate-800">
                      {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
                    </h2>
                    <Button
                      variant="outline"
                      onClick={() => {
                        const newDate = new Date(currentDate);
                        newDate.setMonth(newDate.getMonth() + 1);
                        setCurrentDate(newDate);
                      }}
                    >
                      Next Month
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {/* First row of buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
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

                        {!bulkSelectionMode && (
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

                        {bulkSelectionMode && (
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
                          <Button 
                            variant="outline" 
                            onClick={() => setShowGenerateFromTemplateDialog(true)}
                          >
                            Load Template
                          </Button>
                          <Button variant="outline" onClick={clearMonthlyRoster}>
                            Clear Roster
                          </Button>
                          <Button onClick={generateMonthlyRoster} className="bg-blue-600 hover:bg-blue-700 text-white">
                            Generate Roster
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
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
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Calendar Display - Different Views */}
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
                      Adjust the default start and end times for each shift. These times will be used when generating new rosters.
                    </p>
                  </div>
                  {shiftTemplates.length === 0 && (
                    <Button onClick={createDefaultShiftTemplates}>
                      <Plus className="w-4 h-4 mr-2" />
                      Create Default Templates
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {shiftTemplates.length === 0 ? (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-600 mb-2">No Shift Templates Found</h3>
                    <p className="text-slate-500 mb-4">Create default shift templates to get started with roster generation.</p>
                    <Button onClick={createDefaultShiftTemplates}>
                      <Plus className="w-4 h-4 mr-2" />
                      Create Default Templates
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, dayIndex) => {
                      const dayTemplates = shiftTemplates.filter(t => t.day_of_week === dayIndex);
                      return (
                        <div key={day} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-lg">{day}</h3>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => createShiftTemplateForDay(dayIndex)}
                            >
                              <Plus className="w-3 h-3 mr-1" />
                              Add Shift
                            </Button>
                          </div>
                          {dayTemplates.length === 0 ? (
                            <div className="text-center py-4 text-slate-500">
                              No shifts configured for {day}
                            </div>
                          ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                              {dayTemplates.map((template, shiftIndex) => (
                                <Card key={template.id} className="p-4">
                                  <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                      <h4 className="font-medium">
                                        {template.name || `Shift ${shiftIndex + 1}`}
                                        {template.is_sleepover && <Badge variant="secondary" className="ml-2">Sleepover</Badge>}
                                      </h4>
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => {
                                          setSelectedTemplate(template);
                                          setShowTemplateDialog(true);
                                        }}
                                      >
                                        <Edit className="w-3 h-3 mr-1" />
                                        Edit
                                      </Button>
                                    </div>
                                    <div className="text-sm text-slate-600">
                                      {template.start_time} - {template.end_time}
                                    </div>
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

          <TabsContent value="staff" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Staff Management</span>
                  </CardTitle>
                  <Button onClick={() => setShowStaffDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Staff
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {staff.map(member => (
                    <Card key={member.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{member.name}</h3>
                          <Badge variant={member.active ? "default" : "secondary"}>
                            {member.active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
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
                    <span>Total Hours</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-800">{totalHours.toFixed(1)}</div>
                  <p className="text-slate-600">This week</p>
                </CardContent>
              </Card>

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

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Staff Count</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-800">{staff.length}</div>
                  <p className="text-slate-600">Active staff</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Weekly Staff Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Staff Member</TableHead>
                      <TableHead>Hours Worked</TableHead>
                      <TableHead>Gross Pay</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(staffTotals).map(([name, totals]) => (
                      <TableRow key={name}>
                        <TableCell className="font-medium">{name}</TableCell>
                        <TableCell>{totals.hours.toFixed(1)}</TableCell>
                        <TableCell className="font-medium text-emerald-600">
                          {formatCurrency(totals.pay)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
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
                <div className="flex space-x-4">
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export Excel
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export CSV
                  </Button>
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
                
                <div className="text-sm text-slate-600">
                  Date: {new Date(selectedShift.date).toLocaleDateString()}
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
                      {staff.map(member => (
                        <SelectItem key={member.id} value={member.id}>
                          {member.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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
                    <span className="text-emerald-600">{formatCurrency(selectedShift.total_pay)}</span>
                  </div>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowShiftDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={() => {
                    // Include all manual overrides in the update
                    const updates = {
                      staff_id: selectedShift.staff_id,
                      staff_name: selectedShift.staff_name,
                      start_time: selectedShift.start_time,
                      end_time: selectedShift.end_time,
                      manual_shift_type: selectedShift.manual_shift_type || null,
                      manual_hourly_rate: selectedShift.manual_hourly_rate || null,
                      manual_sleepover: selectedShift.manual_sleepover,
                      wake_hours: selectedShift.wake_hours || null
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
                  value={newShift.staff_id || ''}
                  onValueChange={(value) => {
                    const selectedStaff = staff.find(member => member.id === value);
                    setNewShift({
                      ...newShift, 
                      staff_id: value || null,
                      staff_name: selectedStaff?.name || null
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select staff member (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No staff assigned</SelectItem>
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

                {/* Manual Shift Type Override */}
                <div>
                  <Label htmlFor="template-manual-shift-type">Manual Shift Type Override (Optional)</Label>
                  <Select 
                    value={selectedTemplate.manual_shift_type || ''} 
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
                      manual_hourly_rate: selectedTemplate.manual_hourly_rate
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
                <Button variant="outline" onClick={() => setShowStaffDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={addStaff}>Add Staff</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Settings Dialog */}
        <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
          <DialogContent className="max-w-2xl">
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

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowSettingsDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={() => updateSettings(settings)}>
                  Save Settings
                </Button>
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

      </div>
    </div>
  );
}

export default App;