# Complete Scraping Integration Guide

This document provides comprehensive instructions for the scraping team to integrate with our lead database system using our JSON API.

## Table of Contents

1. [Introduction](#introduction)
2. [API Integration](#api-integration)
3. [Data Field Reference](#data-field-reference)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [FAQ](#faq)

## Introduction

This integration guide helps the scraping team to upload leads directly to our database using our JSON API. This method enables real-time or scheduled automated uploads with comprehensive validation and error handling.

## API Integration

### API Endpoint

```
POST /api/upload_leads
```

### Authentication

The endpoint requires session cookie authentication. There are two ways to authenticate:

#### Option 1: Programmatic Login

1. Send a POST request to the login endpoint:
   ```
   POST /login
   ```
   
   With form data:
   ```
   username=your_username&password=your_password
   ```

2. The server will respond with a session cookie to include in subsequent requests.

#### Option 2: Manual Cookie

If you already have a valid session cookie (from browser login), you can use it directly:

```
Cookie: session=your_session_cookie_value
```

### Request Format

Send a POST request with JSON data containing an array of lead objects. Each object must include:

- `email` (required)
- `phone` (required)

Other fields will be mapped directly to database fields.

### Example API Request

```json
[
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "1234567890",
    "company": "ABC Corp",
    "title": "CEO",
    "industry": "Technology",
    "website": "https://www.example.com",
    "city": "New York",
    "state": "NY"
  },
  {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com", 
    "phone": "0987654321",
    "company": "XYZ Inc",
    "title": "CTO",
    "industry": "Finance",
    "website": "https://www.xyz.com",
    "city": "San Francisco",
    "state": "CA"
  }
]
```

### Example API Implementation

```python
import requests
import json

# Configuration
BASE_URL = "https://your-domain.com"  # Replace with actual server URL
LOGIN_URL = f"{BASE_URL}/login"
API_ENDPOINT = f"{BASE_URL}/api/upload_leads"

# Credentials
USERNAME = "scraping_team"  # Replace with provided username
PASSWORD = "your_password"  # Replace with provided password

def login_and_get_session():
    """Login and get session object"""
    session = requests.Session()
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = session.post(LOGIN_URL, data=login_data)
    
    if response.status_code == 200:
        print("Login successful")
        return session
    else:
        print(f"Login failed: {response.status_code}")
        return None

def upload_leads(session, leads_data):
    """Upload lead data using an authenticated session"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = session.post(
        API_ENDPOINT,
        headers=headers,
        json=leads_data
    )
    
    return response

# Main execution
if __name__ == "__main__":
    # Sample leads
    leads = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "company": "ABC Corp",
            "title": "CEO"
        }
    ]
    
    # 1. Login and get session
    session = login_and_get_session()
    
    if session:
        # 2. Upload leads with session
        response = upload_leads(session, leads)
        
        # 3. Process response
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Added: {result['stats']['added']}, "
                  f"Skipped: {result['stats']['skipped_duplicates']}, "
                  f"Errors: {result['stats']['errors']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
```

## Data Field Reference

The following fields can be included in your JSON API uploads:

| Field Name | Description | Required | Example |
|------------|-------------|----------|---------|
| first_name | First name of contact | No | John |
| last_name | Last name of contact | No | Doe |
| email | Email address | Yes | john.doe@example.com |
| phone | Phone number | Yes | 1234567890 |
| company | Company name | No | ABC Corp |
| city | City | No | New York |
| state | State/Province | No | NY |
| website | Website URL | No | https://example.com |
| linkedin_url | LinkedIn profile URL | No | https://linkedin.com/in/johndoe |
| industry | Industry type | No | Technology |
| revenue | Revenue range | No | 10M-50M |
| product_service_category | Product/Service category | No | SaaS |
| business_type | Business type | No | B2B |
| associated_members | Associated members | No | Jane Smith, Tom Brown |
| employees_range | Number of employees | No | 50-100 |
| rev_source | Revenue source | No | Subscriptions |
| year_founded | Year founded | No | 2010 |
| title | Job title | No | CEO |
| owner_linkedin | Owner's LinkedIn | No | https://linkedin.com/in/owner |
| owner_age | Owner's age | No | 45 |
| additional_notes | Additional notes | No | Interested in AI solutions |
| score | Lead score | No | A |
| reasoning | Score reasoning | No | High match for target profile |
| status | Lead status | No | new |

## Error Handling

### Common API Errors

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 400 | Bad Request - Invalid data format | Check JSON structure and required fields |
| 401 | Unauthorized | Re-authenticate (session expired) |
| 500 | Server Error | Contact technical team |

## Best Practices

### For API Integration

1. **Batch Processing**:
   - Send data in batches of 30-50 leads
   - Include delay between batches (1-2 seconds)

2. **Error Handling**:
   - Implement retry logic for transient errors
   - Log failures for later analysis

3. **Validation**:
   - Validate email and phone formats before sending
   - Check for duplicates in your own system first

4. **Automation**:
   - Implement a scheduled job for regular uploads
   - Use cron jobs or task schedulers for automated execution

### Example Automation Script

```python
import requests
import json
import schedule
import time
from datetime import datetime

def scrape_leads():
    """Your lead scraping function"""
    # Implement your scraping logic here
    return [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "company": "ABC Corp"
        }
    ]

def upload_leads_job():
    """Job to upload leads"""
    print(f"[{datetime.now()}] Starting scheduled lead upload")
    
    # 1. Login to get session
    session = login_and_get_session()
    if not session:
        print("Login failed, aborting")
        return
    
    # 2. Scrape leads
    leads = scrape_leads()
    if not leads:
        print("No leads to upload")
        return
    
    print(f"Found {len(leads)} leads to upload")
    
    # 3. Process in batches
    batch_size = 50
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        try:
            response = upload_leads(session, batch)
            if response.status_code == 200:
                result = response.json()
                print(f"Batch {i//batch_size + 1} success! "
                      f"Added: {result['stats']['added']}, "
                      f"Skipped: {result['stats']['skipped_duplicates']}, "
                      f"Errors: {result['stats']['errors']}")
            else:
                print(f"Batch {i//batch_size + 1} error: {response.status_code}")
        except Exception as e:
            print(f"Error uploading batch {i//batch_size + 1}: {str(e)}")
        
        # Add delay between batches
        if i + batch_size < len(leads):
            time.sleep(2)

# Schedule job to run daily
schedule.every().day.at("02:00").do(upload_leads_job)

if __name__ == "__main__":
    print("Starting lead upload scheduler")
    # Run once immediately
    upload_leads_job()
    
    # Then run on schedule
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## FAQ

**Q: How do I know if a lead was already in the database?**
A: Leads with matching email or phone numbers will be skipped and counted as "skipped_duplicates" in the response.

**Q: How many leads can I upload at once?**
A: We recommend batches of 50 leads per API call to optimize performance.

**Q: What happens if the upload is interrupted?**
A: The system processes leads in batches, so only the current batch will be affected. You can resume from the next batch.

**Q: How can I convert my existing CSV workflow to use the API?**
A: You can create a simple script that reads your CSV file and formats the data as JSON to send to the API.

**Q: How long does the session cookie last?**
A: Sessions typically last for several hours, but it's recommended to reauthenticate before large upload operations.

**Q: How can I validate the data before sending it?**
A: You should validate that emails are in a proper format (user@domain.com) and phone numbers contain only digits, with a reasonable length (8+ digits).

---

For any additional questions or support, please contact the development team at devteam@company.com. 