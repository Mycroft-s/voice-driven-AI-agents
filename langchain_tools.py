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
from gmail_service import GmailService

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
    user_identifier: str,
    medication_name: str,
    time_slots: List[str],
    dosage: str = "as prescribed",
    user_request: str = None
) -> str:
    """Set medication reminder. Use this tool when user mentions keywords like 'set reminder', 'medication reminder', etc.
    
    Respond naturally and helpfully when setting medication reminders. After setting a reminder, 
    automatically suggest sending a personalized email notification to help the user remember 
    their medication schedule. Use caring, conversational language.

    Parameters:
        user_identifier: User identifier (name like "hongdao1" or user ID)
        medication_name: Medication name (e.g., blood pressure medication, aspirin, insulin)
        time_slots: Medication time slots, format ["HH:MM"] (e.g., ["08:00"], ["08:00", "20:00"])
        dosage: Medication dosage, default "as prescribed" (e.g., 100mg, one tablet, two pills)
        user_request: User's original request for context (e.g., "remind me about my blood pressure medication")
    
    Time conversion rules:
    - morning/am → "08:00"
    - noon/midday → "12:00"
    - afternoon/pm → "14:00"
    - evening/night → "20:00"
    
    Email notification suggestion:
    After successfully setting medication reminder, suggest: "I've set your medication reminder. 
    Would you like me to send you a personalized email notification about this medication schedule?"
    
    Examples:
    - medication_reminder("hongdao1", "blood pressure medication", ["08:00"], user_request="remind me about my blood pressure medication")
    - medication_reminder("hongdao1", "aspirin", ["08:00", "20:00"], "100mg", user_request="set reminder for aspirin")
    """
    try:
        # Get or create user
        user_id = _data_manager.get_or_create_user(user_identifier)
        
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
        
        return f"✅ I've set up your medication reminder for {medication_name}\nDosage: {dosage}\nFrequency: {len(time_slots)} times per day\nTimes: {', '.join(time_slots)}\n\nI can also send you a personalized email reminder about this medication schedule to help you stay on track. Would you like me to send that?\n\n📧 To send medication reminder: send_email_notification(user_id={user_id}, email_type='medication_reminder', user_request='{user_request or f'remind me about {medication_name}'}')"
        
    except Exception as e:
        logger.error(f"Failed to set medication reminder: {e}")
        return f"❌ Failed to set medication reminder: {str(e)}"

class HealthRecordInput(PydanticBaseModel):
    """Health record tool input"""
    user_identifier: str = Field(description="User identifier (name like 'hongdao1' or user ID)")
    record_type: str = Field(description="Record type (e.g., blood pressure, blood sugar, symptoms)")
    content: str = Field(description="Record content")
    value: Optional[float] = Field(description="Numeric value (if any)")
    unit: Optional[str] = Field(description="Unit (if any)")

