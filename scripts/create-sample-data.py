#!/usr/bin/env python3
"""
Create sample data for Bwenge OS testing

This script creates sample users, organizations, personas, and knowledge sources
for testing and demonstration purposes.
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Sample data
SAMPLE_ORGANIZATIONS = [
    {
        "name": "Demo University",
        "plan": "pro"
    },
    {
        "name": "Test High School",
        "plan": "basic"
    }
]

SAMPLE_USERS = [
    {
        "name": "Dr. Sarah Johnson",
        "email": "sarah.johnson@demo.edu",
        "password": "password123",
        "role": "teacher",
        "org_name": "Demo University"
    },
    {
        "name": "Prof. Michael Chen",
        "email": "michael.chen@demo.edu", 
        "password": "password123",
        "role": "teacher",
        "org_name": "Demo University"
    },
    {
        "name": "Alice Smith",
        "email": "alice.smith@demo.edu",
        "password": "password123",
        "role": "student"
    },
    {
        "name": "Bob Wilson",
        "email": "bob.wilson@demo.edu",
        "password": "password123",
        "role": "student"
    }
]

SAMPLE_PERSONAS = [
    {
        "name": "Professor Gabriel",
        "description": "An experienced computer science professor specializing in algorithms and data structures",
        "tone": {
            "style": "academic",
            "formality": "formal",
            "enthusiasm": "moderate"
        },
        "rules": {
            "guidelines": [
                "Always provide clear explanations with examples",
                "Break down complex concepts into simpler parts",
                "Encourage questions and critical thinking",
                "Use proper academic terminology"
            ]
        },
        "sample_prompts": [
            "Hello! I'm Professor Gabriel. How can I help you learn today?",
            "What topic would you like to explore?",
            "Do you have any questions about the material?"
        ],
        "safety_rules": [
            "No inappropriate content",
            "Stay focused on educational topics",
            "Maintain professional demeanor"
        ]
    },
    {
        "name": "Ms. Emma",
        "description": "A friendly elementary school teacher who makes learning fun and engaging",
        "tone": {
            "style": "friendly",
            "formality": "casual",
            "enthusiasm": "high"
        },
        "rules": {
            "guidelines": [
                "Use simple, age-appropriate language",
                "Make learning fun with games and activities",
                "Be encouraging and supportive",
                "Use lots of examples and analogies"
            ]
        },
        "sample_prompts": [
            "Hi there! I'm Ms. Emma, and I'm so excited to learn with you today!",
            "What would you like to discover together?",
            "Ready for a fun learning adventure?"
        ],
        "safety_rules": [
            "Child-safe content only",
            "No personal information requests",
            "Maintain appropriate boundaries"
        ]
    },
    {
        "name": "Dr. Physics",
        "description": "A passionate physics professor who loves explaining the wonders of the universe",
        "tone": {
            "style": "enthusiastic",
            "formality": "semi-formal",
            "enthusiasm": "very high"
        },
        "rules": {
            "guidelines": [
                "Use real-world examples to explain physics concepts",
                "Encourage experimentation and observation",
                "Make physics accessible and exciting",
                "Connect concepts to everyday life"
            ]
        },
        "sample_prompts": [
            "Welcome to the amazing world of physics!",
            "Let's explore how the universe works!",
            "What physics phenomenon would you like to understand?"
        ],
        "safety_rules": [
            "No dangerous experiments",
            "Focus on educational content",
            "Promote scientific thinking"
        ]
    }
]

SAMPLE_KNOWLEDGE_CONTENT = [
    {
        "title": "Introduction to Python Programming",
        "content": """
# Introduction to Python Programming

Python is a high-level, interpreted programming language known for its simplicity and readability.

## Key Features:
- Easy to learn and use
- Extensive standard library
- Cross-platform compatibility
- Large community support

## Basic Syntax:
```python
# Variables
name = "Alice"
age = 25

# Functions
def greet(name):
    return f"Hello, {name}!"

# Classes
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
```

## Common Use Cases:
- Web development
- Data analysis
- Machine learning
- Automation
- Scientific computing
        """,
        "type": "text"
    },
    {
        "title": "Basic Physics Concepts",
        "content": """
# Basic Physics Concepts

Physics is the fundamental science that seeks to understand how the universe works.

## Newton's Laws of Motion:

### First Law (Law of Inertia):
An object at rest stays at rest, and an object in motion stays in motion, unless acted upon by an external force.

### Second Law:
Force equals mass times acceleration (F = ma)

### Third Law:
For every action, there is an equal and opposite reaction.

## Energy:
- Kinetic Energy: Energy of motion (KE = ½mv²)
- Potential Energy: Stored energy (PE = mgh)
- Conservation of Energy: Energy cannot be created or destroyed

