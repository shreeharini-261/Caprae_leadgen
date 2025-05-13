import requests
import json

# Replace with your actual server URL and authentication details
BASE_URL = "http://127.0.0.1:8000"  # Change to your actual server URL
API_ENDPOINT = f"{BASE_URL}/api/upload_leads"

# Sample data for lead upload - format must match database fields
sample_leads = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "Doe.doe@example.com",
        "phone": "9804892245",
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
        "email": "Smith.smith@example.com", 
        "phone": "9804892345",
        "company": "XYZ Inc",
        "title": "CTO",
        "industry": "Finance",
        "website": "https://www.xyz.com",
        "city": "San Francisco",
        "state": "CA"
    }
]

def login_and_get_session_cookie(username, password):
    """
    Login to the system and get session cookie
    
    Args:
        username: Username for login
        password: Password for login
    
    Returns:
        Session cookie if login successful, None otherwise
    """
    login_url = f"{BASE_URL}/login"
    
    # Send login request
    session = requests.Session()
    login_data = {
        "username": username,
        "password": password
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code == 200:
        # Return the session cookie
        return session.cookies.get_dict()
    else:
        print(f"Login failed: {response.status_code}")
        return None

def upload_leads(leads_data, session_cookie=None):
    """
    Upload leads to the system via API
    
    Args:
        leads_data: List of lead dictionaries
        session_cookie: Session cookie for authentication
    
    Returns:
        Response from the API
    """
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Make the request to the API with session cookie
    if session_cookie:
        cookies = session_cookie
    else:
        cookies = {}
    
    response = requests.post(
        API_ENDPOINT,
        headers=headers,
        json=leads_data,
        cookies=cookies
    )
    
    return response

if __name__ == "__main__":
    # Replace with your actual credentials
    username = "developer"  # Update with your actual username
    password = "developer123"  # Update with your actual password
    
    # Option 1: Login first to get session cookie
    print("Attempting to login and get session cookie...")
    session_cookie = login_and_get_session_cookie(username, password)
    
    if session_cookie:
        print(f"Login successful, got session cookie: {session_cookie}")
        # Upload leads with the session cookie
        print("Uploading leads with session cookie...")
        response = upload_leads(sample_leads, session_cookie)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text}")
        
        # Try to parse JSON if possible
        try:
            json_response = response.json()
            print(f"JSON Response: {json_response}")
        except Exception as e:
            print(f"Could not parse JSON: {e}")
    else:
        print("Login failed, could not get session cookie")
    
    # Option 2: Using session cookie directly (if you have it)
    # Uncomment and update this if you want to try with a manual cookie
    """
    print("\nTrying with manual session cookie...")
    manual_session_cookie = {"session": "eyJfZnJlc2giOmZhbHNlfQ.aBYgkA.JJzpcxBl4qxKsjfXDSXURI2Yre8"}
    
    # Upload leads with manual session cookie
    response = upload_leads(sample_leads, manual_session_cookie)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Text: {response.text}")
    
    # Try to parse JSON if possible
    try:
        json_response = response.json()
        print(f"JSON Response: {json_response}")
    except Exception as e:
        print(f"Could not parse JSON: {e}")
    """
    
    # The API will return a JSON response with the status and stats:
    # {
    #   "status": "success",
    #   "message": "Upload Complete! Added: 2, Skipped: 0, Errors: 0",
    #   "stats": {
    #     "added": 2,
    #     "skipped_duplicates": 0,
    #     "errors": 0
    #   }
    # } 