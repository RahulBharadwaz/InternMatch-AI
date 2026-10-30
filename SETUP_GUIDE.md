# InternMatch - Detailed Setup Guide

This guide provides step-by-step instructions for setting up InternMatch on Windows with XAMPP.

## System Requirements

- **Operating System**: Windows 10 or Windows 11
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: Minimum 2GB free space
- **Python**: Version 3.12
- **XAMPP**: Latest version (7.4.33 or later)

## Step-by-Step Installation

### Step 1: Install XAMPP

1. Download XAMPP from https://www.apachefriends.org/download.html
2. Run the installer with administrator privileges
3. Select components:
   - ✅ Apache
   - ✅ MySQL
   - ✅ phpMyAdmin
   - ✅ PHP
4. Choose installation directory (default: `C:\xampp`)
5. Complete the installation

### Step 2: Start XAMPP Services

1. Open XAMPP Control Panel from Start Menu
2. Click **Start** button next to Apache
3. Click **Start** button next to MySQL
4. Ensure both services show green status

### Step 3: Verify XAMPP Installation

1. Open browser and visit http://localhost/
2. You should see XAMPP welcome page
3. Visit http://localhost/phpmyadmin/
4. You should see phpMyAdmin interface

### Step 4: Install Python

1. Download Python 3.12 from https://www.python.org/downloads/
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Complete the installation

### Step 5: Verify Python Installation

Open Command Prompt and run:

```bash
python --version
```

You should see: `Python 3.12.x`

### Step 6: Set Up Project Directory

1. Navigate to XAMPP htdocs:
```bash
cd C:\xampp\htdocs
```

2. If you have the project as a zip:
   - Extract the project folder to `C:\xampp\htdocs\internship`

3. If you have Git:
```bash
git clone <repository-url> internship
cd internship
```

### Step 7: Create Virtual Environment

```bash
cd C:\xampp\htdocs\internship
python -m venv venv
```

This creates a virtual environment in the `venv` folder.

### Step 8: Activate Virtual Environment

```bash
venv\Scripts\activate
```

You should see `(venv)` prefix in your command prompt.

### Step 9: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 10: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required Python packages:
- Flask and extensions
- Database drivers
- ML libraries
- Document parsing libraries

### Step 11: Configure Environment Variables

1. Copy the example environment file:
```bash
copy .env.example .env
```

2. Open `.env` file in a text editor

3. Configure the following settings:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-random-secret-key-here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=InternMatch_db
DB_USER=root
DB_PASSWORD=

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=pdf docx

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@InternMatch.local

# Application Configuration
ADMIN_EMAIL=admin@InternMatch.local
RECOMMENDATION_ALGORITHM_VERSION=1.0
```

4. Generate a random secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it as `SECRET_KEY`

### Step 12: Create MySQL Database

**Option A: Using phpMyAdmin**

1. Open http://localhost/phpmyadmin/
2. Click "New" in left sidebar
3. Enter database name: `InternMatch_db`
4. Select "utf8mb4_unicode_ci" as collation
5. Click "Create"

**Option B: Using MySQL Command Line**

```bash
cd C:\xampp\mysql\bin
mysql -u root
```

Then in MySQL prompt:
```sql
CREATE DATABASE InternMatch_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### Step 13: Initialize Database Tables

```bash
cd C:\xampp\htdocs\internship
python scripts\init_db.py
```

You should see:
```
Creating database tables...
Database tables created successfully!
```

If you already have an existing database and profile registration, profile
editing, or resume uploads fail because of missing profile/resume columns, run
this data-preserving schema update instead of dropping/recreating the database:

```bash
python scripts\migrate_profile_skills.py
```

### Step 14: Seed Demo Data (Recommended)

```bash
python scripts\seed_demo_data.py
```

This creates sample data for testing:
- Admin user: admin@InternMatch.local / Admin@123
- Student users: rahul.kumar@example.com / Student@123
- Sample opportunities and skills

### Step 15: Create Uploads Directory

```bash
mkdir uploads
```

This directory will store uploaded resumes.

### Step 16: Run the Application

```bash
python run.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Step 17: Access the Application

Open browser and visit: http://localhost:5000

You should see the InternMatch homepage.

## Verification Steps

### 1. Test Homepage
- Visit http://localhost:5000
- Verify homepage loads correctly
- Check navigation menu

### 2. Test Registration
- Click "Register"
- Fill in registration form
- Submit and verify account creation

### 3. Test Login
- Login with registered account
- Verify dashboard loads
- Check profile completion indicator

### 4. Test Admin Access
- Login with admin credentials (if seeded)
- Visit http://localhost:5000/admin
- Verify admin dashboard loads

### 5. Test Resume-Based Recommendations
- Visit http://localhost:5000/opportunities/explore
- Log in, then upload a resume or paste resume text
- Verify the app automatically opens ranked internship recommendations with match scores

## Common Issues and Solutions

### Issue: "Module not found" errors

**Solution**:
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: MySQL connection refused

**Solution**:
1. Ensure XAMPP MySQL is running
2. Check MySQL port (default: 3306)
3. Verify credentials in `.env`
4. Test connection in phpMyAdmin

### Issue: Port 5000 already in use

**Solution**:
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or run Flask on different port
set FLASK_RUN_PORT=5001
python run.py
```

### Issue: Permission denied for uploads

**Solution**:
```bash
# Ensure uploads directory exists and is writable
mkdir uploads
# Or create manually with write permissions
```

### Issue: PyMuPDF installation fails

**Solution**:
```bash
# Try installing from wheel
pip install pymupdf --only-binary pymupdf

# Or use alternative
pip install pymupdf-binary
```

## Development Workflow

### Making Code Changes

1. Activate virtual environment
2. Make code changes
3. Restart Flask server (it auto-reloads in development)
4. Test changes in browser

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/
```

### Database Reset

```bash
# Drop and recreate all tables
python scripts\init_db.py

# Reseed demo data
python scripts\seed_demo_data.py
```

### Creating New Admin

```bash
python scripts\create_admin.py
```

Follow the prompts to create an administrator.

## Production Deployment Considerations

For production deployment, consider:

1. **Security**:
   - Set `FLASK_ENVproduction` in `.env`
   - Use strong `SECRET_KEY`
   - Enable HTTPS
   - Set `SESSION_COOKIE_SECURE=True`

2. **Database**:
   - Use production MySQL instance
   - Create dedicated database user
   - Enable regular backups

3. **Web Server**:
   - Use Gunicorn or uWSGI
   - Configure Nginx as reverse proxy
   - Enable SSL/TLS certificates

4. **Monitoring**:
   - Set up logging
   - Monitor error logs
   - Track performance metrics

## Uninstallation

To completely remove InternMatch:

1. Stop Flask server (Ctrl+C)
2. Deactivate virtual environment:
```bash
deactivate
```

3. Delete project directory:
```bash
cd C:\xampp\htdocs
rmdir /s internship
```

4. Drop database in phpMyAdmin:
   - Select `InternMatch_db`
   - Click "Operations" tab
   - Click "Drop the database"

## Support

For issues or questions:

1. Check this guide first
2. Review README.md for feature documentation
3. Check code comments for implementation details
4. Contact through academic institution channels

## Next Steps

After successful setup:

1. Explore the application features
2. Review the code structure
3. Customize the recommendation weights in `config.py`
4. Add your own opportunities via admin panel
5. Implement additional features as needed
6. Write tests for new functionality

