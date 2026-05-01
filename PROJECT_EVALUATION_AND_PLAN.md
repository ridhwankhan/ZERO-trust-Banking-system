# 📊 Project Evaluation & Implementation Plan

**Date:** April 30, 2026
**Project:** CSE447 Lab Project - Secure System
**Status:** Partial Completion (Banking features implemented; Profile & Posts missing)

---

## 🟢 1. Implemented Features (What's Been Done)

The system currently functions as a secure, zero-trust banking system with advanced cryptography. Below is a detailed breakdown of what has been successfully completed, where the code resides, and how to navigate it in the UI.

### 🔐 User Authentication & Role-Based Access Control (RBAC)
*   **What it does:** Users can register, log in, and are assigned roles (User, Admin, Authority). Sessions are managed securely using JSON Web Tokens (JWT).
*   **Backend Files:** 
    *   `backend/apps/users/models.py` (Defines User model with roles)
    *   `backend/apps/users/auth_views.py` (Login/Register APIs)
*   **Frontend Files:** 
    *   `frontend/src/pages/Login.tsx`
    *   `frontend/src/pages/Register.tsx`
*   **UI Navigation:** 
    *   Regular users: Navigate to `http://localhost:5174/login` or `/register`.
    *   Admins: Navigate to `/admin-login` (Access to Admin Dashboard).
    *   Authority: Navigate to `/authority-login` (Access to Authority Dashboard).

### 📱 Two-Step Authentication (2FA)
*   **What it does:** Enforces TOTP-based 2FA as required by the verification function to validate both primary credentials and a second factor.
*   **Backend Files:** 
    *   `backend/crypto/totp.py` (Handles TOTP secret generation and validation)
    *   `backend/apps/users/models.py` (Contains 2FA fields)

### 🔑 Data Encryption & Key Management (Partial)
*   **What it does:** Implements **at least two asymmetric algorithms** (RSA and ECC) for encrypting sensitive data (like email and username) before storage, and decrypting it on retrieval. Also includes a key management module for generating and rotating keys.
*   **Backend Files:** 
    *   `backend/crypto/rsa.py` (RSA encryption logic)
    *   `backend/crypto/ecc.py` (ECC encryption logic)
    *   `backend/crypto/key_management.py` (Key rotation and cache)

### 🛡️ Integrity Verification (MAC)
*   **What it does:** Uses Message Authentication Codes (HMAC-SHA256) to verify data integrity for banking transactions and detect unauthorized modifications.
*   **Backend Files:** 
    *   `backend/crypto/hmac_custom.py`

### 💰 Banking System (Deposits & Transfers)
*   **What it does:** Users can deposit simulated funds and securely transfer them to other users using different privacy levels.
*   **Backend Files:** 
    *   `backend/apps/transactions/banking_views.py`
*   **Frontend Files:** 
    *   `frontend/src/pages/Deposit.tsx`
    *   `frontend/src/pages/SendMoney.tsx`
*   **UI Navigation:** Log in as a User, go to the Dashboard (`/dashboard`), and click "Deposit Funds" or "Send Money".

---

## 🔴 2. Missing Features (What's NOT Been Done)

Based on the project requirement rubric, the following features are completely missing from the current implementation and must be added to achieve full marks:

### 1. Contact Info Encryption
*   **Requirement:** *"...all user information (e.g., username, email, **contact info**) must be encrypted before storage..."*
*   **Current State:** While the email and username are encrypted, the system does not collect, store, or encrypt any "contact info" (e.g., phone number, physical address) during registration.

### 2. View or Update Profiles
*   **Requirement:** *"...and **view or update profiles**..."*
*   **Current State:** There is a user dashboard, but there is no dedicated profile management page where users can view their decrypted profile data and securely update it.

### 3. Create, View, and Edit Posts
*   **Requirement:** *"Users must be able to **create, view, and edit posts**... with all data automatically encrypted before storage and decrypted on retrieval."*
*   **Current State:** The system is strictly a banking ledger. There is no "Posts" or "Feeds" module, which is a core requirement of the lab project.

---

## 📋 3. Action Plan (Next Steps)

To fully fulfill the whole process and complete the project, we need to execute the following steps in order:

### Phase 1: Implement Contact Info & Profile Updates
**Backend Tasks:**
1.  Add `contact_info` and `contact_info_encrypted` fields to the `User` model in `backend/apps/users/models.py`.
2.  Generate and apply database migrations.
3.  Update the `RegisterSerializer` to accept the new contact info and encrypt it using the existing RSA/ECC utilities before saving.
4.  Create a new API view (`PATCH /api/auth/profile/`) to handle updating the user's information securely.

**Frontend Tasks:**
1.  Update the registration form (`frontend/src/pages/Register.tsx`) to include a "Contact Info" input field.
2.  Create a new `Profile.tsx` page where users can view their current information and submit updates.
3.  Add `/profile` to the React Router (`App.tsx`) and add a navigation link in the user Dashboard.

### Phase 2: Implement Encrypted Posts Module
**Backend Tasks:**
1.  Create a new `Post` model in the backend (either in the existing transactions app or a new `community` app).
    *   Fields: `id`, `author` (ForeignKey to User), `title_encrypted`, `content_encrypted`, `created_at`.
2.  Create an API ViewSet (`/api/posts/`) to handle CRUD operations (Create, Read, Update, Delete).
3.  Implement encryption logic: When a post is created or edited, the `title` and `content` must be encrypted using the author's public key before touching the database.
4.  Implement decryption logic: When posts are fetched, the server (or frontend, depending on the architecture choice) must decrypt the text.

**Frontend Tasks:**
1.  Create a `Posts.tsx` page to display a list/feed of posts.
2.  Create a `CreatePost.tsx` component (or a modal window) to write and publish new posts.
3.  Add UI buttons to edit or delete posts belonging to the logged-in user.
4.  Link the Posts page to the main navigation menu.
