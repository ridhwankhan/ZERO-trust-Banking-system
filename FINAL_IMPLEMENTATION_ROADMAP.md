# 🚀 Final Implementation Roadmap

This document outlines the exact, step-by-step roadmap to fulfill every missing requirement from the project rubric, while also adding "Wow" factors to ensure the highest possible grade.

---

## 🎯 1. Phase 1: Contact Info Encryption & Profile Management
*Fulfills rubric requirement: "user information (e.g., username, email, **contact info**) must be encrypted before storage... and view or update profiles"*

### Backend Implementation
*   **Model Update:** Add `contact_info` and `contact_info_encrypted` to the `User` model (`backend/apps/users/models.py`).
*   **Migrations:** Run `makemigrations` and `migrate` to update the database schema.
*   **Registration API:** Update the `RegisterSerializer` to accept the new `contact_info` field, encrypt it using RSA, and store it.
*   **Profile API:** Create a `PATCH /api/auth/profile/` endpoint allowing users to update their username, email, and contact info (handling re-encryption on every update).

### Frontend Implementation
*   **Registration Form:** Add a required "Contact Info" (Phone Number/Address) field to `Register.tsx`.
*   **Profile Page (`Profile.tsx`):** Create a secure page where users can:
    *   View their decrypted personal details.
    *   Edit their details and submit updates to the backend.

---

## 🔐 2. Phase 2: Complete 2FA Frontend UI Integration
*Fulfills rubric requirement: "A verification function must enforce two-step authentication"*

### Frontend Implementation (Connecting the existing backend)
*   **2FA Setup UI:** On the `Profile.tsx` page, add a "Security" section.
    *   Add an "Enable 2FA" button.
    *   When clicked, fetch the QR Code URI from the backend (`/api/auth/2fa/setup/`).
    *   Use a React QR Code library to display the code on the screen.
    *   Provide an input field for the user to scan the code with their phone and type the 6-digit TOTP code to verify.
*   **2FA Login Flow (`Login.tsx`):**
    *   Modify the login process. If the user successfully enters their password but has 2FA enabled, intercept the login.
    *   Show a secondary screen: *"Please enter the 6-digit code from your Authenticator App"*.
    *   Send the code to `/api/auth/2fa/verify/` to complete the login and receive the JWT tokens.

---

## 📝 3. Phase 3: Encrypted Posts / Community Module
*Fulfills rubric requirement: "Users must be able to create, view, and edit posts... with all data automatically encrypted"*

### Backend Implementation
*   **Post Model:** Create a `Post` model in `backend/apps/transactions/models.py` (or a new app).
    *   Fields: `id`, `author` (ForeignKey to User), `title_encrypted`, `content_encrypted`, `created_at`, `updated_at`.
*   **Encryption Logic:** When saving a Post, encrypt the `title` and `content` using the author's public key (RSA or ECC) before it touches the database.
*   **API ViewSet:** Create `/api/posts/` to handle creating, viewing, editing, and deleting posts. Ensure the backend decrypts the data before sending it to the frontend, or sends it encrypted for the frontend to decrypt (depending on the chosen key architecture).

### Frontend Implementation
*   **Community Feed (`Posts.tsx`):** A beautiful, scrolling feed showing all posts.
*   **Post Editor (`CreatePost.tsx`):** A modal or separate page to write new posts.
*   **Edit/Delete Controls:** Buttons on the posts allowing the original author to edit or delete their content.

---

## ✨ 4. Phase 4: "Wow" Factors (To Ensure Top Marks)
*These features aren't strictly required by the rubric, but they visualize the complex security happening behind the scenes. Teachers love seeing the invisible made visible.*

*   **Cryptography Visualizer Widget:** Add a small panel on the User Dashboard that says "Current Security Status". 
    *   It will display exactly which encryption algorithm was used for their last transaction (RSA vs ECC).
    *   It will show a "Data Integrity: HMAC-SHA256 Valid" badge.
*   **Encrypted Data Toggle:** On the `Profile.tsx` and `Posts.tsx` pages, add a toggle switch labeled *"View Raw Database Data"*. 
    *   When turned ON, the screen changes to show the raw, unreadable encrypted ciphertext (e.g., `Jhd8923hjn...`) that is actually stored in the database.
    *   When turned OFF, it visually "decrypts" back into readable text. This completely proves to the teacher that the encryption requirement is working perfectly.
*   **Admin Audit Log UI:** Enhance the Admin Dashboard to show a live scrolling feed of all cryptographic actions (e.g., "User A generated RSA keypair", "User B performed AES-encrypted transaction", "User C enabled TOTP").

---

## 🏁 How to Execute This Roadmap

We can tackle this systematically:
1.  **First:** I will execute Phase 1 and Phase 2 together. We will get the Profile page up, encrypt the contact info, and make the 2FA QR code show up on screen.
2.  **Second:** We will test it. You can pull out your phone, scan the QR code, and verify it works.
3.  **Third:** I will build Phase 3 (The Posts feed).
4.  **Fourth:** We will add the Phase 4 visualizers to make the project visually stunning.
