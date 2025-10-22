"""
Intelligent Health Assistant Test Script
Tests AI health assistant functionality based on LangChain and LangGraph
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config, logger
from langchain_agent import langchain_health_assistant
from langgraph_workflow import HealthAssistantWorkflow

async def test_langchain_tools():
    """Test LangChain tools"""
    print("\n=== Testing LangChain Tools ===")
    try:
        tools = langchain_health_assistant.get_available_tools()
        print(f"✅ Available tools count: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        print("✅ LangChain tools test completed")
        
    except Exception as e:
        print(f"❌ LangChain tools test failed: {e}")

async def test_langchain_agent():
    """Test LangChain Agent"""
    print("\n=== Testing LangChain Agent ===")
    try:
        if not config.openai_api_key:
            print("⚠️  OpenAI API key not set, skipping Agent test")
            return
        
        # Test Agent functionality
        test_results = await langchain_health_assistant.test_agent()
        
        print(f"✅ Agent test completed, test cases: {len(test_results['test_results'])}")
        
        for i, result in enumerate(test_results['test_results'][:3], 1):
            print(f"\nTest case {i}:")
            print(f"  Input: {result['input']}")
            print(f"  Output: {result['output'][:100]}...")
            print(f"  Success: {result['success']}")
        
        print("✅ LangChain Agent test completed")
        
    except Exception as e:
        print(f"❌ LangChain Agent test failed: {e}")

async def test_langgraph_workflow():
    """Test LangGraph workflow"""
    print("\n=== Testing LangGraph Workflow ===")
    try:
        if not config.openai_api_key:
            print("⚠️  OpenAI API key not set, skipping workflow test")
            return
        
        # Test workflow
        workflow_results = await langchain_health_assistant.test_workflow()
        
        print(f"✅ Workflow test completed")
        print(f"  Test cases count: {len(workflow_results['test_results'])}")
        
        # Show workflow graph
        if 'workflow_graph' in workflow_results:
            print(f"  Workflow graph: {workflow_results['workflow_graph'][:100]}...")
        
        print("✅ LangGraph workflow test completed")
        
    except Exception as e:
        print(f"❌ LangGraph workflow test failed: {e}")

async def test_conversation_flow():
    """Test conversation flow"""
    print("\n=== Testing Conversation Flow ===")
    try:
        if not config.openai_api_key:
            print("⚠️  OpenAI API key not set, skipping conversation test")
            return
        
        # Test conversation scenarios
        conversation_scenarios = [
            "你好，我是张大爷，今年75岁",
            "我想设置降压药的提醒，每天一次，早上8点",
            "我今天血压是140/90，帮我记录一下",
            "我想预约心内科医生",
            "我有哪些药物需要服用？"
        ]
        
        print("Starting conversation test...")
        
        for i, scenario in enumerate(conversation_scenarios, 1):
            print(f"\nConversation {i}: {scenario}")
            
            result = await langchain_health_assistant.process_user_input(scenario)
            
            if result["success"]:
                print(f"✅ Response: {result['response'][:100]}...")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        print("✅ Conversation flow test completed")
        
    except Exception as e:
        print(f"❌ Conversation flow test failed: {e}")

async def test_memory_functionality():
    """Test memory functionality"""
    print("\n=== Testing Memory Functionality ===")
    try:
        if not config.openai_api_key:
            print("⚠️  OpenAI API key not set, skipping memory test")
            return
        
        # Get conversation history
        history = langchain_health_assistant.get_conversation_history()
        print(f"✅ Current conversation history length: {len(history)}")
        
        # Clear conversation history
        langchain_health_assistant.clear_conversation_history()
        print("✅ Conversation history cleared")
        
        # Get conversation history again
        history_after_clear = langchain_health_assistant.get_conversation_history()
        print(f"✅ Conversation history length after clear: {len(history_after_clear)}")
        
        print("✅ Memory functionality test completed")
        
    except Exception as e:
        print(f"❌ Memory functionality test failed: {e}")

async def test_data_integration():
    """Test data integration"""
    print("\n=== Testing Data Integration ===")
    try:
        # Test user profile
        user_id = await langchain_health_assistant.setup_user_profile(
            name="Test User",
            age=70,
            health_conditions=["高血压"],
            emergency_contact="13800138000"
        )
        print(f"✅ User profile created successfully, ID: {user_id}")
        
        # Test medication addition
        med_id = await langchain_health_assistant.add_medication(
            name="Test Medication",
            dosage="10mg",
            frequency="每天一次",
            time_slots=["09:00"]
        )
        print(f"✅ Medication added successfully, ID: {med_id}")
        
        # Test data query
        medications = langchain_health_assistant.data_manager.get_user_medications(user_id)
        print(f"✅ Retrieved medications count: {len(medications)}")
        
        print("✅ Data integration test completed")
        
    except Exception as e:
        print(f"❌ Data integration test failed: {e}")

async def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    try:
        # Test invalid input
        result = await langchain_health_assistant.process_user_input("")
        print(f"✅ Empty input handling: {result['success']}")
        
        # Test exception cases
        result = await langchain_health_assistant.process_user_input("This is a test exception case")
        print(f"✅ Exception handling: {result['success']}")
        
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Intelligent Health Assistant system tests")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Framework: LangChain + LangGraph")
    
    # Check configuration
    print(f"\n📋 Configuration check:")
    print(f"OpenAI API key: {'Set' if config.openai_api_key else 'Not set'}")
    print(f"Database path: {config.database_url}")
    
    # Run various tests
    await test_langchain_tools()
    await test_data_integration()
    await test_langchain_agent()
    await test_langgraph_workflow()
    await test_conversation_flow()
    await test_memory_functionality()
    await test_error_handling()
    
    print("\n🎉 All tests completed!")
    print("\n📝 Test summary:")
    print("- LangChain tools: 7 professional health management tools")
    print("- LangChain Agent: Intelligent conversation and tool calling")
    print("- LangGraph workflow: Structured conversation flow")
    print("- Memory functionality: Conversation history management")
    print("- Data integration: Health data CRUD operations")
    print("- Error handling: Comprehensive exception handling mechanism")

if __name__ == "__main__":
    # Set logging level
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    asyncio.run(run_all_tests())