class HealthRecordTool(BaseTool):
    """Health record tool"""
    name = "health_record"
    description = """Record user's health information like blood pressure, blood sugar, symptoms, etc.
    
    Respond with empathy and concern for the user's health. If abnormal values are detected, 
    express genuine concern and offer to send helpful health reminder emails. Use natural, 
    caring language rather than clinical responses."""
    args_schema = HealthRecordInput
    data_manager: HealthDataManager = Field(exclude=True)
    
    def _run(self, user_identifier: str, record_type: str, content: str, 
             value: Optional[float] = None, unit: Optional[str] = None) -> str:
        """Execute health record"""
        try:
            # Get or create user
            user_id = self.data_manager.get_or_create_user(user_identifier)
            
            record_id = self.data_manager.add_health_record(
                user_id=user_id,
                record_type=record_type,
                content=content,
                value=value,
                unit=unit
            )
            
            result = f"✅ I've recorded your {record_type} information"
            if value and unit:
                result += f": {value} {unit}"
            else:
                result += f": {content}"
            
            # Add email suggestion for abnormal values or important records
            email_suggestion = ""
            if value:
                if record_type.lower() in ["blood pressure", "血压"] and (value > 140 or value < 90):
                    email_suggestion = f"\n\n⚠️ I'm concerned about your blood pressure reading - it's outside the normal range. I'd like to send you a helpful email with recommendations and monitoring tips. Would that be helpful?\n\n📧 To send health reminder: send_email_notification(user_id={user_id}, email_type='health_reminder', user_request='blood pressure monitoring reminder')"
                elif record_type.lower() in ["blood sugar", "血糖"] and (value > 140 or value < 70):
                    email_suggestion = f"\n\n⚠️ Your blood sugar reading needs attention. I can send you a personalized email with monitoring advice and when to contact your doctor. Would you like me to send that?\n\n📧 To send health reminder: send_email_notification(user_id={user_id}, email_type='health_reminder', user_request='blood sugar monitoring reminder')"
                elif record_type.lower() in ["weight", "体重"] and value:
                    email_suggestion = f"\n\n💡 Great job tracking your weight! I can send you a helpful email with tips for maintaining healthy progress. Would you like me to send that?\n\n📧 To send health reminder: send_email_notification(user_id={user_id}, email_type='health_reminder', user_request='weight tracking reminder')"
            
            if not email_suggestion and record_type.lower() in ["symptoms", "症状", "pain", "疼痛"]:
                email_suggestion = f"\n\n💡 I'm sorry to hear about your symptoms. I can send you a helpful email with follow-up recommendations and when to seek medical attention. Would that be useful?\n\n📧 To send health reminder: send_email_notification(user_id={user_id}, email_type='health_reminder', user_request='symptom monitoring reminder')"
            
            return result + email_suggestion
            
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
    description = """Schedule doctor appointments and health checkups for users. 
    
    When scheduling an appointment, respond naturally and empathetically. After successfully 
    scheduling, automatically suggest sending an email reminder to help the user remember 
    their important appointment. Use conversational language like "I've scheduled your 
    appointment" rather than technical responses."""
    args_schema = DoctorAppointmentInput
    data_manager: HealthDataManager = Field(exclude=True)
    api_manager: ExternalAPIManager = Field(exclude=True)
    
    def _run(self, user_id: int, doctor_name: str, department: str, 
             appointment_time: str, reason: str) -> str:
        """Execute doctor appointment"""
        try:
            # Create calendar event (sync call to async function)
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
            
            return f"✅ I've successfully scheduled your appointment with Dr. {doctor_name} from the {department} department for {appointment_time}. The appointment is for: {reason}.\n\nI can also send you an email reminder about this appointment to make sure you don't forget. Would you like me to send you a reminder email?\n\n📧 To send email reminder: send_email_notification(user_id={user_id}, email_type='appointment_reminder', user_request='appointment reminder for {department} with Dr. {doctor_name}', doctor_name='{doctor_name}', department='{department}', appointment_time='{appointment_time}', reason='{reason}')"
            
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
            # Send emergency alert (sync call to async function)
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
            # Sync call to async function
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
    description = """Query user's reminders for today
    
    IMPORTANT: When showing reminders, especially medication reminders, consider suggesting 
    email notifications to ensure users don't miss important reminders. Use send_email_notification 
    tool to send reminder emails."""
    args_schema = ReminderQueryInput
    data_manager: HealthDataManager = Field(exclude=True)
    
    def _run(self, user_id: int) -> str:
        """Execute reminder query"""
        try:
            reminders = self.data_manager.get_today_reminders(user_id)
            
            if not reminders:
                return "You have no reminders for today."
            
            result = "📋 Your reminders for today:\n"
            has_medication_reminder = False
            
            for reminder in reminders:
                result += f"- {reminder['title']}: {reminder['content']}\n"
                result += f"  Time: {reminder['scheduled_time']}\n"
                
                # Check if it's a medication reminder
                if reminder['reminder_type'] == 'medication':
                    has_medication_reminder = True
            
            # Add email suggestion for medication reminders
            if has_medication_reminder:
                result += "\n💡 SUGGESTION: I can send you email reminders for your medications to ensure you don't miss them. Would you like me to send medication reminder emails?"
            else:
                result += "\n💡 SUGGESTION: I can send you email reminders for your appointments and health tasks. Would you like me to send reminder emails?"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to query reminder information: {e}")
            return f"Failed to query reminder information: {str(e)}"

