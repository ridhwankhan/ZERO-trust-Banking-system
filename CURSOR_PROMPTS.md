# 🤖 Cursor AI Agent Prompts

Copy and paste these prompts one by one into the **Cursor AI Composer (Ctrl+I or Cmd+I)** or the **Cursor Chat**. Wait for the agent to finish implementing and testing each prompt before moving to the next one.

These prompts are heavily engineered to guide the AI to build a "Final Year Showcase" level project.

---

## 📌 Prompt 1: Contact Info & Profile Management (Phase 1)
**Copy this:**
```text
I need to implement Phase 1 of my secure banking project: Contact Info Encryption and Profile Management. 

1. BACKEND: Open `backend/apps/users/models.py` and add `contact_info` and `contact_info_encrypted` fields to the `User` model. Run `python manage.py makemigrations` and `migrate`.
2. BACKEND: Open the registration serializers/views. Update it so that when a user registers, their `contact_info` is encrypted using the existing RSA encryption utilities before saving to the database.
3. BACKEND: Create a `PATCH /api/auth/profile/` endpoint allowing a user to update their email, username, and contact info. Ensure the updated data is re-encrypted before saving.
4. FRONTEND: Update `frontend/src/pages/Register.tsx` to include a required "Contact Info" (Phone/Address) text field.
5. FRONTEND: Create a beautiful, modern `Profile.tsx` page using Tailwind/CSS. It should allow the user to view their decrypted details and edit them. Add it to `App.tsx` routing and the dashboard navigation.
Ensure the design looks premium, like a real-world fintech app.
```

---

## 📌 Prompt 2: 2FA Frontend Integration (Phase 2)
**Copy this:**
```text
I need to connect my existing backend 2FA logic to the frontend UI. The backend endpoints in `backend/apps/users/two_factor_views.py` are already complete (`setup/`, `enable/`, `verify/`).

1. PROFILE UI: On the `Profile.tsx` page, add a "Security Settings" section. Add an "Enable 2FA" button. 
2. 2FA SETUP: When clicked, call `/api/auth/2fa/setup/`. Install `qrcode.react` (npm install qrcode.react) and use it to display the `provisioning_uri` as a QR code on screen. Provide a 6-digit text input for the user to verify the setup by calling the enable endpoint.
3. LOGIN UI: Modify `frontend/src/pages/Login.tsx`. If the user successfully enters their email and password, check the response to see if `two_factor_enabled` is true. If it is, do NOT log them in yet. Instead, display a sleek secondary screen asking for their "6-digit Authenticator Code". Send this code to `/api/auth/2fa/verify/` to get the JWT tokens and complete the login.
Make the transitions smooth using framer-motion if possible.
```

---

## 📌 Prompt 3: Encrypted Community Posts Module (Phase 3)
**Copy this:**
```text
I need to build an Encrypted Posts Module to satisfy a core project requirement.

1. BACKEND MODEL: In `backend/apps/transactions/models.py` (or a new app), create a `Post` model. Fields: `id`, `author` (ForeignKey to User), `title_encrypted` (TextField), `content_encrypted` (TextField), `created_at`, `updated_at`. Create migrations and migrate.
2. BACKEND API: Create a ViewSet for Posts (`/api/posts/`). 
3. ENCRYPTION LOGIC: Override the `perform_create` and `perform_update` methods. When a post is saved, the `title` and `content` MUST be encrypted using the author's RSA public key before hitting the database. When fetching posts, decrypt them so the frontend receives readable text.
4. FRONTEND UI: Create `frontend/src/pages/Posts.tsx`. Build a beautiful, modern social feed card layout.
5. FRONTEND CREATION: Create a `CreatePost.tsx` modal or page with a rich-feeling input for Title and Content.
6. FRONTEND CONTROLS: Add "Edit" and "Delete" buttons to posts, but only show them if the logged-in user is the author.
```

---

## 📌 Prompt 4: The "Wow" Factors - Visualizing Cryptography (Phase 4)
**Copy this:**
```text
I want to add visual "Wow" factors for my final year project presentation to show the teacher that the cryptography is actually working.

1. CRYPTO VISUALIZER WIDGET: On `Dashboard.tsx`, build a cool "Live Security Status" widget. It should show a pulsing green dot and text like: "Connection Secured | AES-256 Transport | RSA-2048 Data at Rest | HMAC-SHA256 Integrity Verified".
2. RAW DATA TOGGLE (THE BIG WOW): On the `Profile.tsx` and `Posts.tsx` pages, add a premium-looking toggle switch at the top labeled "Teacher Mode: View Raw Encrypted Database Data".
3. TOGGLE LOGIC: When this toggle is turned ON, replace the readable text (like the user's contact info or post content) with a long string of random ciphertext (e.g., `eyJhbGciOiJSUzI1NiIsI...`) to simulate exactly what the database sees. When turned OFF, play a quick "decrypting" text animation that reveals the real text.
This will definitively prove the encryption requirement is met during the demo.
```

---

## 📌 Prompt 5: Final Year Showcase Polish (Phase 5)
**Copy this:**
```text
This is a final year showcase project, so the UI and UX need to look like a multi-million dollar startup. 

1. ANIMATIONS: Install and implement `framer-motion` for page transitions across all routes in `App.tsx`. Elements should smoothly fade and slide in when the user navigates.
2. PDF EXPORT: On the `TransactionHistory.tsx` page, add an "Export Statement to PDF" button. Use `jspdf` and `jspdf-autotable` to generate a beautiful, branded bank statement containing the user's transaction history.
3. LANDING PAGE REVAMP: Redesign `Home.tsx` to look like a modern, dark-mode SaaS banking platform (think Stripe or Vercel aesthetics). Add animated glowing gradients, a hero section explaining "Zero-Trust Encrypted Banking", and mock feature cards.
4. AUDIT LOGS UI: Enhance `AdminDashboard.tsx` with a terminal-like "Live Cryptographic Audit Trail" window that shows fake or real logs of cryptographic operations (e.g., "0xA9F... Key Pair Generated", "Integrity Check Passed").
```
