#!/usr/bin/env python3
"""
Bwenge OS System Status Monitor

This script provides comprehensive system status monitoring including:
- Service health checks
- Database connectivity
- Resource usage
- Performance metrics
- Error rates
"""

import requests
import psycopg2
import redis
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import subprocess

class SystemMonitor:
    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://bwenge:bwenge_dev@localhost:5432/bwenge")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        
        self.services = {
            "api-gateway": "http://localhost:8000",
            "auth-service": "http://localhost:8001",
            "ingest-service": "http://localhost:8002",
            "persona-service": "http://localhost:8003",
            "chat-service": "http://localhost:8004",
            "3d-service": "http://localhost:8005",
            "analytics-service": "http://localhost:8006",
            "payments-service": "http://localhost:8007"
        }
        
        self.status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "services": {},
            "infrastructure": {},
            "metrics": {},
            "alerts": []
        }
    
    def check_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            start_time = time.time()
            response = requests.get(f"{url}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "details": response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "error": f"HTTP {response.status_code}"
                }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "error": "Request timeout (>5s)"
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unreachable",
                "error": "Connection refused"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity and stats"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check connection
            cursor.execute("SELECT 1")
            
            # Get database stats
            cursor.execute("""
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections
            """)
            
            db_size, active_connections, total_connections = cursor.fetchone()
            
            # Get table stats
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                    n_live_tup as live_tuples
                FROM pg_stat_user_tables 
                ORDER BY total_operations DESC 
                LIMIT 5
            """)
            
            table_stats = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "status": "healthy",
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / 1024 / 1024, 2),
                "active_connections": active_connections,
                "total_connections": total_connections,
                "top_tables": [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "operations": row[2],
                        "live_tuples": row[3]
                    }
                    for row in table_stats
                ]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and stats"""
        try:
            r = redis.Redis.from_url(self.redis_url)
            
            # Check connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": {
                    db: info.get(f"db{db}", {})
                    for db in range(16)
                    if f"db{db}" in info
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_weaviate(self) -> Dict[str, Any]:
        """Check Weaviate vector database"""
        try:
            # Check meta endpoint
            response = requests.get(f"{self.weaviate_url}/v1/meta", timeout=5)
            
            if response.status_code == 200:
                meta = response.json()
                
                # Get objects count
                objects_response = requests.get(f"{self.weaviate_url}/v1/objects", timeout=5)
                objects_count = 0
                
                if objects_response.status_code == 200:
                    objects_data = objects_response.json()
                    objects_count = len(objects_data.get("objects", []))
                
                return {
                    "status": "healthy",
                    "version": meta.get("version"),
                    "hostname": meta.get("hostname"),
                    "objects_count": objects_count
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_docker_stats(self) -> Dict[str, Any]:
        """Get Docker container statistics"""
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        container = json.loads(line)
                        containers.append({
                            "name": container.get("Name"),
                            "state": container.get("State"),
                            "status": container.get("Status")
                        })
                
                return {
                    "status": "available",
                    "containers": containers
                }
            else:
                return {
                    "status": "error",
                    "error": "docker-compose not available"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Get load average (Unix-like systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
            else:
                load_avg = [0, 0, 0]
            
            # Get disk usage
            disk_usage = {}
            for path in ['.', './uploads', './assets']:
                if os.path.exists(path):
                    stat = os.statvfs(path)
                    total = stat.f_frsize * stat.f_blocks
                    free = stat.f_frsize * stat.f_bavail
                    used = total - free
                    
                    disk_usage[path] = {
                        "total_gb": round(total / 1024 / 1024 / 1024, 2),
                        "used_gb": round(used / 1024 / 1024 / 1024, 2),
                        "free_gb": round(free / 1024 / 1024 / 1024, 2),
                        "usage_percent": round((used / total) * 100, 1) if total > 0 else 0
                    }
            
            return {
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                },
                "disk_usage": disk_usage
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Test key API endpoints"""
        endpoints = [
            {"name": "Health Check", "url": f"{self.api_base_url}/health", "method": "GET"},
            {"name": "Auth Register", "url": f"{self.api_base_url}/auth/register", "method": "POST", "expect_error": True},
            {"name": "Personas List", "url": f"{self.api_base_url}/personas", "method": "GET", "expect_error": True},
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                if endpoint["method"] == "GET":
                    response = requests.get(endpoint["url"], timeout=5)
                else:
                    response = requests.post(endpoint["url"], json={}, timeout=5)
                
                response_time = (time.time() - start_time) * 1000
                
                # Some endpoints are expected to return errors (like auth without credentials)
                if endpoint.get("expect_error") and response.status_code in [401, 422]:
                    status = "reachable"
                elif response.status_code < 400:
                    status = "healthy"
                else:
                    status = "error"
                
                results[endpoint["name"]] = {
                    "status": status,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2)
                }
                
            except Exception as e:
                results[endpoint["name"]] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def generate_alerts(self):
        """Generate alerts based on system status"""
        alerts = []
        
        # Check service health
        unhealthy_services = [
            name for name, status in self.status["services"].items()
            if status.get("status") != "healthy"
        ]
        
        if unhealthy_services:
            alerts.append({
                "level": "critical",
                "message": f"Unhealthy services: {', '.join(unhealthy_services)}"
            })
        
        # Check database
        db_status = self.status["infrastructure"].get("database", {})
        if db_status.get("status") != "healthy":
            alerts.append({
                "level": "critical",
                "message": f"Database issue: {db_status.get('error', 'Unknown error')}"
            })
        
        # Check high response times
        slow_services = [
            name for name, status in self.status["services"].items()
            if status.get("response_time_ms", 0) > 2000  # > 2 seconds
        ]
        
        if slow_services:
            alerts.append({
                "level": "warning",
                "message": f"Slow response times: {', '.join(slow_services)}"
            })
        
        # Check disk usage
        metrics = self.status.get("metrics", {})
        disk_usage = metrics.get("disk_usage", {})
        
        for path, usage in disk_usage.items():
            if usage.get("usage_percent", 0) > 90:
                alerts.append({
                    "level": "warning",
                    "message": f"High disk usage on {path}: {usage['usage_percent']}%"
                })
        
        self.status["alerts"] = alerts
    
    def run_full_check(self) -> Dict[str, Any]:
        """Run complete system status check"""
        print("🔍 Running Bwenge OS system status check...")
        
        # Check all services
        print("Checking services...")
        for service_name, url in self.services.items():
            print(f"  - {service_name}...")
            self.status["services"][service_name] = self.check_service_health(service_name, url)
        
        # Check infrastructure
        print("Checking infrastructure...")
        print("  - PostgreSQL...")
        self.status["infrastructure"]["database"] = self.check_database()
        
        print("  - Redis...")
        self.status["infrastructure"]["redis"] = self.check_redis()
        
        print("  - Weaviate...")
        self.status["infrastructure"]["weaviate"] = self.check_weaviate()
        
        print("  - Docker...")
        self.status["infrastructure"]["docker"] = self.get_docker_stats()
        
        # Get metrics
        print("Collecting metrics...")
        self.status["metrics"] = self.get_system_metrics()
        
        # Test API endpoints
        print("Testing API endpoints...")
        self.status["api_tests"] = self.check_api_endpoints()
        
        # Generate alerts
        self.generate_alerts()
        
        # Determine overall status
        critical_alerts = [a for a in self.status["alerts"] if a["level"] == "critical"]
        warning_alerts = [a for a in self.status["alerts"] if a["level"] == "warning"]
        
        if critical_alerts:
            self.status["overall_status"] = "critical"
        elif warning_alerts:
            self.status["overall_status"] = "warning"
        else:
            self.status["overall_status"] = "healthy"
        
        return self.status
    
    def print_status_report(self):
        """Print formatted status report"""
        status = self.status
        
        # Header
        print("\n" + "="*60)
        print("🚀 BWENGE OS SYSTEM STATUS REPORT")
        print("="*60)
        print(f"Timestamp: {status['timestamp']}")
        print(f"Overall Status: {status['overall_status'].upper()}")
        
        # Services
        print(f"\n📊 SERVICES ({len(status['services'])})")
        print("-" * 40)
        for name, service_status in status["services"].items():
            status_icon = "✅" if service_status["status"] == "healthy" else "❌"
            response_time = service_status.get("response_time_ms", "N/A")
            print(f"{status_icon} {name:<20} {service_status['status']:<12} {response_time}ms")
        
        # Infrastructure
        print(f"\n🏗️  INFRASTRUCTURE")
        print("-" * 40)
        for name, infra_status in status["infrastructure"].items():
            status_icon = "✅" if infra_status["status"] == "healthy" else "❌"
            print(f"{status_icon} {name:<20} {infra_status['status']}")
            
            if name == "database" and infra_status["status"] == "healthy":
                print(f"    Size: {infra_status['database_size_mb']} MB")
                print(f"    Connections: {infra_status['active_connections']}/{infra_status['total_connections']}")
            
            elif name == "redis" and infra_status["status"] == "healthy":
                print(f"    Memory: {infra_status['used_memory_mb']} MB")
                print(f"    Clients: {infra_status['connected_clients']}")
        
        # Metrics
        print(f"\n📈 SYSTEM METRICS")
        print("-" * 40)
        metrics = status.get("metrics", {})
        
        if "load_average" in metrics:
            load = metrics["load_average"]
            print(f"Load Average: {load['1min']:.2f}, {load['5min']:.2f}, {load['15min']:.2f}")
        
        if "disk_usage" in metrics:
            print("Disk Usage:")
            for path, usage in metrics["disk_usage"].items():
                print(f"  {path}: {usage['used_gb']:.1f}GB / {usage['total_gb']:.1f}GB ({usage['usage_percent']:.1f}%)")
        
        # Alerts
        if status["alerts"]:
            print(f"\n⚠️  ALERTS ({len(status['alerts'])})")
            print("-" * 40)
            for alert in status["alerts"]:
                level_icon = "🔴" if alert["level"] == "critical" else "🟡"
                print(f"{level_icon} {alert['level'].upper()}: {alert['message']}")
        else:
            print(f"\n✅ NO ALERTS")
        
        print("\n" + "="*60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bwenge OS System Status Monitor")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--save", help="Save report to file")
    parser.add_argument("--watch", type=int, help="Watch mode - refresh every N seconds")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.watch:
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                status = monitor.run_full_check()
                
                if args.json:
                    print(json.dumps(status, indent=2))
                else:
                    monitor.print_status_report()
                
                print(f"\nRefreshing in {args.watch} seconds... (Ctrl+C to stop)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        status = monitor.run_full_check()
        
        if args.json:
            output = json.dumps(status, indent=2)
            print(output)
            
            if args.save:
                with open(args.save, 'w') as f:
                    f.write(output)
                print(f"\nReport saved to: {args.save}")
        else:
            monitor.print_status_report()
            
            if args.save:
                with open(args.save, 'w') as f:
                    f.write(json.dumps(status, indent=2))
                print(f"\nReport saved to: {args.save}")

if __name__ == "__main__":
    main()