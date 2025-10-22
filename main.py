"""
Intelligent Health Assistant Web API Service
Voice-driven AI agent based on LangChain and LangGraph
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import uvicorn

from config import config, logger
from langchain_agent import langchain_health_assistant
from langgraph_workflow import HealthAssistantWorkflow

# Create FastAPI application
app = FastAPI(
    title="Intelligent Health Assistant API",
    description="Voice-driven AI Health Assistant API based on LangChain and LangGraph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket connection management
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connection established")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket connection closed")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    """Root endpoint - serve the main page"""
    return FileResponse("static/index.html")

@app.get("/login")
async def login_page():
    """Login page endpoint"""
    return FileResponse("static/index.html")

@app.get("/register") 
async def register_page():
    """Register page endpoint"""
    return FileResponse("static/index.html")

@app.get("/chat")
async def chat_page():
    """Chat page endpoint"""
    return FileResponse("static/index.html")

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Intelligent Health Assistant API",
        "version": "1.0.0",
        "framework": "LangChain + LangGraph",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "framework": "LangChain + LangGraph",
        "services": {
            "langchain_agent": "active",
            "langgraph_workflow": "active",
            "voice_processor": "active",
            "data_manager": "active",
            "api_manager": "active"
        }
    }

@app.get("/api/tools")
async def get_available_tools():
    """Get available tools list"""
    try:
        tools = langchain_health_assistant.get_available_tools()
        return {
            "success": True,
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to get tools list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    try:
        history = langchain_health_assistant.get_conversation_history()
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/clear")
async def clear_conversation_history():
    """Clear conversation history"""
    try:
        langchain_health_assistant.clear_conversation_history()
        return {
            "success": True,
            "message": "Conversation history cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/register")
async def register_user(user_data: dict):
    """Register new user"""
    try:
        # 从JSON数据中提取字段
        name = user_data.get('name')
        age = user_data.get('age')
        health_conditions = user_data.get('health_conditions')
        emergency_contact = user_data.get('emergency_contact')
        
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        user_id = langchain_health_assistant.data_manager.add_user(
            name=name,
            age=age,
            health_conditions=health_conditions,
            emergency_contact=emergency_contact
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "name": name,
            "message": "User registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/list")
async def list_users():
    """Get list of all users"""
    try:
        conn = langchain_health_assistant.data_manager.db_path
        import sqlite3
        connection = sqlite3.connect(conn)
        cursor = connection.cursor()
        
        cursor.execute('SELECT id, name, age FROM users ORDER BY id')
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'age': row[2]
            })
        
        connection.close()
        
        return {
            "success": True,
            "users": users
        }
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/{user_id}")
async def delete_user(user_id: int):
    """Delete user and all related data"""
    try:
        # 检查用户是否存在
        profile = langchain_health_assistant.data_manager.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 删除用户及其所有相关数据
        import sqlite3
        conn = sqlite3.connect(langchain_health_assistant.data_manager.db_path)
        cursor = conn.cursor()
        
        # 删除用户相关的所有数据
        cursor.execute('DELETE FROM medications WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM health_records WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {user_id} and all related data deleted")
        
        return {
            "success": True,
            "message": f"User {profile['name']} and all related data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/clear-all")
async def clear_all_users():
    """Clear all users and related data (use with caution!)"""
    try:
        import sqlite3
        conn = sqlite3.connect(langchain_health_assistant.data_manager.db_path)
        cursor = conn.cursor()
        
        # 清空所有表
        cursor.execute('DELETE FROM medications')
        cursor.execute('DELETE FROM health_records')
        cursor.execute('DELETE FROM reminders')
        cursor.execute('DELETE FROM users')
        
        # 重置自增ID
        cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("users", "medications", "health_records", "reminders")')
        
        conn.commit()
        conn.close()
        
        logger.info("All users and data cleared")
        
        return {
            "success": True,
            "message": "All users and related data cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear all users: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/api/user/login")
async def login_user(login_data: dict):
    """Login user by ID"""
    try:
        user_id = login_data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        profile = langchain_health_assistant.data_manager.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Set current user
        langchain_health_assistant.current_user_id = user_id
        
        return {
            "success": True,
            "user_id": user_id,
            "name": profile['name'],
            "age": profile['age'],
            "health_conditions": profile['health_conditions'],
            "message": f"Welcome back, {profile['name']}!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to login user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/profile")
async def create_user_profile(
    name: str,
    age: int,
    health_conditions: List[str] = None,
    emergency_contact: str = None
):
    """Create user profile (legacy endpoint)"""
    try:
        user_id = await langchain_health_assistant.setup_user_profile(
            name, age, health_conditions, emergency_contact
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User profile created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/medication")
async def add_medication(
    name: str,
    dosage: str,
    frequency: str,
    time_slots: List[str]
):
    """Add medication information"""
    try:
        med_id = await langchain_health_assistant.add_medication(
            name, dosage, frequency, time_slots
        )
        
        return {
            "success": True,
            "medication_id": med_id,
            "message": "Medication information added successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to add medication information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/medications")
async def get_medications():
    """Get user medication information"""
    try:
        medications = langchain_health_assistant.data_manager.get_user_medications(
            langchain_health_assistant.current_user_id
        )
        
        return {
            "success": True,
            "medications": medications
        }
        
    except Exception as e:
        logger.error(f"Failed to get medication information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reminders/today")
async def get_today_reminders():
    """Get today's reminders"""
    try:
        reminders = langchain_health_assistant.data_manager.get_today_reminders(
            langchain_health_assistant.current_user_id
        )
        
        return {
            "success": True,
            "reminders": reminders
        }
        
    except Exception as e:
        logger.error(f"Failed to get today's reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: int):
    """Mark reminder as completed"""
    try:
        langchain_health_assistant.data_manager.complete_reminder(reminder_id)
        
        return {
            "success": True,
            "message": "Reminder completed"
        }
        
    except Exception as e:
        logger.error(f"Failed to complete reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health-records/recent")
async def get_recent_health_records(days: int = 7):
    """Get recent health records"""
    try:
        records = langchain_health_assistant.data_manager.get_recent_health_records(
            langchain_health_assistant.current_user_id, days
        )
        
        return {
            "success": True,
            "records": records
        }
        
    except Exception as e:
        logger.error(f"Failed to get health records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/text")
async def process_text_input(user_input: str):
    """Process text input"""
    try:
        result = await langchain_health_assistant.process_user_input(user_input)
        
        return {
            "success": result["success"],
            "response": result["response"],
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Failed to process text input: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test/agent")
async def test_agent():
    """Test LangChain Agent functionality"""
    try:
        results = await langchain_health_assistant.test_agent()
        
        return {
            "success": True,
            "test_results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to test Agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test/workflow")
async def test_workflow():
    """Test LangGraph workflow"""
    try:
        results = await langchain_health_assistant.test_workflow()
        
        return {
            "success": True,
            "test_results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to test workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow/graph")
async def get_workflow_graph():
    """Get workflow graph"""
    try:
        graph = langchain_health_assistant.workflow.get_workflow_graph()
        
        return {
            "success": True,
            "graph": graph
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint - Real-time voice interaction"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        welcome_message = await langchain_health_assistant.start_conversation()
        await manager.send_personal_message(
            json.dumps({
                "type": "welcome",
                "message": welcome_message,
                "framework": "LangChain + LangGraph",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        while True:
            # Receive client message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "voice_input":
                # Process voice input
                result = await langchain_health_assistant.process_voice_input()
                
                # Debug logging
                logger.info(f"Voice input result: {result}")
                logger.info(f"User input in result: {result.get('user_input', 'NOT FOUND')}")
                
                response_data = {
                    "type": "response",
                    "success": result["success"],
                    "response": result["response"],
                    "framework": "LangChain",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Include user input if available
                if "user_input" in result:
                    response_data["user_input"] = result["user_input"]
                    logger.info(f"Added user_input to response: {result['user_input']}")
                else:
                    logger.warning("No user_input found in result")
                
                logger.info(f"Sending response_data: {response_data}")
                
                await manager.send_personal_message(
                    json.dumps(response_data),
                    websocket
                )
            
            elif message_type == "text_input":
                # Process text input
                user_input = message_data.get("text", "")
                result = await langchain_health_assistant.process_user_input(user_input)
                
                await manager.send_personal_message(
                    json.dumps({
                        "type": "response",
                        "success": result["success"],
                        "response": result["response"],
                        "framework": "LangChain",
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )
            
            elif message_type == "stop":
                # Stop conversation (but keep connection)
                langchain_health_assistant.stop_conversation()
                await manager.send_personal_message(
                    json.dumps({
                        "type": "stopped",
                        "message": "Conversation paused, you can resume anytime",
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )
                # Don't break, keep WebSocket connection for resuming
                continue
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        langchain_health_assistant.stop_conversation()
    except Exception as e:
        logger.error(f"WebSocket processing error: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"Processing error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Intelligent Health Assistant API service starting")
    
    # Check if demo user exists, if not create one
    try:
        # Try to get user with ID 1
        demo_user = langchain_health_assistant.data_manager.get_user_profile(1)
        
        if not demo_user:
            # Create demo user if doesn't exist
            await langchain_health_assistant.setup_user_profile(
                name="Demo User",
                age=70,
                health_conditions=["Hypertension"],
                emergency_contact="13800138000"
            )
            
            # Add sample medications for demo user
            await langchain_health_assistant.add_medication(
                name="Blood Pressure Medication",
                dosage="5mg",
                frequency="Once daily",
                time_slots=["08:00"]
            )
            
            logger.info("Demo user profile created")
        else:
            logger.info(f"Found existing user: {demo_user['name']}")
        
    except Exception as e:
        logger.error(f"Failed to initialize demo data: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Intelligent Health Assistant API service shutting down")
    langchain_health_assistant.stop_conversation()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )
