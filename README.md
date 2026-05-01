# 🔐 ZERO Trust Banking System

A comprehensive, secure banking platform built with zero-trust principles, featuring advanced cryptography, role-based access control, and tamper-proof transaction integrity.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Security Features](#security-features)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This is a full-stack banking application that implements enterprise-grade security features including:

- **RSA-2048 + ECC Encryption** for all transactions
- **HMAC-SHA256** integrity verification
- **Role-Based Access Control** (User, Admin, Authority)
- **Tamper-proof transaction chains** with hash linking
- **JWT-based authentication** with secure token management
- **Real-time balance updates** with atomic transactions

## ✨ Features

### 🔐 Security & Authentication
- JWT-based authentication with access/refresh tokens
- Role-based access control (User, Admin, Authority)
- Two-factor authentication (TOTP) setup and login verification
- Secure password hashing with PBKDF2
- Session management with automatic logout
- Profile encryption for email, username, and contact info

### 💰 Banking Features
- **Deposit System** with fake payment gateway simulation
- **Money Transfers** between users with privacy levels
- **Transaction History** with advanced filtering
- **Real-time Balance Updates**
- **Admin Dashboard** for user management
- **Authority Panel** for compliance oversight

### 📝 Encrypted Posts Module
- Create/read/update/delete posts via `/api/posts/`
- Post title and content are encrypted with RSA before database storage
- Feed responses expose decrypted content when key material is available
- Author-only controls for edit/delete in frontend feed

### 🔒 Privacy Levels
- **Standard**: Basic transaction visibility
- **Private Metadata**: Hidden transaction details
- **High Privacy**: Maximum encryption and anonymity

### 📊 Dashboard & Analytics
- Real-time balance display
- Transaction statistics (sent/received/total)
- Privacy level filtering
- Responsive design for all devices

## 🛠 Tech Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **SQLite/MySQL** - Database
- **JWT** - Authentication
- **RSA/ECC** - Cryptographic operations
- **HMAC-SHA256** - Integrity verification

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **Axios** - HTTP client

### Security Libraries
- **cryptography** - RSA/ECC operations
- **hashlib** - HMAC and hashing
- **secrets** - Secure random generation

## 🔒 Security Features

### Cryptographic Security
- **RSA-2048** key pairs for user authentication
- **ECC (Elliptic Curve)** for high-privacy transactions
- **HMAC-SHA256** for transaction integrity
- **SHA256 hash chains** for tamper detection

### Authentication & Authorization
- **JWT tokens** with expiration and refresh
- **Role-based permissions** (User/Admin/Authority)
- **Password complexity requirements**
- **Session timeout and automatic logout**

### Transaction Security
- **Atomic transactions** with rollback on failure
- **Encrypted payload storage**
- **Transaction hash verification**
- **Privacy level enforcement**

## 📁 Project Structure

```
CSE447/
├── README.md
├── backend/                          # Django Backend
│   ├── manage.py
│   ├── core/                         # Django Settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/                         # Application Modules
│   │   ├── api/                      # Main API routing
│   │   ├── users/                    # User management
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   └── permissions.py
│   │   ├── transactions/             # Banking operations
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── banking_views.py
│   │   │   ├── serializers.py
│   │   │   └── urls.py
│   │   ├── audit/                    # Audit logging
│   │   └── auth/                     # Authentication
│   ├── crypto/                       # Cryptographic utilities
│   │   ├── ecc.py
│   │   ├── rsa.py
│   │   ├── hmac_custom.py
│   │   └── unified_encryption.py
│   ├── requirements.txt
│   └── db.sqlite3
│
├── frontend/                         # React Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/               # Reusable components
│   │   ├── pages/                    # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Deposit.tsx
│   │   │   ├── SendMoney.tsx
│   │   │   ├── TransactionHistory.tsx
│   │   │   ├── AdminDashboard.tsx
│   │   │   └── AuthorityDashboard.tsx
│   │   ├── services/                 # API services
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── diagram/                          # System diagrams
```

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **npm or yarn**
- **Git**

### Backend Setup

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Database setup:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Initialize balances (optional):**
   ```bash
   python manage.py initialize_balances
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment configuration:**
   ```bash
   cp .env.example .env.local
   # The default VITE_API_BASE_URL=/api should work with Vite proxy
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

### Environment Variables

#### Backend (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5174,http://127.0.0.1:5174
```

#### Frontend (.env.local)
```env
VITE_API_BASE_URL=/api
```

## 📖 Usage Guide

### User Registration & Login

1. **Register**: Visit `http://localhost:5174` and click "Register"
2. **Login**: Use your credentials to access the dashboard
3. **RSA/ECC Keys**: Automatically generated during registration

### Banking Operations

#### Making a Deposit
1. Click "Deposit" on dashboard
2. Enter amount
3. Use test card: `4111-1111-1111-1111` (success) or `4444-4444-4444-4444` (decline)
4. Complete payment to credit your account

#### Sending Money
1. Click "Send Money" on dashboard
2. Select recipient and amount
3. Choose privacy level
4. Confirm transaction

#### Viewing History
1. Click "History" or "View All" on dashboard
2. Filter by type (all/sent/received)
3. Filter by privacy level
4. Expand transactions for details

### Admin Features

#### Admin Dashboard (`/admin-login`)
- View all users and their balances
- Manage user accounts
- Access audit logs
- Override transactions if needed

#### Authority Dashboard (`/authority-login`)
- Compliance monitoring
- Transaction verification
- Security oversight
- Regulatory reporting

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | ❌ |
| POST | `/api/auth/login/` | Obtain JWT tokens | ❌ |
| POST | `/api/auth/logout/` | Blacklist refresh token | ✅ |
| GET | `/api/auth/profile/` | Get current user profile | ✅ |
| GET/POST | `/api/auth/2fa/setup/` | Create TOTP setup and enable 2FA | ✅ |
| POST | `/api/auth/2fa/verify/` | Verify 2FA code for login | ❌ |

### Banking Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/transactions/balance/` | Get user balance | ✅ |
| POST | `/api/transactions/deposit/initiate/` | Start deposit | ✅ |
| POST | `/api/transactions/deposit/process/` | Process deposit | ✅ |
| POST | `/api/transactions/create/` | Send money | ✅ |
| GET | `/api/transactions/history/` | Transaction history | ✅ |
| GET | `/api/transactions/{id}/` | Transaction details | ✅ |

### Posts Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/posts/` | List encrypted posts (decrypted in response when available) | ✅ |
| POST | `/api/posts/` | Create encrypted post | ✅ |
| PUT | `/api/posts/{id}/` | Update own encrypted post | ✅ |
| DELETE | `/api/posts/{id}/` | Delete own post | ✅ |

### Admin Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/users/` | List all users | Admin |
| GET | `/api/transactions/admin/all/` | All transactions | Admin |
| GET | `/api/audit/logs/` | Audit logs | Admin |

### Request/Response Examples

#### Register User
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!"
}
```

#### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Verify 2FA Login
```bash
POST /api/auth/2fa/verify/
Content-Type: application/json

