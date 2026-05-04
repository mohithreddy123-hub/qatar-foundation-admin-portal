# Qatar Foundation Admin Portal — Backend Implementation

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black?style=flat&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey?style=flat&logo=sqlite)
![Status](https://img.shields.io/badge/Status-Completed-success)

A secure, fully functional backend architecture built to power the Qatar Foundation Admin Portal UI. This project fulfills a strict internship assignment requiring a robust Python/Flask backend and seamless integration with an untouched frontend SPA (Single Page Application).

## 🎯 Project Overview
The objective was to implement user authentication and a complete **CRUD** (Create, Read, Update, Delete) system for managing "Opportunities". The core architectural constraint was **zero modification to the existing UI structure or CSS**. 

Instead of rewriting the frontend logic, a custom integration script (`backend_integration.js`) was engineered to gracefully hijack existing static DOM elements and redirect form submissions to strict, JSON-based REST APIs.

---

## 🚀 Key Features

### 1. Advanced Security & Authentication
* **PBKDF2-SHA256 Hashing:** Passwords are cryptographically hashed using `werkzeug.security` before database insertion.
* **Session Management:** Secure, `HttpOnly` cookie-based session tracking handled by `Flask-Login` with 'Remember Me' functionality.
* **Anti-Enumeration:** Registration and Password Reset endpoints return generic responses to prevent user-enumeration attacks.
* **CSRF Protection:** Enterprise-grade Cross-Site Request Forgery protection implemented via `Flask-WTF`, mandating strict `X-CSRFToken` verification for all mutating API requests (`POST`, `PUT`, `DELETE`).

### 2. Multi-Tenant Opportunity Management
* **Strict Tenant Isolation:** The backend utilizes an SQLAlchemy relational model where every opportunity is tied to its creator via a Foreign Key. Users can only view, edit, or delete their own data.
* **Dynamic CRUD:** Flawless REST APIs (`GET`, `POST`, `PUT`, `DELETE`) allow data to be managed dynamically without a single page refresh.

### 3. Non-Destructive UI Integration
* **Preserved Design:** Original `admin.html` and `admin.css` are entirely preserved.
* **DOM Interception:** The JS integration layer uses `cloneNode` techniques to bypass the original static mock logic and inject real asynchronous `fetch()` API calls seamlessly.

---

## 🛠️ Technology Stack
* **Core:** Python 3.8+
* **Web Framework:** Flask 3.0.3
* **Database & ORM:** SQLite, Flask-SQLAlchemy 3.1.1
* **Auth & Security:** Flask-Login, Flask-WTF, Werkzeug
* **Frontend Logic:** ES6 Vanilla JavaScript, Async/Await Fetch API

---

## ⚙️ Installation & Setup

If you wish to run this application locally, follow these steps:

### 1. Clone the repository
```bash
git clone https://github.com/mohithreddy123-hub/qatar-foundation-admin-portal.git
cd qatar-foundation-admin-portal
```

### 2. Set up a Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the `.env.example` file to create your own configuration:
```bash
cp .env.example .env
```

### 5. Run the Server
```bash
python app.py
```
*The database (`database.db`) will auto-generate in the `instance/` folder on first boot. The application will be live at `http://localhost:5000`.*

---

---

## 🏗️ Project Structure

This project follows a modular Flask architecture to ensure scalability and clean separation of concerns:

```text
├── app.py                  # Application Factory & app initialization
├── config.py               # Environment-specific configurations (Dev/Prod)
├── models.py               # SQLAlchemy Database Models (Admin & Opportunity)
├── wsgi.py                 # Production WSGI entry point for Render/Gunicorn
├── routes/                 # API Blueprint directory
│   ├── __init__.py         # Blueprint initialization
│   ├── auth_routes.py      # Authentication endpoints (Signup, Login, Forgot Pwd)
│   └── opportunity_routes.py # CRUD endpoints for Opportunity management
├── static/                 # Frontend Assets
│   ├── css/
│   │   └── admin.css       # Core styling (Original UI)
│   └── js/
│       ├── admin.js        # Original UI logic (Mock interactions)
│       └── backend_integration.js # Integration Bridge (The "Brain" that connects UI to API)
├── templates/              # HTML Templates
│   └── admin.html          # Main Single Page Application (SPA)
├── requirements.txt        # Python dependency list
├── .env.example            # Template for environment variables (Secret Key, DB URL)
├── test_api.py             # Automated test suite for backend verification
└── BACKEND_SUMMARY.txt     # Technical summary of the implementation
```

---

## 🛠️ Implementation Summary: What was Updated?

The transition from a **static mock frontend** to a **production-ready full-stack application** involved several critical updates:

1.  **Backend Core:** Built a robust Flask API using the Factory pattern to handle all business logic.
2.  **Database Integration:** Replaced the local JSON/variable-based storage in `admin.js` with a persistent **SQLite** database using SQLAlchemy.
3.  **Security Layer:** 
    *   Implemented password hashing using **PBKDF2-SHA256**.
    *   Added **CSRF Protection** to prevent cross-site attacks.
    *   Enforced **Secure Session Cookies** for user authentication.
4.  **Integration Bridge:** Developed `backend_integration.js` to intelligently override the original frontend behavior. It intercepts form submissions, strips the mock logic, and uses the `fetch()` API to communicate with our new Python backend.
5.  **Dynamic Rendering:** Updated the UI to render "Opportunity Cards" directly from the database, enabling real-time Add/Edit/Delete functionality without page reloads.

---

## 📡 API Routes

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | Register a new Admin account. |
| `POST` | `/api/auth/login` | Authenticate an Admin and set session cookies. |
| `POST` | `/api/auth/logout` | Destroy the active session. |
| `GET`  | `/api/auth/me` | Return the logged-in user's data. |
| `GET`  | `/api/auth/csrf-token` | Retrieve the required CSRF token for mutating requests. |
| `POST` | `/api/auth/forgot-password`| Generate a 1-hour expiration reset token. |
| `GET`  | `/api/opportunities` | Fetch all opportunities owned by the active Admin. |
| `POST` | `/api/opportunities` | Create a new opportunity. |
| `PUT`  | `/api/opportunities/<id>` | Edit a specific opportunity (ownership verified). |
| `DELETE`| `/api/opportunities/<id>` | Delete an opportunity (ownership verified). |

---

## 🧪 Testing
A complete API testing script (`test_api.py`) is included to verify the integrity of the auth flow, CSRF validation, and CRUD operations programmatically.
```bash
python test_api.py
```