"""
Intelligent Health Assistant Startup Script
Voice-driven AI agent based on LangChain and LangGraph
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config, logger

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                Intelligent Health Assistant AI Agent         ║
    ║                  Voice-Driven AI Agents                       ║
    ║                                                              ║
    ║  🏥 Voice health management assistant for elderly            ║
    ║  🎤 Supports voice interaction and natural conversation      ║
    ║  📊 Intelligent health data management and analysis          ║
    ║  🔔 Personalized reminders and health advice                ║
    ║                                                              ║
    ║  Tech Stack: LangChain + LangGraph + OpenAI GPT-4           ║
    ║  Framework: FastAPI + WebSocket + SQLite                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check dependencies"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'openai', 'fastapi', 'uvicorn', 'speech_recognition', 
        'pyttsx3', 'pyaudio', 'pandas', 'requests',
        'langchain', 'langchain_openai', 'langchain_community',
        'langgraph', 'langsmith'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies checked successfully")
    return True

def check_audio_devices():
    """Check audio devices"""
    print("\n🎤 Checking audio devices...")
    
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        # Check input devices
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(info['name'])
        
        # Check output devices
        output_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                output_devices.append(info['name'])
        
        print(f"  ✅ Input devices: {len(input_devices)}")
        print(f"  ✅ Output devices: {len(output_devices)}")
        
        if input_devices:
            print(f"  📱 Default microphone: {input_devices[0]}")
        if output_devices:
            print(f"  🔊 Default speaker: {output_devices[0]}")
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"  ❌ Audio device check failed: {e}")
        return False

def check_configuration():
    """Check configuration"""
    print("\n⚙️  Checking configuration...")
    
    config_items = [
        ("OpenAI API Key", config.openai_api_key),
        ("Weather API Key", config.weather_api_key),
        ("Database URL", config.database_url),
        ("Server Address", f"{config.host}:{config.port}")
    ]
    
    for name, value in config_items:
        if value:
            if "API Key" in name:
                print(f"  ✅ {name}: Set")
            else:
                print(f"  ✅ {name}: {value}")
        else:
            if "API Key" in name:
                print(f"  ⚠️  {name}: Not set (optional)")
            else:
                print(f"  ✅ {name}: {value}")
    
    return True

def start_server():
    """Start server"""
    print("\n🚀 Starting server...")
    
    try:
        import uvicorn
        from main import app
        
        print(f"📡 Server address: http://{config.host}:{config.port}")
        print(f"🌐 Web interface: http://{config.host}:{config.port}/static/index.html")
        print(f"📚 API documentation: http://{config.host}:{config.port}/docs")
        print(f"🔌 WebSocket: ws://{config.host}:{config.port}/ws")
        
        print("\n💡 Usage instructions:")
        print("1. Open browser and access web interface")
        print("2. Click 'Connect Service' to establish connection")
        print("3. Click 'Start Conversation' to begin voice interaction")
        print("4. Use 'Voice Input' button for voice conversation")
        print("5. Or directly input questions in text box")
        
        print("\n🔧 LangChain features:")
        print("- Intelligent tool calling and Agent execution")
        print("- LangGraph workflow management")
        print("- Conversation memory and history management")
        print("- Professional health management tools")
        
        print("\n🛑 Press Ctrl+C to stop service")
        print("=" * 60)
        
        # Start server
        # Note: When passing app object directly, reload mode cannot be used
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            reload=False,  # Disable reload to avoid issues
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Service stopped")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        logger.error(f"Failed to start server: {e}")

def run_tests():
    """Run tests"""
    print("\n🧪 Running LangChain system tests...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ LangChain system tests passed")
            print(result.stdout)
        else:
            print("❌ LangChain system tests failed")
            print(result.stderr)
            
    except Exception as e:
        print(f"⚠️  Error running tests: {e}")

def show_framework_info():
    """Show framework information"""
    print("\n📚 LangChain framework information:")
    print("=" * 50)
    
    print("🔧 Core components:")
    print("  - LangChain: AI application development framework")
    print("  - LangGraph: Workflow and state management")
    print("  - OpenAI GPT-4: Large language model")
    print("  - FastAPI: Web service framework")
    print("  - WebSocket: Real-time communication")
    
    print("\n🛠️  Tool set:")
    print("  - medication_reminder: Medication reminder tool")
    print("  - health_record: Health record tool")
    print("  - doctor_appointment: Doctor appointment tool")
    print("  - emergency_alert: Emergency alert tool")
    print("  - weather_health_advice: Weather health advice tool")
    print("  - medication_query: Medication query tool")
    print("  - reminder_query: Reminder query tool")
    
    print("\n🔄 Workflow:")
    print("  1. Analyze user input")
    print("  2. Route to appropriate tool")
    print("  3. Execute tool operation")
    print("  4. Generate intelligent response")
    print("  5. Error handling")

def main():
    """Main function"""
    print_banner()
    
    # Check parameters
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            run_tests()
            return
        elif sys.argv[1] == "help":
            print_help()
            return
        elif sys.argv[1] == "info":
            show_framework_info()
            return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check audio devices
    if not check_audio_devices():
        print("\n⚠️  Audio device check failed, but can continue running (text mode)")
    
    # Check configuration
    check_configuration()
    
    # Start server
    start_server()

def print_help():
    """Print help information"""
    help_text = """
📖 Intelligent Health Assistant Usage Instructions

🚀 Start service:
    python start.py

🧪 Run tests:
    python start.py test

📚 Show framework information:
    python start.py info

❓ Show help:
    python start.py help

📁 Project structure:
    ├── langchain_tools.py        # LangChain tool definitions
    ├── langgraph_workflow.py     # LangGraph workflow
    ├── langchain_agent.py        # LangChain Agent core
    ├── main.py                   # Web API service
    ├── test.py                   # LangChain tests
    ├── start.py                  # Startup script
    └── requirements.txt          # Dependency package list

🔧 Configuration instructions:
    1. Copy config.env.example to .env
    2. Set OpenAI API key (required)
    3. Optionally set weather API key
    4. Other configurations use default values

🎯 Feature characteristics:
    - LangChain Agent intelligent conversation
    - LangGraph workflow management
    - Professional health management tools
    - Voice interaction conversation
    - Health data management
    - Emergency situation handling
    - Personalized health advice

🌐 Access addresses:
    - Web interface: http://localhost:8000/static/index.html
    - API documentation: http://localhost:8000/docs
    - WebSocket: ws://localhost:8000/ws

🔧 LangChain advantages:
    - Modular tool design
    - Intelligent Agent execution
    - Workflow state management
    - Memory and context
    - Error handling mechanism
    """
    print(help_text)

if __name__ == "__main__":
    main()