{
  "user_id": 1,
  "token": "123456"
}
```

#### Create Encrypted Post
```bash
POST /api/posts/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Release Notes",
  "content": "Phase 1 is now live."
}
```

#### Create Transaction
```bash
POST /api/transactions/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "receiver_id": 2,
  "amount": "100.00",
  "privacy_level": "standard",
  "description": "Payment for services"
}
```

## 🗄 Database Schema

### Users Table
```sql
CREATE TABLE users_user (
    id INTEGER PRIMARY KEY,
    email VARCHAR(254) UNIQUE,
    username VARCHAR(150) UNIQUE,
    password VARCHAR(128),
    role VARCHAR(20) DEFAULT 'user',
    balance DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    rsa_public_key TEXT,
    rsa_encrypted_private_key TEXT,
    ecc_public_key TEXT,
    ecc_encrypted_private_key TEXT
);
```

### Transactions Table
```sql
CREATE TABLE transactions_transaction (
    id INTEGER PRIMARY KEY,
    transaction_type VARCHAR(20),
    status VARCHAR(20),
    sender_id INTEGER REFERENCES users_user(id),
    receiver_id INTEGER REFERENCES users_user(id),
    amount DECIMAL(15,2),
    privacy_level VARCHAR(20),
    encrypted_payload TEXT,
    hmac_signature VARCHAR(64),
    transaction_hash VARCHAR(64),
    previous_hash VARCHAR(64),
    created_at DATETIME
);
```

### Ledger Table
```sql
CREATE TABLE transactions_ledger (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users_user(id) UNIQUE,
    balance DECIMAL(15,2) DEFAULT 0.00,
    last_updated DATETIME
);
```

## 🧪 Testing

### Test Accounts

| Email | Password | Role | Balance |
|-------|----------|------|---------|
| `admin@example.com` | `Admin@12345` | Admin | $1,000,000 |
| `authority@example.com` | `Authority@12345` | Authority | $500,000 |
| `user@example.com` | `User@12345` | User | $1,000 |

### Test Cards (Deposit)

| Card Number | Result |
|-------------|--------|
| `4111-1111-1111-1111` | ✅ Success |
| `4444-4444-4444-4444` | ❌ Declined |

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables:**
   ```env
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=postgresql://user:pass@host:port/db
   ALLOWED_HOSTS=yourdomain.com
   CORS_ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Build Frontend:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Collect Static Files:**
   ```bash
   cd backend
   python manage.py collectstatic
   ```

4. **Use Production Server:**
   ```bash
   # Gunicorn for Django
   gunicorn core.wsgi:application --bind 0.0.0.0:8000

   # Nginx for static files
   # Serve built frontend from /static/
   ```

### Docker Deployment

```dockerfile
# Dockerfile for backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests:**
   ```bash
   # Backend
   cd backend && python manage.py test

   # Frontend
   cd frontend && npm test
   ```
5. **Commit your changes:**
   ```bash
   git commit -m "Add your feature description"
   ```
6. **Push to the branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Code Style

- **Backend**: Follow PEP 8
- **Frontend**: Use ESLint and Prettier
- **Commits**: Use conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation for common solutions

## 🔄 Version History

- **v1.0.0** - Initial release with core banking features
- **v1.1.0** - Added advanced privacy levels
- **v1.2.0** - Enhanced security with ECC encryption
- **v1.3.0** - Added admin and authority dashboards

---

**Built with ❤️ for secure, private banking in the digital age**
