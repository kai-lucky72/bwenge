#!/usr/bin/env python3
"""
Verify that all Bwenge OS services are running properly in Docker
"""

import requests
import time
import sys
import subprocess
import json



def check_docker_compose():
    """Check if docker-compose is running"""

    try:
        result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 

                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:

            containers = []
            for line in result.stdout.strip().split('\n'):

                if line:

                    try:

                        container = json.loads(line)

                        containers.append(container)
                    except json.JSONDecodeError:
                        pass
            return containers
        return []



        
    except Exception as e:
        print(f"Error checking docker-compose: {e}")
        return []

def check_service_health(service_name, port, max_retries=30):
    """Check if a service is healthy"""
    url = f"http://localhost:{port}/health"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {service_name} (port {port}): {data.get('status', 'OK')}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            print(f"⏳ Waiting for {service_name} (attempt {attempt + 1}/{max_retries})...")
            time.sleep(2)
    
    print(f"❌ {service_name} (port {port}): Not responding")
    return False

def main():
    print("🔍 Verifying Bwenge OS Docker Services")
    print("=" * 50)
    
    # Check docker-compose status
    print("\n📦 Docker Compose Status:")
    containers = check_docker_compose()
    
    if not containers:
        print("❌ No containers found. Run 'docker-compose up -d' first.")
        sys.exit(1)
    
    for container in containers:
        name = container.get('Name', 'Unknown')
        state = container.get('State', 'Unknown')
        status = container.get('Status', 'Unknown')
        
        if state == 'running':
            print(f"✅ {name}: {status}")
        else:
            print(f"❌ {name}: {state} - {status}")
    
    # Check service health endpoints
    print("\n🏥 Service Health Checks:")
    
    services = [
        ("API Gateway", 8000),
        ("Auth Service", 8001),
        ("Ingest Service", 8002),
        ("Persona Service", 8003),
        ("Chat Service", 8004),
        ("3D Service", 8005),
        ("Analytics Service", 8006),
        ("Payments Service", 8007)
    ]
    
    healthy_services = 0
    total_services = len(services)
    
    for service_name, port in services:
        if check_service_health(service_name, port):
            healthy_services += 1
    
    # Check infrastructure services
    print("\n🏗️ Infrastructure Services:")
    
    # Check PostgreSQL
    try:
        result = subprocess.run(['docker-compose', 'exec', '-T', 'postgres', 'pg_isready', '-U', 'bwenge'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ PostgreSQL: Ready")
        else:
            print("❌ PostgreSQL: Not ready")
    except Exception:
        print("❌ PostgreSQL: Cannot check status")
    
    # Check Redis
    try:
        result = subprocess.run(['docker-compose', 'exec', '-T', 'redis', 'redis-cli', 'ping'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis: Ready")
        else:
            print("❌ Redis: Not ready")
    except Exception:
        print("❌ Redis: Cannot check status")
    
    # Check Weaviate
    try:
        response = requests.get("http://localhost:8080/v1/meta", timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate: Ready")
        else:
            print("❌ Weaviate: Not ready")
    except Exception:
        print("❌ Weaviate: Cannot connect")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"Services: {healthy_services}/{total_services} healthy")
    
    if healthy_services == total_services:
        print("🎉 All services are running successfully!")
        print("\n🚀 Next steps:")
        print("   1. Test the API: python3 scripts/test-api.py")
        print("   2. Create sample data: python3 scripts/create-sample-data.py")
        print("   3. View logs: docker-compose logs -f")
        return 0
    else:
        print("⚠️  Some services are not healthy. Check logs with: docker-compose logs")
        return 1

if __name__ == "__main__":
    sys.exit(main())