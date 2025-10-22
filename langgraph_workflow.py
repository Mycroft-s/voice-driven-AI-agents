"""
LangGraph Workflow Module
Defines the conversation workflow for the health assistant AI agent
"""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from langchain_tools import create_health_tools
from data_manager import HealthDataManager
from external_apis import ExternalAPIManager
from config import config

logger = logging.getLogger(__name__)

class HealthAssistantState(TypedDict):
    """Health assistant state"""
    messages: List[Any]
    user_id: int
    current_action: Optional[str]
    tool_results: List[str]
    final_response: Optional[str]
    error: Optional[str]

class HealthAssistantWorkflow:
    """Health assistant workflow"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=openai_api_key
        )
        
        # Initialize data manager and API manager
        self.data_manager = HealthDataManager()
        self.api_manager = ExternalAPIManager(
            weather_api_key=config.weather_api_key,
            calendar_api_key=config.calendar_api_key
        )
        
        # Create tools
        self.tools = create_health_tools(self.data_manager, self.api_manager)
        self.tool_node = ToolNode(self.tools)
        
        # Create memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("Health assistant workflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build workflow graph"""
        workflow = StateGraph(HealthAssistantState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("route_to_tool", self._route_to_tool)
        workflow.add_node("execute_tool", self.tool_node)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("analyze_input")
        
        # Add conditional edges - from analyze_input based on error status
        workflow.add_conditional_edges(
            "analyze_input",
            self._check_error,
            {
                "continue": "route_to_tool",
                "error": "handle_error"
            }
        )
        
        # Add conditional edges - from route_to_tool based on error status
        workflow.add_conditional_edges(
            "route_to_tool",
            self._check_error,
            {
                "continue": "execute_tool",
                "error": "handle_error"
            }
        )
        
        # Add conditional edges - from execute_tool based on error status
        workflow.add_conditional_edges(
            "execute_tool",
            self._check_error,
            {
                "continue": "generate_response",
                "error": "handle_error"
            }
        )
        
        # Add end edges
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _check_error(self, state: HealthAssistantState) -> str:
        """Check if there is an error"""
        if state.get("error"):
            return "error"
        return "continue"
    
    def _analyze_input(self, state: HealthAssistantState) -> HealthAssistantState:
        """Analyze user input"""
        try:
            messages = state["messages"]
            if not messages:
                state["error"] = "No user input received"
                return state
            
            last_message = messages[-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Use LLM to analyze user intent
            analysis_prompt = f"""
            Analyze the following user input and determine what operation the user wants to perform:
            
            User input: {user_input}
            
            Possible operation types:
            1. medication_reminder - Set medication reminder
            2. health_record - Record health information
            3. doctor_appointment - Schedule doctor appointment
            4. emergency_alert - Emergency situation
            5. weather_advice - Weather health advice
            6. medication_query - Query medication information
            7. reminder_query - Query reminders
            8. general_chat - General conversation
            
            Return only the operation type, nothing else.
            """
            
            analysis_message = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            action_type = analysis_message.content.strip().lower()
            
            # Validate operation type
            valid_actions = [
                "medication_reminder", "health_record", "doctor_appointment",
                "emergency_alert", "weather_advice", "medication_query",
                "reminder_query", "general_chat"
            ]
            
            if action_type not in valid_actions:
                action_type = "general_chat"
            
            state["current_action"] = action_type
            logger.info(f"Analyzed user input, identified operation type: {action_type}")
            
        except Exception as e:
            logger.error(f"Failed to analyze user input: {e}")
            state["error"] = f"Failed to analyze user input: {str(e)}"
        
        return state
    
    def _route_to_tool(self, state: HealthAssistantState) -> HealthAssistantState:
        """Route to appropriate tool"""
        try:
            action_type = state["current_action"]
            
            if action_type == "general_chat":
                # Generate response directly, no tool needed
                state["current_action"] = "generate_response"
            else:
                # Prepare tool invocation
                state["current_action"] = "execute_tool"
            
            logger.info(f"Routed to operation: {action_type}")
            
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            state["error"] = f"Routing failed: {str(e)}"
        
        return state
    
    def _generate_response(self, state: HealthAssistantState) -> HealthAssistantState:
        """Generate final response"""
        try:
            messages = state["messages"]
            user_input = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            tool_results = state.get("tool_results", [])
            
            # Build system prompt
            system_prompt = """
            You are a professional health assistant AI, specialized in providing health management services for elderly people.
            
            Your responsibilities include:
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
            
            Please reply to users in English.
            """
            
            # Build response prompt
            response_prompt = f"""
            User input: {user_input}
            
            """
            
            if tool_results:
                response_prompt += f"""
            Tool execution results:
            {chr(10).join(tool_results)}
                
            """
            
            response_prompt += """
            Based on the user input and tool execution results, generate a natural and friendly response.
            If the tool executed successfully, confirm the operation is complete and provide relevant advice.
            If it's general conversation, provide useful health advice.
            """
            
            # Generate response
            response_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=response_prompt)
            ]
            
            response = self.llm.invoke(response_messages)
            state["final_response"] = response.content
            
            logger.info("Generated final response successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            state["error"] = f"Failed to generate response: {str(e)}"
        
        return state
    
    def _handle_error(self, state: HealthAssistantState) -> HealthAssistantState:
        """Handle errors"""
        error = state.get("error", "Unknown error")
        state["final_response"] = f"Sorry, there was an issue processing your request: {error}. Please try again later."
        logger.error(f"Workflow error handling: {error}")
        return state
    
    async def process_user_input(self, user_input: str, user_id: int = 1) -> Dict[str, Any]:
        """Process user input"""
        try:
            # Initialize state
            initial_state = HealthAssistantState(
                messages=[HumanMessage(content=user_input)],
                user_id=user_id,
                current_action=None,
                tool_results=[],
                final_response=None,
                error=None
            )
            
            # Execute workflow
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "success": True,
                "response": result["final_response"],
                "action": result.get("current_action"),
                "tool_results": result.get("tool_results", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process user input: {e}")
            return {
                "success": False,
                "response": f"Sorry, there was an issue processing your request: {str(e)}",
                "action": None,
                "tool_results": [],
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_workflow_graph(self) -> str:
        """Get visual representation of workflow graph"""
        try:
            return self.workflow.get_graph().draw_mermaid()
        except Exception as e:
            logger.error(f"Failed to get workflow graph: {e}")
            return "Unable to generate workflow graph"
    
    async def test_workflow(self) -> Dict[str, Any]:
        """Test workflow"""
        test_cases = [
            "I want to set a reminder for blood pressure medication",
            "My blood pressure is a bit high today, please record it",
            "I want to schedule a cardiology appointment",
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
                "action": result["action"]
            })
        
        return {
            "test_results": results,
            "workflow_graph": self.get_workflow_graph()
        }
