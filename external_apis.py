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
                "description": "晴天",
                "humidity": 65,
                "health_advice": "天气晴朗，适合户外活动，注意防晒"
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
                "description": "未知",
                "humidity": 50,
                "health_advice": "请关注天气变化，注意身体健康"
            }
    
    def _generate_weather_health_advice(self, weather_data: Dict[str, Any]) -> str:
        """Generate health advice based on weather data"""
        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        description = weather_data["weather"][0]["description"]
        
        advice_parts = []
        
        # Temperature advice
        if temp < 5:
            advice_parts.append("天气寒冷，请注意保暖，特别是老年人要预防感冒")
        elif temp > 30:
            advice_parts.append("天气炎热，请多喝水，避免中暑")
        elif 15 <= temp <= 25:
            advice_parts.append("温度适宜，适合户外活动")
        
        # Humidity advice
        if humidity > 80:
            advice_parts.append("湿度较高，注意关节保养")
        elif humidity < 30:
            advice_parts.append("空气干燥，多补充水分")
        
        # Weather condition advice
        if "雨" in description:
            advice_parts.append("雨天路滑，外出请注意安全")
        elif "雾" in description:
            advice_parts.append("有雾霾，建议减少户外活动")
        elif "晴" in description:
            advice_parts.append("阳光充足，适合晒太阳补充维生素D")
        
        return "；".join(advice_parts) if advice_parts else "天气变化，请注意身体健康"
    
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
                    "title": "医生预约 - 心内科",
                    "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
                    "description": "定期检查血压和心脏健康"
                },
                {
                    "id": "event_2", 
                    "title": "服药提醒",
                    "start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "description": "降压药 - 每天一次"
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
                    "每天进行适量运动，如散步30分钟",
                    "保持充足睡眠，建议7-8小时",
                    "定期体检，关注血压、血糖等指标",
                    "保持社交活动，与家人朋友多交流"
                ])
            
            # Health condition-based advice
            if conditions:
                if "高血压" in conditions:
                    tips.extend([
                        "低盐饮食，每日盐摄入量不超过6克",
                        "定期监测血压，按时服药",
                        "避免情绪激动，保持心情平静"
                    ])
                
                if "糖尿病" in conditions:
                    tips.extend([
                        "控制饮食，少食多餐",
                        "定期监测血糖",
                        "注意足部护理，预防并发症"
                    ])
            
            # General advice
            tips.extend([
                "多喝水，保持身体水分平衡",
                "多吃蔬菜水果，保持营养均衡",
                "避免吸烟和过量饮酒"
            ])
            
            logger.info(f"Generated health advice: {len(tips)} tips")
            return tips[:5]  # Return first 5 tips
            
        except Exception as e:
            logger.error(f"Failed to get health advice: {e}")
            return ["保持健康的生活方式，定期体检"]
    
    async def test_apis(self) -> Dict[str, Any]:
        """Test all API functionality"""
        results = {}
        
        # Test weather API
        weather = await self.get_weather_info("北京")
        results["weather"] = weather
        
        # Test calendar API
        event = await self.create_calendar_event(
            "测试事件", 
            (datetime.now() + timedelta(hours=1)).isoformat()
        )
        results["calendar"] = event
        
        # Test health advice
        tips = await self.get_health_tips(75, ["高血压"])
        results["health_tips"] = tips
        
        logger.info("API functionality test completed")
        return results
