"""
External API Integration Module
Integrates weather, calendar and other external services
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ExternalAPIManager:
    """External API Manager"""
    
    # Chinese city name to English mapping
    CITY_NAME_MAP = {
        "北京": "Beijing",
        "上海": "Shanghai",
        "广州": "Guangzhou",
        "深圳": "Shenzhen",
        "杭州": "Hangzhou",
        "成都": "Chengdu",
        "重庆": "Chongqing",
        "天津": "Tianjin",
        "南京": "Nanjing",
        "武汉": "Wuhan",
        "西安": "Xi'an",
        "长沙": "Changsha",
        "沈阳": "Shenyang",
        "青岛": "Qingdao",
        "大连": "Dalian",
        "厦门": "Xiamen",
        "苏州": "Suzhou",
        "哈尔滨": "Harbin",
    }
    
    def __init__(self, weather_api_key: str = "", calendar_api_key: str = ""):
        self.weather_api_key = weather_api_key
        self.calendar_api_key = calendar_api_key
        logger.info("External API manager initialized successfully")
    
    async def get_weather_info(self, city: str = "北京") -> Dict[str, Any]:
        """
        Get weather information
        Uses OpenWeatherMap API (free version)
        """
        # Save original city name (for return)
        original_city = city
        
        # If it's a Chinese city name, convert to English
        if city in self.CITY_NAME_MAP:
            city = self.CITY_NAME_MAP[city]
            logger.info(f"City name conversion: {original_city} -> {city}")
        
        if not self.weather_api_key:
            # Mock weather data
            return {
                "city": original_city,
                "temperature": 22,
                "description": "Sunny",
                "humidity": 65,
                "health_advice": "The weather is clear and sunny, perfect for outdoor activities. Remember to apply sunscreen."
            }
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.weather_api_key,
                "units": "metric",
                "lang": "zh_cn"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_info = {
                "city": original_city,  # Use original city name
                "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "health_advice": self._generate_weather_health_advice(data)
            }
            
            logger.info(f"Weather information retrieved successfully: {original_city} ({city})")
            return weather_info
            
        except Exception as e:
            logger.error(f"Failed to get weather information: {e}")
            return {
                "city": original_city,  # Use original city name
                "temperature": 20,
                "description": "Unknown",
                "humidity": 50,
                "health_advice": "Please pay attention to weather changes and take care of your health."
            }
    
    def _generate_weather_health_advice(self, weather_data: Dict[str, Any]) -> str:
        """Generate health advice based on weather data"""
        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        description = weather_data["weather"][0]["description"]
        
        advice_parts = []
        
        # Temperature advice
        if temp < 5:
            advice_parts.append("It's very cold outside. Please keep warm, especially elderly people should prevent colds.")
        elif temp > 30:
            advice_parts.append("It's very hot outside. Please drink more water and avoid heatstroke.")
        elif 15 <= temp <= 25:
            advice_parts.append("The temperature is comfortable, perfect for outdoor activities.")
        
        # Humidity advice
        if humidity > 80:
            advice_parts.append("High humidity detected. Please take care of your joints.")
        elif humidity < 30:
            advice_parts.append("The air is dry. Please drink more water to stay hydrated.")
        
        # Weather condition advice
        if "rain" in description.lower():
            advice_parts.append("It's raining. Please be careful when going out as roads may be slippery.")
        elif "fog" in description.lower() or "haze" in description.lower():
            advice_parts.append("There's fog or haze. It's recommended to reduce outdoor activities.")
        elif "sunny" in description.lower() or "clear" in description.lower():
            advice_parts.append("Sunny weather with plenty of sunshine. Great for getting vitamin D.")
        
        return "; ".join(advice_parts) if advice_parts else "Weather changes detected. Please take care of your health."
    
    async def create_calendar_event(self, title: str, start_time: str, 
                                  duration_minutes: int = 60, description: str = "") -> Dict[str, Any]:
        """
        Create calendar event
        This uses a mock implementation, actual projects can integrate Google Calendar API
        """
        try:
            # Mock calendar event creation
            event = {
                "id": f"event_{datetime.now().timestamp()}",
                "title": title,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            logger.info(f"Created calendar event: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return {"error": str(e)}
    
    async def get_upcoming_events(self, days_ahead: int = 7) -> list:
        """Get upcoming events"""
        try:
            # Mock upcoming events
            events = [
                {
                    "id": "event_1",
                    "title": "Doctor Appointment - Cardiology",
                    "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
                    "description": "Regular blood pressure and heart health checkup"
                },
                {
                    "id": "event_2", 
                    "title": "Medication Reminder",
                    "start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "description": "Blood pressure medication - once daily"
                }
            ]
            
            logger.info(f"Retrieved upcoming events: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    async def send_emergency_alert(self, message: str, contact: str) -> Dict[str, Any]:
        """Send emergency alert"""
        try:
            # Mock emergency alert sending
            alert = {
                "id": f"alert_{datetime.now().timestamp()}",
                "message": message,
                "contact": contact,
                "sent_at": datetime.now().isoformat(),
                "status": "sent"
            }
            
            logger.warning(f"Sent emergency alert: {message} -> {contact}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return {"error": str(e)}
    
    async def get_health_tips(self, user_age: int = 65, conditions: list = None) -> list:
        """Get personalized health advice"""
        try:
            tips = []
            
            # Age-based advice
            if user_age >= 65:
                tips.extend([
                    "Engage in moderate exercise daily, such as walking for 30 minutes",
                    "Get adequate sleep, recommended 7-8 hours",
                    "Have regular health checkups, monitor blood pressure and blood sugar",
                    "Maintain social activities and communicate with family and friends"
                ])
            
            # Health condition-based advice
            if conditions:
                if "hypertension" in conditions or "high blood pressure" in conditions:
                    tips.extend([
                        "Follow a low-salt diet, limit daily salt intake to no more than 6 grams",
                        "Monitor blood pressure regularly and take medication on time",
                        "Avoid emotional stress and maintain a calm mood"
                    ])
                
                if "diabetes" in conditions:
                    tips.extend([
                        "Control your diet with small, frequent meals",
                        "Monitor blood sugar regularly",
                        "Take care of your feet to prevent complications"
                    ])
            
            # General advice
            tips.extend([
                "Drink plenty of water to maintain body fluid balance",
                "Eat more vegetables and fruits for balanced nutrition",
                "Avoid smoking and excessive alcohol consumption"
            ])
            
            logger.info(f"Generated health advice: {len(tips)} tips")
            return tips[:5]  # Return first 5 tips
            
        except Exception as e:
            logger.error(f"Failed to get health advice: {e}")
            return ["Maintain a healthy lifestyle and have regular health checkups"]
    
    async def test_apis(self) -> Dict[str, Any]:
        """Test all API functionality"""
        results = {}
        
        # Test weather API
        weather = await self.get_weather_info("Beijing")
        results["weather"] = weather
        
        # Test calendar API
        event = await self.create_calendar_event(
            "Test Event", 
            (datetime.now() + timedelta(hours=1)).isoformat()
        )
        results["calendar"] = event
        
        # Test health advice
        tips = await self.get_health_tips(75, ["hypertension"])
        results["health_tips"] = tips
        
        logger.info("API functionality test completed")
        return results
