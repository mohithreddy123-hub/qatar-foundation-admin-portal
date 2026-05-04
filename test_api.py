import requests
import sys

BASE_URL = "http://localhost:5000/api"

print("--- Testing API ---")

# 1. Login
try:
    session = requests.Session()
    # Get CSRF token
    res = session.get(f"{BASE_URL}/auth/csrf-token")
    csrf_token = res.json()["csrf_token"]
    session.headers.update({"X-CSRFToken": csrf_token})

    res = session.post(f"{BASE_URL}/auth/login", json={"email": "admin@qf.org.qa", "password": "Admin@123"})
    print(f"Login Response: {res.status_code} {res.text}")
except Exception as e:
    print("Login error:", e)

# 2. Get Me
try:
    res = session.get(f"{BASE_URL}/auth/me")
    print(f"Me Response: {res.status_code} {res.text}")
except Exception as e:
    print("Me error:", e)

# 3. Create Opportunity
opp_data = {
    "opportunity_name": "Full Stack Dev",
    "duration": "3 months",
    "start_date": "2025-06-01",
    "description": "Learn full-stack development",
    "skills_to_gain": "Python,Flask,React",
    "category": "technology",
    "future_opportunities": "Senior Developer",
    "max_applicants": "50"
}
try:
    res = session.post(f"{BASE_URL}/opportunities", json=opp_data)
    print(f"Create Opp Response: {res.status_code} {res.text}")
    if res.status_code == 201:
        opp_id = res.json()["opportunity"]["id"]
    else:
        opp_id = None
except Exception as e:
    print("Create Opp error:", e)

# 4. List Opportunities
try:
    res = session.get(f"{BASE_URL}/opportunities")
    print(f"List Opps Response: {res.status_code} {res.text}")
except Exception as e:
    print("List Opps error:", e)

# 5. Forgot Password
try:
    s2 = requests.Session()
    res = s2.get(f"{BASE_URL}/auth/csrf-token")
    s2.headers.update({"X-CSRFToken": res.json()["csrf_token"]})
    res = s2.post(f"{BASE_URL}/auth/forgot-password", json={"email": "admin@qf.org.qa"})
    print(f"Forgot Password Response: {res.status_code} {res.text}")
except Exception as e:
    print("Forgot Password error:", e)
