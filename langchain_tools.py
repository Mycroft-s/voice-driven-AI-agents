"""
LangChain Tools Module
Defines various tools used by the health assistant AI agent
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from langchain.tools import tool, BaseTool, StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel as PydanticBaseModel

from data_manager import HealthDataManager
from external_apis import ExternalAPIManager

logger = logging.getLogger(__name__)

# Global instances for tool function access
_data_manager = None
_api_manager = None

def set_managers(data_manager: HealthDataManager, api_manager: ExternalAPIManager):
    """Set global manager instances"""
    global _data_manager, _api_manager
    _data_manager = data_manager
    _api_manager = api_manager

@tool
def medication_reminder(
    user_id: int,
    medication_name: str,
    time_slots: List[str],
    dosage: str = "as prescribed"
) -> str:
    """Set medication reminder. Use this tool when user mentions keywords like 'set reminder', 'medication reminder', etc.

    Parameters:
        user_id: User ID, extracted from first line 'User ID: X' in input
        medication_name: Medication name (e.g., blood pressure medication, aspirin, insulin)
        time_slots: Medication time slots, format ["HH:MM"] (e.g., ["08:00"], ["08:00", "20:00"])
        dosage: Medication dosage, default "as prescribed" (e.g., 100mg, one tablet, two pills)
    
    Time conversion rules:
    - morning/am → "08:00"
    - noon/midday → "12:00"
    - afternoon/pm → "14:00"
    - evening/night → "20:00"
    
    Examples:
    - medication_reminder(1, "blood pressure medication", ["08:00"])
    - medication_reminder(1, "aspirin", ["08:00", "20:00"], "100mg")
    """
    try:
        # Add medication information
        med_id = _data_manager.add_medication(
            user_id=user_id,
            name=medication_name,
            dosage=dosage,
            frequency=f"{len(time_slots)} times per day",
            time_slots=time_slots
        )
        
        # Create reminders
        for time_slot in time_slots:
            reminder_id = _data_manager.add_reminder(
                user_id=user_id,
                reminder_type="medication",
                title=f"Medication Reminder - {medication_name}",
                content=f"Please take {medication_name} on time, dosage: {dosage}",
                scheduled_time=datetime.now().strftime("%Y-%m-%d") + f" {time_slot}"
            )
        
        return f"✅ Successfully set medication reminder for {medication_name}\nDosage: {dosage}\nFrequency: {len(time_slots)} times per day\nTime: {', '.join(time_slots)}"
        
    except Exception as e:
        logger.error(f"Failed to set medication reminder: {e}")
        return f"❌ Failed to set medication reminder: {str(e)}"

class HealthRecordInput(PydanticBaseModel):
    """Health record tool input"""
    user_id: int = Field(description="User ID")
    record_type: str = Field(description="Record type (e.g., blood pressure, blood sugar, symptoms)")
    content: str = Field(description="Record content")
    value: Optional[float] = Field(description="Numeric value (if any)")
    unit: Optional[str] = Field(description="Unit (if any)")

class HealthRecordTool(BaseTool):
    """Health record tool"""
    name = "health_record"
    description = "Record user's health information such as blood pressure, blood sugar, symptoms, etc."
    args_schema = HealthRecordInput
    data_manager: HealthDataManager = Field(exclude=True)
    
    def _run(self, user_id: int, record_type: str, content: str, 
             value: Optional[float] = None, unit: Optional[str] = None) -> str:
        """Execute health record"""
        try:
            record_id = self.data_manager.add_health_record(
                user_id=user_id,
                record_type=record_type,
                content=content,
                value=value,
                unit=unit
            )
            
            result = f"Recorded {record_type} information"
            if value and unit:
                result += f": {value} {unit}"
            else:
                result += f": {content}"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to record health information: {e}")
            return f"Failed to record health information: {str(e)}"

class DoctorAppointmentInput(PydanticBaseModel):
    """Doctor appointment tool input"""
    user_id: int = Field(description="User ID")
    doctor_name: str = Field(description="Doctor's name")
    department: str = Field(description="Department")
    appointment_time: str = Field(description="Appointment time")
    reason: str = Field(description="Reason for appointment")

class DoctorAppointmentTool(BaseTool):
    """Doctor appointment tool"""
    name = "doctor_appointment"
    description = "Help users schedule doctor appointments and arrange health checkups"
    args_schema = DoctorAppointmentInput
    data_manager: HealthDataManager = Field(exclude=True)
    api_manager: ExternalAPIManager = Field(exclude=True)
    
    def _run(self, user_id: int, doctor_name: str, department: str, 
             appointment_time: str, reason: str) -> str:
        """Execute doctor appointment"""
        try:
            # Create calendar event (同步调用异步函数)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                event = loop.run_until_complete(self.api_manager.create_calendar_event(
                    title=f"Doctor Appointment - {doctor_name}",
                    start_time=appointment_time,
                    duration_minutes=60,
                    description=f"Department: {department}, Reason: {reason}"
                ))
            finally:
                loop.close()
            
            return f"Scheduled appointment with Dr. {doctor_name} from {department}, Time: {appointment_time}, Reason: {reason}"
            
        except Exception as e:
            logger.error(f"Failed to schedule doctor appointment: {e}")
            return f"Failed to schedule doctor appointment: {str(e)}"

class EmergencyAlertInput(PydanticBaseModel):
    """Emergency alert tool input"""
    user_id: int = Field(description="User ID")
    emergency_message: str = Field(description="Emergency situation description")
    contact_number: str = Field(description="Emergency contact phone number")

class EmergencyAlertTool(BaseTool):
    """Emergency alert tool"""
    name = "emergency_alert"
    description = "Send emergency alerts in critical situations, contact family members or emergency services"
    args_schema = EmergencyAlertInput
    data_manager: HealthDataManager = Field(exclude=True)
    api_manager: ExternalAPIManager = Field(exclude=True)
    
    def _run(self, user_id: int, emergency_message: str, contact_number: str) -> str:
        """Execute emergency alert"""
        try:
            # Send emergency alert (同步调用异步函数)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                alert = loop.run_until_complete(self.api_manager.send_emergency_alert(
                    message=emergency_message,
                    contact=contact_number
                ))
            finally:
                loop.close()
            
            return f"Emergency alert sent! Contacted {contact_number}. Please stay calm and wait for assistance."
            
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return f"Failed to send emergency alert: {str(e)}"

class WeatherHealthAdviceInput(PydanticBaseModel):
    """Weather health advice tool input"""
    city: str = Field(description="City name")

class WeatherHealthAdviceTool(BaseTool):
    """Weather health advice tool"""
    name = "weather_health_advice"
    description = "Provide health advice based on weather conditions"
    args_schema = WeatherHealthAdviceInput
    api_manager: ExternalAPIManager = Field(exclude=True)
    
    def _run(self, city: str) -> str:
        """Execute weather health advice"""
        try:
            # 同步调用异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                weather_info = loop.run_until_complete(self.api_manager.get_weather_info(city))
            finally:
                loop.close()
            
            advice = f"Current weather in {city}: {weather_info['temperature']}°C, {weather_info['description']}. "
            advice += f"Health advice: {weather_info['health_advice']}"
            
            return advice
            
        except Exception as e:
            logger.error(f"Failed to get weather health advice: {e}")
            return f"Failed to get weather health advice: {str(e)}"

class MedicationQueryInput(PydanticBaseModel):
    """Medication query tool input"""
    user_id: int = Field(description="User ID")

class MedicationQueryTool(BaseTool):
    """Medication query tool"""
    name = "medication_query"
    description = "Query user's medication information and medication records"
    args_schema = MedicationQueryInput
    data_manager: HealthDataManager = Field(exclude=True)
    
    def _run(self, user_id: int) -> str:
        """Execute medication query"""
        try:
            medications = self.data_manager.get_user_medications(user_id)
            
            if not medications:
                return "You currently have no medication information set up."
            
            result = "Your medication information:\n"
            for med in medications:
                result += f"- {med['name']}: {med['dosage']}, {med['frequency']}, "
                result += f"Times: {', '.join(med['time_slots'])}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to query medication information: {e}")
            return f"Failed to query medication information: {str(e)}"

class ReminderQueryInput(PydanticBaseModel):
    """Reminder query tool input"""
    user_id: int = Field(description="User ID")

class ReminderQueryTool(BaseTool):
    """Reminder query tool"""
    name = "reminder_query"
    description = "Query user's reminders for today"
    args_schema = ReminderQueryInput
    data_manager: HealthDataManager = Field(exclude=True)
    
    def _run(self, user_id: int) -> str:
        """Execute reminder query"""
        try:
            reminders = self.data_manager.get_today_reminders(user_id)
            
            if not reminders:
                return "You have no reminders for today."
            
            result = "Your reminders for today:\n"
            for reminder in reminders:
                result += f"- {reminder['title']}: {reminder['content']}\n"
                result += f"  Time: {reminder['scheduled_time']}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to query reminder information: {e}")
            return f"Failed to query reminder information: {str(e)}"

def create_health_tools(data_manager: HealthDataManager, api_manager: ExternalAPIManager) -> List[BaseTool]:
    """Create all health assistant tools"""
    # Set global managers
    set_managers(data_manager, api_manager)
    
    tools = [
        medication_reminder,  # Function defined with @tool decorator
        HealthRecordTool(data_manager=data_manager),
        DoctorAppointmentTool(data_manager=data_manager, api_manager=api_manager),
        EmergencyAlertTool(data_manager=data_manager, api_manager=api_manager),
        WeatherHealthAdviceTool(api_manager=api_manager),
        MedicationQueryTool(data_manager=data_manager),
        ReminderQueryTool(data_manager=data_manager)
    ]
    
    logger.info(f"Created {len(tools)} health assistant tools")
    return tools