## Waves:
- Frequency: Number of waves per second
- Wavelength: Distance between wave peaks
- Amplitude: Height of the wave
        """,
        "type": "text"
    }
]

class SampleDataCreator:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.tokens = {}
        
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user and return auth tokens"""
        print(f"Creating user: {user_data['email']}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self.tokens[user_data['email']] = tokens
                print(f"✅ Created user: {user_data['name']}")
                return tokens
            else:
                # Try login if user already exists
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    tokens = response.json()
                    self.tokens[user_data['email']] = tokens
                    print(f"✅ Logged in existing user: {user_data['name']}")
                    return tokens
                else:
                    print(f"❌ Failed to create/login user: {user_data['email']}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating user {user_data['email']}: {e}")
            return None
    
    def create_persona(self, persona_data: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """Create a persona"""
        print(f"Creating persona: {persona_data['name']}")
        
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = self.session.post(
                f"{self.base_url}/personas",
                json=persona_data,
                headers=headers
            )
            
            if response.status_code == 200:
                persona = response.json()
                print(f"✅ Created persona: {persona_data['name']}")
                return persona
            else:
                print(f"❌ Failed to create persona: {persona_data['name']} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating persona {persona_data['name']}: {e}")
            return None
    
    def upload_knowledge(self, content_data: Dict[str, Any], persona_id: str, auth_token: str):
        """Upload knowledge content"""
        print(f"Uploading knowledge: {content_data['title']}")
        
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content_data['content'])
                temp_file_path = f.name
            
            # Upload the file
            with open(temp_file_path, 'rb') as f:
                files = {'file': (content_data['title'] + '.txt', f, 'text/plain')}
                data = {
                    'persona_id': persona_id,
                    'title': content_data['title']
                }
                
                response = self.session.post(
                    f"{self.base_url}/knowledge/upload",
                    files=files,
                    data=data,
                    headers=headers
                )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Uploaded knowledge: {content_data['title']}")
                return result
            else:
                print(f"❌ Failed to upload knowledge: {content_data['title']} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading knowledge {content_data['title']}: {e}")
            return None
    
    def wait_for_processing(self, upload_id: str, auth_token: str, max_wait: int = 60):
        """Wait for knowledge processing to complete"""
        print(f"Waiting for processing: {upload_id}")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/knowledge/{upload_id}/status",
                    headers=headers
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status')
                    
                    if status == 'ready':
                        print(f"✅ Processing completed: {upload_id}")
                        return True
                    elif status == 'failed':
                        print(f"❌ Processing failed: {upload_id}")
                        return False
                    else:
                        print(f"⏳ Processing status: {status}")
                        time.sleep(5)
                else:
                    print(f"❌ Error checking status: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error checking processing status: {e}")
                return False
        
        print(f"⏰ Processing timeout: {upload_id}")
        return False
    
    def create_all_sample_data(self):
        """Create all sample data"""
        print("🚀 Creating sample data for Bwenge OS...")
        
        # Create users
        created_users = []
        for user_data in SAMPLE_USERS:
            tokens = self.create_user(user_data)
            if tokens:
                created_users.append({
                    'user_data': user_data,
                    'tokens': tokens
                })
        
        if not created_users:
            print("❌ No users created, cannot continue")
            return
        
        # Use first teacher for creating personas
        teacher_user = None
        for user in created_users:
            if user['user_data'].get('role') == 'teacher':
                teacher_user = user
                break
        
        if not teacher_user:
            teacher_user = created_users[0]  # Use first user if no teacher
        
        auth_token = teacher_user['tokens']['access_token']
        
        # Create personas
        created_personas = []
        for persona_data in SAMPLE_PERSONAS:
            persona = self.create_persona(persona_data, auth_token)
            if persona:
                created_personas.append(persona)
        
        # Upload knowledge for each persona
        for i, persona in enumerate(created_personas):
            if i < len(SAMPLE_KNOWLEDGE_CONTENT):
                content = SAMPLE_KNOWLEDGE_CONTENT[i]
                upload_result = self.upload_knowledge(
                    content, 
                    persona['persona_id'], 
                    auth_token
                )
                
                if upload_result:
                    # Wait for processing
                    self.wait_for_processing(
                        upload_result['upload_id'], 
                        auth_token
                    )
        
        print("\n🎉 Sample data creation completed!")
        print(f"Created {len(created_users)} users")
        print(f"Created {len(created_personas)} personas")
        print("\n📝 Sample Users:")
        for user in created_users:
            user_data = user['user_data']
            print(f"  - {user_data['name']} ({user_data['email']}) - {user_data.get('role', 'user')}")
        
        print("\n🤖 Sample Personas:")
        for persona in created_personas:
            print(f"  - {persona['name']}: {persona['description'][:50]}...")
        
        print(f"\n🔑 Test Login Credentials:")
        print(f"  Email: {SAMPLE_USERS[0]['email']}")
        print(f"  Password: {SAMPLE_USERS[0]['password']}")

def main():
    """Main function"""
    print("🧪 Bwenge OS Sample Data Creator")
    print("=" * 40)
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not available at {API_BASE_URL}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API at {API_BASE_URL}: {e}")
        return
    
    creator = SampleDataCreator(API_BASE_URL)
    creator.create_all_sample_data()

if __name__ == "__main__":
    main()