"""
Voice Processing Module
Integrates speech-to-text and text-to-speech functionality
"""

import speech_recognition as sr
import pyttsx3
import threading
import queue
import logging
from typing import Optional, Callable
import time

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Voice Processor - handles speech-to-text and text-to-speech"""
    
    def __init__(self, language: str = "en-US", rate: int = 150, volume: float = 0.8):
        self.language = language
        self.rate = rate
        self.volume = volume
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize speech synthesis
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
        
        # Voice queue
        self.voice_queue = queue.Queue()
        self.is_speaking = False
        
        logger.info("Voice processor initialized successfully")
    
    def _configure_tts(self):
        """Configure text-to-speech parameters"""
        voices = self.tts_engine.getProperty('voices')
        
        # Try to find English voice
        for voice in voices:
            if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        self.tts_engine.setProperty('rate', self.rate)
        self.tts_engine.setProperty('volume', self.volume)
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 3) -> Optional[str]:
        """
        Listen to voice input and convert to text
        
        Args:
            timeout: Timeout in seconds
            phrase_time_limit: Phrase time limit in seconds
            
        Returns:
            Converted text or None
        """
        try:
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Please start speaking...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                logger.info("Recognizing speech...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                
                logger.info(f"Recognition result: {text}")
                return text
                
        except sr.WaitTimeoutError:
            logger.warning("Voice input timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand speech")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition exception: {e}")
            return None
    
    def speak(self, text: str, blocking: bool = False):
        """
        Convert text to speech output
        
        Args:
            text: Text to convert
            blocking: Whether to block and wait for speech to finish
        """
        if not text.strip():
            return
            
        logger.info(f"Speech output: {text}")
        
        if blocking:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            # Non-blocking mode, use queue
            self.voice_queue.put(text)
            if not self.is_speaking:
                threading.Thread(target=self._speak_worker, daemon=True).start()
    
    def _speak_worker(self):
        """Speech playback worker thread"""
        self.is_speaking = True
        
        while not self.voice_queue.empty():
            try:
                text = self.voice_queue.get_nowait()
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.voice_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Speech playback error: {e}")
        
        self.is_speaking = False
    
    def stop_speaking(self):
        """Stop current speech playback"""
        self.tts_engine.stop()
        # Clear queue
        while not self.voice_queue.empty():
            try:
                self.voice_queue.get_nowait()
            except queue.Empty:
                break
    
    def test_voice(self):
        """Test voice functionality"""
        logger.info("Testing voice functionality...")
        
        # Test speech synthesis
        self.speak("Hello, I am your health assistant", blocking=True)
        
        # Test speech recognition
        logger.info("Please say something to test...")
        result = self.listen(timeout=10)
        
        if result:
            self.speak(f"I heard you say: {result}", blocking=True)
        else:
            self.speak("Sorry, I didn't catch that", blocking=True)
        
        logger.info("Voice functionality test completed")

# Global voice processor instance
voice_processor = VoiceProcessor()

