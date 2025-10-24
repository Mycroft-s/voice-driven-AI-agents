"""
LangChain-based AI Health Assistant Core Module
Integrates LangChain tools and LangGraph workflow
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

from langchain_tools import create_health_tools
from langgraph_workflow import HealthAssistantWorkflow
from voice_processor import voice_processor
from data_manager import HealthDataManager
from external_apis import ExternalAPIManager
from config import config, logger

class LangChainHealthAssistant:
    """LangChain-based Health Assistant AI Agent"""
    
    def __init__(self, openai_api_key: str):
        # Initialize LLM (lower temperature for better tool calling accuracy)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,  # Use 0 for most deterministic output
            api_key=openai_api_key
        )
        
        # Initialize components
        self.data_manager = HealthDataManager()
        self.api_manager = ExternalAPIManager(
            weather_api_key=config.weather_api_key,
            calendar_api_key=config.calendar_api_key
        )
        
        # Create tools
        self.tools = create_health_tools(self.data_manager, self.api_manager)
        
        # Create memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create prompt template
        self.prompt = self._create_prompt_template()
        
        # Create Agent
        self.agent = self._create_agent()
        
        # Create Agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # Increase iterations
            return_intermediate_steps=False  # Don't return intermediate steps for simplicity
        )
        
        # Create LangGraph workflow (backup)
        self.workflow = HealthAssistantWorkflow(openai_api_key)
        
        # Current user ID
        self.current_user_id = 1
        
        logger.info("LangChain Health Assistant initialized successfully")
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create prompt template"""
        system_message = """
        You are a professional health assistant AI, specialized in providing health management services for elderly people.
        
        Your main responsibilities include:
        1. Help users manage medications and medication reminders
        2. Record health information and symptoms
        3. Assist with scheduling doctor appointments and health checkups
        4. Handle emergency medical situations
        5. Provide personalized health advice
        
        Please follow these principles:
        - Use a gentle and patient tone when communicating with users
        - Explain health issues in simple, understandable language
        - Encourage users to seek medical attention promptly, don't replace professional medical advice
        - Keep conversations natural and flowing
        - Proactively ask about user's health status and needs
        
        Pay special attention when users mention:
        - Physical discomfort or pain
        - Forgetting to take medication
        - Need to schedule a doctor appointment
        - Emergency medical situations
        
        You have the following tools available:
        - medication_reminder: Set medication reminders (requires: user ID, medication name, dosage, medication time)
        - health_record: Record health information (requires: user ID, record type, content)
        - doctor_appointment: Schedule doctor appointments (requires: user ID, doctor name, department, time, reason)
        - emergency_alert: Send emergency alerts (requires: user ID, emergency message, contact phone)
        - weather_health_advice: Get weather health advice (requires: city name)
        - medication_query: Query medication information (requires: user ID)
        - reminder_query: Query reminder items (requires: user ID)
        
        Important notes:
        1. Before using tools, ensure you extract all required parameters from user input
        2. Time format must be "HH:MM", for example: 8am="08:00", 2pm="14:00", 8pm="20:00"
        3. If user doesn't provide some information, use reasonable default values
        4. User ID is always on the first line "User ID: X"
        
        Parameter extraction examples:
        
        Example 1:
        User input: "I want to set a reminder for blood pressure medication, every day at 8am"
        Extract parameters:
        - user_id: 1 (extracted from first line)
        - medication_name: "blood pressure medication"
        - dosage: "as prescribed" (not provided by user, use default)
        - time_slots: ["08:00"] (8am converted to 08:00)
        
        Example 2:
        User input: "Help me set up aspirin, every day at 8am and 8pm"
        Extract parameters:
        - user_id: 1
        - medication_name: "aspirin"
        - dosage: "as prescribed"
        - time_slots: ["08:00", "20:00"] (8am and 8pm)
        
        Example 3:
        User input: "Set medication reminder: blood pressure medication, 100mg, every day at 8am"
        Extract parameters:
        - user_id: 1
        - medication_name: "blood pressure medication"
        - dosage: "100mg"
        - time_slots: ["08:00"]
        
        Please choose appropriate tools based on user needs and reply in English or Chinese depends on the question.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def _create_agent(self):
        """Create Agent"""
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        return agent
    
    async def process_user_input(self, user_input: str, user_id: int = None) -> Dict[str, Any]:
        """Process user input"""
        try:
            if user_id:
                self.current_user_id = user_id
            
            # Build input with user ID information and instructions
            enhanced_input = f"""User ID: {self.current_user_id}

            User input: {user_input}

            Processing steps:
            1. Analyze user intent, determine which tool to use
            2. Extract required parameters from user input
            3. Call tool after ensuring parameter format is correct
            4. Generate friendly response

            Time conversion reference:
            - "8am" or "morning 8" → ["08:00"]
            - "8pm" or "evening 8" → ["20:00"]
            - "8am and 8pm" → ["08:00", "20:00"]
            - "noon daily" → ["12:00"]

            If user doesn't provide dosage information, use "as prescribed" as default value.
            """
            
            # Use Agent executor to process input
            result = await self.agent_executor.ainvoke({
                "input": enhanced_input
            })
            
            return {
                "success": True,
                "response": result["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process user input: {e}")
            error_detail = str(e)
            
            # Provide more friendly error messages
            if "missing" in error_detail and "required positional arguments" in error_detail:
                friendly_message = "Sorry, I need more information to help you. Please tell me:\n1. Medication name\n2. Time to take\n3. Dosage (optional)"
            else:
                friendly_message = f"Sorry, there was an issue processing your request. Please try describing your needs in more detail."
            
            return {
                "success": False,
                "response": friendly_message,
                "timestamp": datetime.now().isoformat(),
                "error": error_detail
            }
    
    async def process_voice_input(self) -> Dict[str, Any]:
        """Process voice input"""
        try:
            # Listen to voice input with simple method to avoid hanging
            user_input = voice_processor.listen_simple(timeout=15)
            
            if not user_input:
                return {
                    "success": False,
                    "message": "No voice input detected",
                    "response": "Sorry, I didn't catch that. Please speak again."
                }
            
            logger.info(f"User voice input: {user_input}")
            
            # Process user input
            result = await self.process_user_input(user_input)
            
            # Add user input to result for frontend display
            result["user_input"] = user_input
            logger.info(f"Added user_input to result: {result.get('user_input')}")
            logger.info(f"Complete result before return: {result}")
            
            # Voice output response (disabled - handled by frontend)
            # if result["response"]:
            #     voice_processor.speak(result["response"], blocking=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            error_message = "Sorry, there was an issue processing your request. Please try again later."
            # voice_processor.speak(error_message, blocking=True)  # Disabled - handled by frontend
            
            return {
                "success": False,
                "message": str(e),
                "response": error_message
            }
    
    async def start_conversation(self) -> str:
        """Start conversation"""
        welcome_message = "Hello! I am your intelligent health assistant, built with LangChain technology. I can help you manage health matters including medication reminders, health records, doctor appointments, and more. How can I assist you today?"
        
        # Don't play voice on server side, let frontend handle it
        # voice_processor.speak(welcome_message, blocking=True)
        
        return welcome_message
    
    async def setup_user_profile(self, name: str, age: int, 
                               health_conditions: List[str] = None,
                               emergency_contact: str = None) -> int:
        """Set up user profile - only creates if doesn't exist"""
        try:
            # 检查是否已存在相同名称的用户
            existing_user = self.data_manager.get_user_by_name(name)
            if existing_user:
                self.current_user_id = existing_user['id']
                logger.info(f"Found existing user: {name}, ID: {existing_user['id']}")
                return existing_user['id']
            
            # 如果不存在，创建新用户
            user_id = self.data_manager.add_user(
                name, age, health_conditions, emergency_contact
            )
            
            self.current_user_id = user_id
            logger.info(f"User profile setup complete: {name}, ID: {user_id}")
            
            return user_id
            
        except Exception as e:
            logger.error(f"Error setting up user profile: {e}")
            raise
    
    async def add_medication(self, name: str, dosage: str, frequency: str, 
                           time_slots: List[str]) -> int:
        """Add medication information"""
        try:
            med_id = self.data_manager.add_medication(
                self.current_user_id, name, dosage, frequency, time_slots
            )
            
            logger.info(f"Added medication: {name}")
            return med_id
            
        except Exception as e:
            logger.error(f"Error adding medication: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get available tools list"""
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description
            })
        return tools_info
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        history = []
        if hasattr(self.memory, 'chat_memory'):
            for message in self.memory.chat_memory.messages:
                history.append({
                    "type": message.__class__.__name__,
                    "content": message.content
                })
        return history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.memory.clear()
        logger.info("Conversation history cleared")
    
    async def test_agent(self) -> Dict[str, Any]:
        """Test Agent functionality"""
        test_cases = [
            "I want to set a reminder for blood pressure medication, once daily, at 8am",
            "My blood pressure today is 140/90, please record it",
            "I want to schedule a cardiology appointment, tomorrow afternoon",
            "I have chest pain, I need urgent help",
            "What's the weather today, any health advice?",
            "What medications do I need to take?",
            "Do I have any reminders today?"
        ]
        
        results = []
        for test_input in test_cases:
            result = await self.process_user_input(test_input)
            results.append({
                "input": test_input,
                "output": result["response"],
                "success": result["success"]
            })
        
        return {
            "test_results": results,
            "available_tools": self.get_available_tools(),
            "conversation_history": self.get_conversation_history()
        }
    
    async def test_workflow(self) -> Dict[str, Any]:
        """Test LangGraph workflow"""
        return await self.workflow.test_workflow()
    
    async def generate_chat_title(self, first_message: str) -> str:
        """Generate chat title based on first user message using LLM"""
        try:
            logger.info(f"Generating chat title for message: {first_message[:50]}...")
            
            # Create a simple prompt for title generation
            title_prompt = f"""
            Based on the following user message, generate a concise and descriptive title for a health assistant conversation.
            The title should be 2-6 words maximum and capture the main topic or intent.
            
            User message: "{first_message}"
            
            Generate a title:
            """
            
            # Use LLM to generate title
            response = await self.llm.ainvoke(title_prompt)
            title = response.content.strip()
            
            # Clean up the title
            title = title.replace('"', '').replace("'", '').strip()
            
            # Ensure title is not too long
            if len(title) > 30:
                words = title.split()[:4]
                title = ' '.join(words) + '...'
            
            logger.info(f"Generated chat title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Failed to generate chat title: {e}")
            # Fallback to simple title generation
            words = first_message.split()[:3]
            return ' '.join(words) + ('...' if len(first_message.split()) > 3 else '')
    
    def stop_conversation(self):
        """Stop conversation"""
        voice_processor.stop_speaking()
        logger.info("Conversation stopped")

# Global AI agent instance - lazy initialization
_langchain_health_assistant = None

def get_health_assistant() -> LangChainHealthAssistant:
    """Get health assistant instance (lazy loading)"""
    global _langchain_health_assistant
    if _langchain_health_assistant is None:
        if not config.openai_api_key:
            raise ValueError("OpenAI API key not set, please configure OPENAI_API_KEY in .env file")
        _langchain_health_assistant = LangChainHealthAssistant(config.openai_api_key)
    return _langchain_health_assistant

# Keep original variable name for backward compatibility
try:
    if config.openai_api_key:
        langchain_health_assistant = LangChainHealthAssistant(config.openai_api_key)
    else:
        langchain_health_assistant = None
        logger.warning("OpenAI API key not set, health assistant will be initialized on first use")
except Exception as e:
    logger.error(f"Failed to initialize health assistant: {e}")
    langchain_health_assistant = None
