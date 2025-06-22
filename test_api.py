#!/usr/bin/env python3
"""
Test script for University Chatbot API
This script tests the basic functionality of the chatbot API.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"
CHAT_BASE = f"{BASE_URL}/api/chat"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

def test_university_info():
    """Test getting university information."""
    print("🔍 Testing university info...")
    try:
        response = requests.get(f"{API_BASE}/university-info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ University info retrieved: {data['university_name']}")
            return True
        else:
            print(f"❌ University info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ University info failed: {str(e)}")
        return False

def test_chat_session():
    """Test creating a chat session and sending messages."""
    print("🔍 Testing chat functionality...")
    
    # Create session
    try:
        response = requests.post(f"{CHAT_BASE}/session")
        if response.status_code != 201:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
        
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ Chat session created: {session_id}")
        
        # Send a test message
        test_message = {
            "message": "What programs do you offer?"
        }
        
        response = requests.post(
            f"{CHAT_BASE}/session/{session_id}/message",
            json=test_message,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            message_data = response.json()
            print(f"✅ Message sent and response received")
            print(f"   Response: {message_data['response'][:100]}...")
            return True
        else:
            print(f"❌ Message failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test failed: {str(e)}")
        return False

def test_document_endpoints():
    """Test document-related endpoints."""
    print("🔍 Testing document endpoints...")
    
    # Test listing documents (should work even if empty)
    try:
        response = requests.get(f"{API_BASE}/documents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Document list retrieved: {data['total_count']} documents")
            return True
        else:
            print(f"❌ Document list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document list failed: {str(e)}")
        return False

def test_vector_stats():
    """Test vector database statistics."""
    print("🔍 Testing vector stats...")
    try:
        response = requests.get(f"{API_BASE}/vector-stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vector stats retrieved: {data['vector_database']['total_chunks']} chunks")
            return True
        else:
            print(f"❌ Vector stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Vector stats failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 University Chatbot API Tests")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("University Info", test_university_info),
        ("Document Endpoints", test_document_endpoints),
        ("Vector Stats", test_vector_stats),
        ("Chat Session", test_chat_session),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("\n💡 Common issues:")
        print("- Make sure the Flask app is running (python app.py)")
        print("- Check your .env file has the correct API keys")
        print("- Ensure database is initialized (python setup.py)")

if __name__ == "__main__":
    main() 