@echo off
REM Bwenge OS Complete Setup Script for Windows
REM This script sets up the complete development environment

echo 🚀 Starting Bwenge OS Complete Setup...
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create .env file from template
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file from template
    echo ⚠️  Please edit .env file with your API keys and configuration
    echo ℹ️  Required API keys:
    echo    - OPENAI_API_KEY (for AI functionality)
    echo    - STRIPE_SECRET_KEY (for payments - optional for development)
    echo    - JWT_SECRET (generate a secure random string)
) else (
    echo ✅ .env file already exists
)

REM Create virtual environment
if not exist venv (
    echo ℹ️  Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment and install dependencies
echo ℹ️  Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Python dependencies installed

REM Create necessary directories
echo ℹ️  Creating necessary directories...
if not exist uploads mkdir uploads
if not exist assets mkdir assets
if not exist assets\3d mkdir assets\3d
if not exist assets\models mkdir assets\models
if not exist logs mkdir logs
echo ✅ Directories created

REM Generate JWT secret if needed
echo ℹ️  Checking JWT secret...
findstr "your-jwt-secret-key" .env >nul
if not errorlevel 1 (
    echo ℹ️  Generating JWT secret...
    python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))" > temp_jwt.txt
    for /f "tokens=2 delims==" %%a in (temp_jwt.txt) do set JWT_SECRET=%%a
    powershell -Command "(gc .env) -replace 'your-jwt-secret-key', '%JWT_SECRET%' | Out-File -encoding ASCII .env"
    del temp_jwt.txt
    echo ✅ JWT secret generated
)

echo.
echo 🎉 Bwenge OS Setup Complete!
echo ===============================
echo ✅ Backend services are ready to run
echo ℹ️  Next steps:
echo    1. Edit .env file with your API keys
echo    2. Set up PostgreSQL database (see README.md)
echo    3. Set up Redis (see README.md)
echo    4. Set up Weaviate vector database (see README.md)
echo    5. Run individual services or use Docker
echo.
echo ℹ️  Service URLs (when running):
echo    - API Gateway: http://localhost:8000
echo    - Auth Service: http://localhost:8001
echo    - Ingest Service: http://localhost:8002
echo    - Persona Service: http://localhost:8003
echo    - Chat Service: http://localhost:8004
echo    - 3D Service: http://localhost:8005
echo    - Analytics Service: http://localhost:8006
echo    - Payments Service: http://localhost:8007
echo.
echo ℹ️  Default admin login: admin@bwenge.com / admin123
echo.
echo ⚠️  For full setup including databases, please:
echo    1. Install PostgreSQL and create database 'bwenge'
echo    2. Install Redis
echo    3. Run Weaviate with Docker: docker run -d -p 8080:8080 semitechnologies/weaviate:1.21.2
echo    4. Run database init: psql -U bwenge -d bwenge -f scripts\init-db.sql
echo.
pause