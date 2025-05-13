# Phase 1 Implementation
### TODO:
## Environment Setup
- Choose Tech Stack
- Initialize Git repo
- CI/CD Skeleton
- Provision hosting
- Project Structures

## Lead Ingestion
- Create web form
- CSV parser & upload
- Field mapping
- Backend ingestion route

## Web Form & Database Feature

A new feature has been added to provide manual lead entry through a web form interface with database storage.

### Components:

1. **Web Form (Frontend just only for Testing)**
   - Simple form to collect lead information (name, email, phone, company)
   - HTML templates with CSS styling for clean UI
   - Form validation for required fields

2. **CSV Upload Feature**
   - Upload leads in bulk via CSV files
   - Field mapping for CSV columns
   - Data validation and cleaning
   - Duplicate detection
   - Support for all lead fields:
     - Basic contact info (name, email, phone)
     - Company details (name, website, industry)
     - Location (city, state)
     - Additional fields (title, business type, notes)

3. **Database Connection (Backend)**
   - PostgreSQL database for storing lead information
   - Flask-SQLAlchemy integration for ORM functionality
   - Data model for leads with appropriate fields

4. **Data Viewing**
   - Page to view all submitted leads in a table format
   - Quick verification of stored information
   - Edit and delete functionality

### File Structure:
```
/backend
  /models
    lead_model.py    # Database model for Lead
  /controllers
    lead_controller.py  # Business logic for lead operations
    upload_controller.py # CSV upload processing
  /routes
    lead_routes.py   # API routes for lead operations
  /templates
    form.html        # Form for submitting leads
    upload.html      # CSV upload interface
    leads.html       # View for displaying stored leads
  /config
    config.py        # Configuration settings
  app.py            # Main Flask application
  wsgi.py           # WSGI entry point
```

### Data Flow:
1. User submits form with lead information or uploads CSV file
2. Backend validates and processes form data
3. Lead data is stored in PostgreSQL database
4. User can view all submitted leads

This feature complements the automated lead generation capabilities by allowing manual entry of leads from other sources.

## Testing Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- pandas (for CSV processing)

### Database Setup
1. Create a PostgreSQL database named `lead_db`:
   ```
   createdb lead_db
   ```
2. Update the database connection string in `backend/config/config.py` if needed:
   ```python
   SQLALCHEMY_DATABASE_URI = 'postgresql://username@localhost:5432/lead_db'
   ```

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd LeadGen
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r backend/requirements.txt
   pip install pandas==1.3.3
   ```

### Running the Application
There are several ways to run the application:

1. Using Python module syntax (recommended):
   ```
   # From the project root directory
   python -m backend.wsgi
   ```

2. Using Flask directly:
   ```
   # Set the PYTHONPATH first
   # On Windows PowerShell:
   $env:PYTHONPATH = "."
   
   # On Windows Command Prompt:
   set PYTHONPATH=.
   
   # On Linux/Mac:
   export PYTHONPATH=.
   
   # Then run the application
   python backend/wsgi.py
   ```

3. Using Flask CLI:
   ```
   # Set the Flask application
   # On Windows PowerShell:
   $env:FLASK_APP = "backend/app.py"
   
   # On Windows Command Prompt:
   set FLASK_APP=backend/app.py
   
   # On Linux/Mac:
   export FLASK_APP=backend/app.py
   
   # Run Flask
   flask run --port 8000
   ```

### Docker Deployment
The application can be deployed using Docker:

1. Build the Docker image:
   ```
   docker build -t leadgen-app .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 leadgen-app
   ```

The application will be available at `http://localhost:8000`.

### Troubleshooting

#### Module Import Issues
If you encounter the error: `ImportError: attempted relative import with no known parent package`, this is typically due to Python's module resolution when using relative imports (imports starting with a dot `.`). Here are the solutions:

1. **Set PYTHONPATH** (Recommended for development):
   - The PYTHONPATH should point to your project root directory
   - This allows Python to correctly resolve relative imports
   ```
   # On Windows PowerShell:
   $env:PYTHONPATH = "."
   
   # On Windows Command Prompt:
   set PYTHONPATH=.
   
   # On Linux/Mac:
   export PYTHONPATH=.
   ```

2. **Use Python Module Syntax**:
   - Run the application as a module using the `-m` flag
   - This ensures proper package resolution
   ```
   python -m backend.wsgi
   ```

3. **Docker Environment**:
   - In Docker, the PYTHONPATH is automatically set in the Dockerfile:
   ```dockerfile
   ENV PYTHONPATH=/app
   ```
   - This is why the application runs without issues in Docker

#### Common Issues:
1. Make sure you're in the project root directory when running the application
2. Ensure your virtual environment is activated
3. Verify that all required packages are installed
4. Check that the database connection string is correct
5. Make sure PostgreSQL is running and accessible

For any other issues, please check the application logs or create an issue in the repository.

### CSV Upload Format
The CSV file should contain the following columns (column names can be mapped during upload):
- Name (required)
- Email (required)
- Phone (required)
- Company
- Website
- City
- State
- Title
- Industry
- Business Type
- Notes
