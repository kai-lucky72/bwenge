#!/usr/bin/env python3
"""
Service Runner for Bwenge OS
Runs individual services for development
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

SERVICES = {
    "api-gateway": {
        "path": "services/api-gateway",
        "port": 8000,
        "description": "API Gateway - Central routing and authentication"
    },
    "auth": {
        "path": "services/auth-service", 
        "port": 8001,
        "description": "Auth Service - User authentication and management"
    },
    "ingest": {
        "path": "services/ingest-service",
        "port": 8002,
        "description": "Ingest Service - Knowledge ingestion and processing"
    },
    "persona": {
        "path": "services/persona-service",
        "port": 8003,
        "description": "Persona Service - AI persona management and RAG"
    },
    "chat": {
        "path": "services/chat-service",
        "port": 8004,
        "description": "Chat Service - Real-time messaging and WebSocket"
    },
    "3d": {
        "path": "services/3d-service",
        "port": 8005,
        "description": "3D Service - 3D model management and serving"
    },
    "analytics": {
        "path": "services/analytics-service",
        "port": 8006,
        "description": "Analytics Service - Usage analytics and reporting"
    },
    "payments": {
        "path": "services/payments-service",
        "port": 8007,
        "description": "Payments Service - Subscription and billing"
    }
}

def run_service(service_name: str, reload: bool = True):
    """Run a specific service"""
    
    if service_name not in SERVICES:
        print(f"❌ Unknown service: {service_name}")
        print(f"Available services: {', '.join(SERVICES.keys())}")
        return False
    
    service = SERVICES[service_name]
    service_path = project_root / service["path"]
    
    if not service_path.exists():
        print(f"❌ Service path not found: {service_path}")
        return False
    
    print(f"🚀 Starting {service['description']}")
    print(f"📍 Path: {service_path}")
    print(f"🌐 URL: http://localhost:{service['port']}")
    print(f"🔄 Reload: {'enabled' if reload else 'disabled'}")
    print("-" * 50)
    
    # Change to service directory
    os.chdir(service_path)
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    # Build uvicorn command
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(service["port"])
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        # Run the service
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping {service_name} service...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Service failed to start: {e}")
        return False
    except FileNotFoundError:
        print("❌ uvicorn not found. Please install it with: pip install uvicorn")
        return False
    
    return True

def list_services():
    """List all available services"""
    print("📋 Available Bwenge OS Services:")
    print("=" * 50)
    
    for name, info in SERVICES.items():
        print(f"🔹 {name:<12} - {info['description']}")
        print(f"   Port: {info['port']}, Path: {info['path']}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Run Bwenge OS services")
    parser.add_argument("service", nargs="?", help="Service to run")
    parser.add_argument("--list", "-l", action="store_true", help="List available services")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    if args.list:
        list_services()
        return
    
    if not args.service:
        print("❌ Please specify a service to run")
        list_services()
        return
    
    success = run_service(args.service, reload=not args.no_reload)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()