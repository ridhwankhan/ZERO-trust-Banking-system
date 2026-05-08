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

## 🧭 Comprehensive System Guide: Algorithms & Navigation

To provide full clarity on how the project functions internally and externally, here is a detailed breakdown of **which algorithms are used where**, and **how to navigate the entire system and its features**.

### 1. Which Algorithm is Where?

The system uses a combination of modern cryptographic algorithms to ensure Zero-Trust principles. All cryptographic logic is contained within the `backend/crypto/` directory.

*   **RSA-2048 (Asymmetric Encryption)**
    *   **Where it is:** `backend/crypto/rsa.py`
    *   **What it does:** Generates keypairs for users during registration. Used to encrypt sensitive User Profile data (Email, Username, Contact Info) and the transaction amounts in the payload before they are stored in the database.
*   **ECC - Elliptic Curve Cryptography (Asymmetric & Key Exchange)**
    *   **Where it is:** `backend/crypto/ecc.py`
    *   **What it does:** Generates ECC keypairs for users. Used for high-privacy transactions (ECDH Key Exchange) to encrypt metadata that only the sender and receiver can decrypt.
*   **HMAC-SHA256 (Message Authentication Code)**
    *   **Where it is:** `backend/crypto/hmac_custom.py`
    *   **What it does:** Ensures data integrity. Whenever a transaction (Deposit or Transfer) is created, an HMAC signature is generated using a server secret. This detects if anyone maliciously modifies the transaction amount directly in the database.
*   **SHA-256 Hash Chains (Tamper-Proof Ledger)**
    *   **Where it is:** `backend/apps/transactions/banking_views.py` (Transaction processing)
    *   **What it does:** Every transaction generates a SHA256 hash that includes the `previous_hash` of the sender's last transaction. This creates an unbreakable chain, simulating a blockchain ledger.
*   **TOTP (Time-Based One-Time Password for 2FA)**
    *   **Where it is:** `backend/crypto/totp.py`
    *   **What it does:** Generates the QR code provisioning URI and validates the 6-digit codes sent from the user's Google/Microsoft Authenticator app during login.

### 2. How to Navigate the Project (Routes & Roles)

The application has three distinct User Roles. Depending on the account you log into, the system navigates you to different Dashboards.

*   **Regular User Role**
    *   **Login URL:** `http://localhost:5174/login`
    *   **Main Navigation:** Navigates to `/dashboard`.
    *   **Permissions:** Can deposit funds, send money, view own transaction history, manage profile, and use 2FA.
*   **Admin Role**
    *   **Login URL:** `http://localhost:5174/login` (with Admin credentials: `admin@example.com` / `Admin@12345`)
    *   **Main Navigation:** Automatically redirects to `/admin-dashboard`.
    *   **Permissions:** Can view all users (encrypted), suspend/activate users, and monitor all transactions across the system without being able to decrypt the private details.
*   **Authority Role**
    *   **Login URL:** `http://localhost:5174/login` (with Authority credentials: `authority@example.com` / `Authority@12345`)
    *   **Main Navigation:** Automatically redirects to `/authority-dashboard`.
    *   **Permissions:** Responsible for verifying KYC (Know Your Customer) requests, approving user accounts, and issuing the cryptographic keys (RSA/ECC) upon approval.

### 3. How to Navigate Each Feature (Step-by-Step)

#### Feature 1: Registration & 2FA Setup
1. Go to `http://localhost:5174/register` to create a new User account.
2. The system will automatically log you in and take you to the User Dashboard.
3. To setup 2FA, navigate to your Profile (if implemented) or follow the prompts, scan the QR code with an Authenticator App, and enter the 6-digit code.

#### Feature 2: Deposit Funds (Fake Payment Gateway)
1. On the Dashboard, click the green **Deposit Funds** button.
2. Enter the amount you wish to deposit (e.g., `$500`).
3. Click "Continue to Payment".
4. Enter the test card details: 
   * Use **`4111-1111-1111-1111`** for a **Successful** payment.
   * Use **`4444-4444-4444-4444`** to test a **Declined** payment.
5. Provide any Expiry Date and CVV.
6. The backend processes this atomically, updates your ledger balance, and redirects you back to the Dashboard with your new balance.

#### Feature 3: Send Money (Transfers & Privacy Levels)
1. On the Dashboard, click the white **Send Money** button.
2. Select a recipient from the dropdown.
3. Enter the amount to send.
4. **Select a Privacy Level:**
   * **Standard:** Basic transaction metadata.
   * **Private Metadata:** Information is partially encrypted.
   * **High Privacy:** Utilizes ECC to fully encrypt the transaction payload.
5. Click transfer. The system validates the balance, encrypts the payload, signs it with HMAC, and hashes it before committing.

#### Feature 4: View Encrypted Transaction History
1. From the Dashboard, click **History** or the transparent History button.
2. You will see a list of Sent and Received transactions. 
3. The backend automatically decrypts the RSA/ECC payloads using your stored keys before serving them to your frontend, proving the end-to-end encryption works seamlessly.

---

**Built with ❤️ for secure, private banking in the digital age**
