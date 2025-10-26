"""
Intelligent Health Assistant AI Agent - Core Configuration Module
Technology Selection Notes:
1. OpenAI GPT-4: Powerful dialogue understanding and generation capabilities, supports Chinese
2. SpeechRecognition + PyAudio: Reliable speech-to-text conversion
3. pyttsx3: Cross-platform text-to-speech, supports Chinese
4. FastAPI: Modern asynchronous web framework, supports WebSocket real-time communication
5. SQLite: Lightweight database, suitable for personal health data storage
"""

import os
from typing import Dict, Any, Optional, Union
from pydantic_settings import BaseSettings
import logging

class Config(BaseSettings):
    """Application configuration class"""
    
    # API key configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Voice configuration
    voice_language: str = "zh-CN"
    voice_rate: int = 150
    voice_volume: float = 0.8
    
    # Database configuration
    database_url: str = "sqlite:///health_assistant.db"
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_cache_enabled: bool = False  # 默认禁用，系统会自动降级到SQLite。启用后Redis不可用时也会自动降级
    
    # External API configuration
    weather_api_key: str = ""
    calendar_api_key: str = ""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = Config()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Technology selection notes
TECH_STACK_INFO = {
    "foundational_model": {
        "choice": "OpenAI GPT-4",
        "reason": "Powerful Chinese dialogue understanding capabilities, supports complex health scenario reasoning"
    },
    "speech_to_text": {
        "choice": "SpeechRecognition + Google Speech API",
        "reason": "High accuracy Chinese recognition, supports real-time speech processing"
    },
    "text_to_speech": {
        "choice": "pyttsx3",
        "reason": "Cross-platform support, configurable Chinese voice parameters"
    },
    "orchestration": {
        "choice": "FastAPI + WebSocket + SQLite",
        "reason": "Asynchronous processing, real-time communication, lightweight data storage"
    },
    "integration_points": [
        "OpenAI API - Dialogue understanding",
        "Google Speech API - Speech recognition", 
        "Weather API - Health advice",
        "Calendar API - Appointment management",
        "SQLite - Health data storage"
    ]
}

