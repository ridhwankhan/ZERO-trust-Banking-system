# Full Stack Application

Django + React (Vite) + PostgreSQL/SQLite

## Project Structure

```
.
├── backend/          # Django REST API
│   ├── apps/         # Application modules
│   │   ├── api/      # API routing
│   │   └── users/    # User model & endpoints
│   ├── core/         # Django settings
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/         # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
└── README.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Features

- **Backend**: Django + DRF with CORS enabled
- **Frontend**: React 18 + Vite + TypeScript
- **Database**: SQLite (default) or PostgreSQL
- **Auth**: JWT-based authentication with role-based access control
- **API**: RESTful endpoints with pagination

## Authentication

The system implements secure JWT-based authentication:

- **Password Hashing**: Django's PBKDF2 with SHA256 + salt (default)
- **Token Lifetime**: Access tokens expire after 30 minutes, refresh tokens after 7 days
- **Role-Based Access**: Admin and User roles with appropriate permissions

### Auth Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Obtain JWT tokens | No |
| POST | `/api/auth/logout/` | Blacklist refresh token | Yes |
| GET | `/api/auth/profile/` | Get current user profile | Yes |
| POST | `/api/auth/change-password/` | Change password | Yes |

### User Endpoints (Role-Based)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/users/` | List all users | Admin only |
| GET | `/api/users/{id}/` | Get specific user | Owner or Admin |
| PUT | `/api/users/{id}/` | Update user | Owner or Admin |
| DELETE | `/api/users/{id}/` | Delete user | Owner or Admin |
| GET | `/api/users/me/` | Current user details | Authenticated |

### Role Permissions

- **Admin**: Full access to all users, can list all users, manage any user account
- **User**: Can only view/update their own profile

## Environment Variables

### Backend (.env)
- `DEBUG` - Debug mode
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Allowed hosts
- `CORS_ALLOWED_ORIGINS` - Frontend URL (e.g., `http://localhost:5173`)

### Frontend (.env.local)
- `VITE_API_BASE_URL` - Backend API URL (e.g., `http://localhost:8000/api`)

## API Usage Example

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"securepass123","password_confirm":"securepass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass123"}'
```

### Access Protected Endpoint
```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/auth/profile/
```