class EmailTool(BaseTool):
    """Email sending tool with dynamic content generation"""
    name = "send_email"
    description = """Send email notifications to users with dynamic content based on user's specific needs. 
    Use this tool when user requests to send emails, email reminders, or notifications. 
    Can send health reminders, medication reminders, appointment reminders, or custom emails.
    
    IMPORTANT: This tool can generate personalized email content based on:
    - User's specific request and context
    - Current medication information from database
    - User's health records and reminders
    - Personalized messaging based on user's needs
    
    The email content will be dynamically generated to match the user's exact requirements."""
    
    data_manager: HealthDataManager = Field(exclude=True)
    gmail_service: GmailService = Field(exclude=True)
    
    def __init__(self, data_manager: HealthDataManager):
        gmail_service = GmailService(sender_email="hm3424@nyu.edu")
        super().__init__(data_manager=data_manager, gmail_service=gmail_service)
    
    def _generate_dynamic_email_content(self, user_id: int, email_type: str, 
                                      user_request: str = None, **kwargs) -> tuple:
        """
        Generate dynamic email content based on user's specific request and context
        
        Args:
            user_id: User ID
            email_type: Type of email
            user_request: User's specific request/context
            **kwargs: Additional parameters
            
        Returns:
            tuple: (subject, html_content)
        """
        try:
            # Get user profile
            user_profile = self.data_manager.get_user_profile(user_id)
            user_name = user_profile.get('name', 'User')
            
            # Get user's current medications
            medications = self.data_manager.get_user_medications(user_id)
            
            # Get user's today's reminders
            reminders = self.data_manager.get_today_reminders(user_id)
            
            # Get recent health records
            recent_records = self.data_manager.get_recent_health_records(user_id, days=7)
            
            if email_type == "medication_reminder":
                return self._generate_medication_reminder_content(
                    user_name, medications, reminders, user_request, **kwargs
                )
            elif email_type == "health_reminder":
                return self._generate_health_reminder_content(
                    user_name, recent_records, user_request, **kwargs
                )
            elif email_type == "appointment_reminder":
                return self._generate_appointment_reminder_content(
                    user_name, user_request, **kwargs
                )
            elif email_type == "custom":
                return self._generate_custom_content(
                    user_name, user_request, **kwargs
                )
            else:
                # Fallback to basic content
                subject = f"Health Assistant Notification"
                content = user_request or "This is a notification from your AI Health Assistant."
                return subject, self._create_basic_html_template(user_name, content)
                
        except Exception as e:
            logger.error(f"Failed to generate dynamic email content: {e}")
            # Fallback to basic content
            subject = f"Health Assistant Notification"
            content = user_request or "This is a notification from your AI Health Assistant."
            return subject, self._create_basic_html_template("User", content)
    
    def _generate_medication_reminder_content(self, user_name: str, medications: list, 
                                           reminders: list, user_request: str = None, **kwargs) -> tuple:
        """Generate personalized medication reminder content"""
        
        # Extract specific medication info from kwargs or use all medications
        medication_name = kwargs.get('medication_name')
        dosage = kwargs.get('dosage', 'as prescribed')
        frequency = kwargs.get('frequency', 'daily')
        
        # Find specific medication if requested
        target_medication = None
        if medication_name:
            for med in medications:
                if medication_name.lower() in med['name'].lower():
                    target_medication = med
                    break
        
        # Generate subject
        if target_medication:
            subject = f"Medication Reminder - {target_medication['name']}"
        elif medications:
            subject = f"Medication Reminder - {len(medications)} medications"
        else:
            subject = "Medication Reminder"
        
        # Generate personalized content based on user request
        if user_request and "remind me about" in user_request.lower():
            # User specifically asked for medication reminder
            if target_medication:
                content_intro = f"Hi {user_name}, as requested, here's your reminder about {target_medication['name']}:"
                medication_details = f"""
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <h3 style="color: #d32f2f; margin-top: 0;">📋 Your Medication Details:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Medication:</strong> {target_medication['name']}</li>
                        <li><strong>Dosage:</strong> {target_medication['dosage']}</li>
                        <li><strong>Frequency:</strong> {target_medication['frequency']}</li>
                        <li><strong>Times:</strong> {', '.join(target_medication['time_slots'])}</li>
                    </ul>
                </div>
                """
            else:
                content_intro = f"Hi {user_name}, here are your current medication reminders:"
                medication_details = ""
                for med in medications:
                    medication_details += f"""
                    <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ff9800;">
                        <h4 style="color: #d32f2f; margin-top: 0;">💊 {med['name']}</h4>
                        <ul style="margin-bottom: 0;">
                            <li><strong>Dosage:</strong> {med['dosage']}</li>
                            <li><strong>Frequency:</strong> {med['frequency']}</li>
                            <li><strong>Times:</strong> {', '.join(med['time_slots'])}</li>
                        </ul>
                    </div>
                    """
        else:
            # General medication reminder
            content_intro = f"Hi {user_name}, here's your medication reminder:"
            medication_details = ""
            for med in medications:
                medication_details += f"""
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ff9800;">
                    <h4 style="color: #d32f2f; margin-top: 0;">💊 {med['name']}</h4>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Dosage:</strong> {med['dosage']}</li>
                        <li><strong>Frequency:</strong> {med['frequency']}</li>
                        <li><strong>Times:</strong> {', '.join(med['time_slots'])}</li>
                    </ul>
                </div>
                """
        
        # Add today's medication reminders
        today_med_reminders = [r for r in reminders if r['reminder_type'] == 'medication']
        reminder_section = ""
        if today_med_reminders:
            reminder_section = """
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #2e7d32; margin-top: 0;">⏰ Today's Medication Schedule:</h3>
                <ul style="margin-bottom: 0;">
            """
            for reminder in today_med_reminders:
                reminder_section += f"<li>{reminder['title']} at {reminder['scheduled_time']}</li>"
            reminder_section += """
                </ul>
            </div>
            """
        
        # Generate HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">
                    💊 Personalized Medication Reminder
                </h2>
                
                <p>{content_intro}</p>
                
                {medication_details}
                
                {reminder_section}
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2e7d32;"><strong>⚠️ Important Reminders:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Take your medication exactly as prescribed</li>
                        <li>Don't skip doses without consulting your doctor</li>
                        <li>Contact your healthcare provider if you experience side effects</li>
                        <li>Keep medications in a safe, dry place</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This personalized reminder was generated by your AI Health Assistant based on your specific request.</p>
                    <p>Sender: {self.gmail_service.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _generate_health_reminder_content(self, user_name: str, recent_records: list, 
                                        user_request: str = None, **kwargs) -> tuple:
        """Generate personalized health reminder content"""
        
        reminder_type = kwargs.get('reminder_type', 'Health Reminder')
        subject = f"Health Reminder - {reminder_type}"
        
        # Analyze recent health records for personalized advice
        health_summary = ""
        if recent_records:
            health_summary = "<h3 style='color: #2c5aa0;'>📊 Your Recent Health Summary:</h3><ul>"
            for record in recent_records[:3]:  # Show last 3 records
                health_summary += f"<li>{record['record_type']}: {record['content']}"
                if record.get('value') and record.get('unit'):
                    health_summary += f" ({record['value']} {record['unit']})"
                health_summary += f" - {record['created_at']}</li>"
            health_summary += "</ul>"
        
        # Generate personalized content based on user request
        if user_request:
            content_intro = f"Hi {user_name}, based on your request: '{user_request}', here's your personalized health reminder:"
        else:
            content_intro = f"Hi {user_name}, here's your health reminder:"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    🏥 Personalized Health Reminder
                </h2>
                
                <p>{content_intro}</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c5aa0; margin-top: 0;">Reminder Content:</h3>
                    <p style="margin-bottom: 0;">{kwargs.get('reminder_content', 'Please pay attention to your health condition')}</p>
                </div>
                
                {health_summary}
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin-top: 0;">💡 Health Tips:</h3>
                    <ul style="margin-bottom: 0;">
                        <li>Maintain regular exercise routine</li>
                        <li>Eat a balanced diet</li>
                        <li>Get adequate sleep (7-9 hours)</li>
                        <li>Stay hydrated throughout the day</li>
                        <li>Schedule regular health checkups</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This personalized health reminder was generated by your AI Health Assistant.</p>
                    <p>Sender: {self.gmail_service.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _generate_appointment_reminder_content(self, user_name: str, user_request: str = None, **kwargs) -> tuple:
        """Generate personalized appointment reminder content"""
        
        doctor_name = kwargs.get('doctor_name', 'Doctor')
        appointment_time = kwargs.get('appointment_time', 'Appointment Time')
        department = kwargs.get('department', 'Department')
        reason = kwargs.get('reason', 'Visit')
        
        subject = f"Appointment Reminder - {department}"
        
        # Generate personalized content based on user request
        if user_request:
            content_intro = f"Hi {user_name}, as requested, here's your appointment reminder:"
        else:
            content_intro = f"Hi {user_name}, here's your appointment reminder:"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px;">
                    🏥 Personalized Appointment Reminder
                </h2>
                
                <p>{content_intro}</p>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin-top: 0;">Appointment Details:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Department:</strong> {department}</li>
                        <li><strong>Doctor:</strong> {doctor_name}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Reason:</strong> {reason}</li>
                    </ul>
                </div>
                
                <div style="background-color: #f3e5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #7b1fa2;"><strong>📋 Important Preparation:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Please arrive 15 minutes early</li>
                        <li>Bring your ID card and insurance card</li>
                        <li>Bring a list of current medications</li>
                        <li>Prepare questions for your doctor</li>
                        <li>Contact the hospital if there are any changes</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This personalized appointment reminder was generated by your AI Health Assistant.</p>
                    <p>Sender: {self.gmail_service.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _generate_custom_content(self, user_name: str, user_request: str = None, **kwargs) -> tuple:
        """Generate custom email content based on user request"""
        
        subject = kwargs.get('subject', 'AI Health Assistant Notification')
        content = kwargs.get('content', user_request or 'This is a notification from your AI Health Assistant.')
        
        # Generate personalized content based on user request
        if user_request:
            content_intro = f"Hi {user_name}, as requested: '{user_request}', here's your personalized message:"
        else:
            content_intro = f"Hi {user_name}, here's your personalized message:"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    📧 Personalized Message
                </h2>
                
                <p>{content_intro}</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin-bottom: 0;">{content}</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This personalized message was generated by your AI Health Assistant based on your specific request.</p>
                    <p>Sender: {self.gmail_service.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _create_basic_html_template(self, user_name: str, content: str) -> str:
        """Create basic HTML template for fallback"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    AI Health Assistant Notification
                </h2>
                
                <p>Dear {user_name},</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin-bottom: 0;">{content}</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This email is automatically sent by AI Health Assistant, please do not reply.</p>
                    <p>Sender: {self.gmail_service.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _run(self, user_id: int, email_type: str, subject: str = None, 
             content: str = None, user_request: str = None, **kwargs) -> str:
        """Send email with dynamic content generation"""
        try:
            # Get user information
            user_profile = self.data_manager.get_user_profile(user_id)
            if not user_profile:
                return f"User {user_id} not found"
            
            user_email = user_profile.get('email')
            if not user_email:
                return f"User {user_profile['name']} does not have an email address configured"
            
            user_name = user_profile['name']
            
            # Authenticate Gmail service
            if not self.gmail_service.authenticate():
                return f"Failed to authenticate Gmail service for user {user_name}"
            
            # Generate dynamic email content based on user's specific request and context
            dynamic_subject, dynamic_html_content = self._generate_dynamic_email_content(
                user_id=user_id,
                email_type=email_type,
                user_request=user_request,
                subject=subject,
                content=content,
                **kwargs
            )
            
            # Send the dynamically generated email
            success = self.gmail_service.send_email(
                to_email=user_email,
                subject=dynamic_subject,
                body=dynamic_html_content,
                is_html=True
            )
            
            if success:
                return f"✅ Personalized email sent successfully to {user_email}\n📧 Subject: {dynamic_subject}\n💡 Content generated based on your specific request: '{user_request or 'general reminder'}'"
            else:
                return f"❌ Failed to send email to {user_email}"
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return f"❌ Failed to send email: {str(e)}"

@tool
def send_email_notification(
    user_identifier: str,
    email_type: str,
    subject: str = None,
    content: str = None,
    user_request: str = None,
    **kwargs
) -> str:
    """Send personalized email notification to user with dynamic content generation. 
    Use this tool when user requests to send emails or notifications.
    
    IMPORTANT: This tool generates personalized email content based on:
    - User's specific request and context (user_request parameter)
    - Current medication information from database
    - User's health records and reminders
    - Personalized messaging based on user's exact needs
    
    Parameters:
        user_identifier: User identifier (name like "hongdao1" or user ID)
        email_type: Type of email - "health_reminder", "medication_reminder", "appointment_reminder", or "custom"
        subject: Email subject (optional, will be auto-generated if not provided)
        content: Email content (optional, will be personalized based on user_request)
        user_request: User's specific request/context (e.g., "remind me about my blood pressure medication")
        **kwargs: Additional parameters based on email type
    
    Examples:
        - send_email_notification("hongdao1", "medication_reminder", user_request="remind me about my blood pressure medication")
        - send_email_notification("hongdao1", "health_reminder", user_request="send me a reminder to check my blood sugar")
        - send_email_notification("hongdao1", "appointment_reminder", user_request="remind me about my cardiology appointment tomorrow")
        - send_email_notification("hongdao1", "custom", user_request="send me a summary of my health status")
    """
    if not _data_manager:
        return "Data manager not initialized"
    
    try:
        # Get or create user
        user_id = _data_manager.get_or_create_user(user_identifier)
        
        # Get user information
        user_profile = _data_manager.get_user_profile(user_id)
        if not user_profile:
            return f"User {user_identifier} not found"
        
        user_email = user_profile.get('email')
        if not user_email:
            return f"User {user_profile['name']} does not have an email address configured"
        
        user_name = user_profile['name']
        
        # Create Gmail service instance, using hm3424@nyu.edu as sender
        gmail_service = GmailService(sender_email="hm3424@nyu.edu")
        
        # Authenticate Gmail service
        if not gmail_service.authenticate():
            return f"Failed to authenticate Gmail service for user {user_name}"
        
        # Create EmailTool instance to use dynamic content generation
        email_tool = EmailTool(data_manager=_data_manager)
        
        # Generate dynamic email content based on user's specific request and context
        dynamic_subject, dynamic_html_content = email_tool._generate_dynamic_email_content(
            user_id=user_id,
            email_type=email_type,
            user_request=user_request,
            subject=subject,
            content=content,
            **kwargs
        )
        
        # Send the dynamically generated email
        success = gmail_service.send_email(
            to_email=user_email,
            subject=dynamic_subject,
            body=dynamic_html_content,
            is_html=True
        )
        
        if success:
            return f"✅ Personalized email sent successfully to {user_email}\n📧 Subject: {dynamic_subject}\n💡 Content generated based on your specific request: '{user_request or 'general reminder'}'"
        else:
            return f"❌ Failed to send email to {user_email}"
            
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return f"❌ Failed to send email: {str(e)}"

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
        ReminderQueryTool(data_manager=data_manager),
        EmailTool(data_manager=data_manager),  # Add email sending tool
        send_email_notification  # Add email notification tool
    ]
    
    logger.info(f"Created {len(tools)} health assistant tools")
    return tools
