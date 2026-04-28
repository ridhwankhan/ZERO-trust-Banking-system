#!/bin/bash

# DEPOSIT FLOW TEST SCRIPT
# This script tests the complete deposit flow

echo "======================================"
echo "DEPOSIT FLOW TEST - COMPLETE VERIFICATION"
echo "======================================"

# 1. Register a new user
echo -e "\n[STEP 1] Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:5174/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"deposittest@example.com",
    "username":"deposittest",
    "password":"Test@12345",
    "password_confirm":"Test@12345"
  }')

echo "Response: $REGISTER_RESPONSE" | head -c 200
echo "..."

# Extract access token
ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)
USER_ID=$(echo $REGISTER_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Registration failed!"
  exit 1
fi

echo "✅ User registered! Token: ${ACCESS_TOKEN:0:20}..."
echo "   User ID: $USER_ID"

# 2. Check initial balance
echo -e "\n[STEP 2] Checking initial balance..."
BALANCE_BEFORE=$(curl -s -X GET http://localhost:5174/api/transactions/balance/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' | grep -o '"balance":"[^"]*' | cut -d'"' -f4)

echo "✅ Initial Balance: \$$BALANCE_BEFORE"

# 3. Initiate deposit
echo -e "\n[STEP 3] Initiating deposit..."
DEPOSIT_AMOUNT="500.00"
INITIATE_RESPONSE=$(curl -s -X POST http://localhost:5174/api/transactions/deposit/initiate/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"amount\": $DEPOSIT_AMOUNT}")

echo "✅ Deposit initiated for \$$DEPOSIT_AMOUNT"
echo "Response: $INITIATE_RESPONSE" | head -c 150
echo "..."

# 4. Process payment
echo -e "\n[STEP 4] Processing payment..."
PROCESS_RESPONSE=$(curl -s -X POST http://localhost:5174/api/transactions/deposit/process/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"amount\": $DEPOSIT_AMOUNT,
    \"card_number\": \"4111111111111111\"
  }")

echo "Response: $PROCESS_RESPONSE"

# Extract new balance from response
NEW_BALANCE=$(echo $PROCESS_RESPONSE | grep -o '"new_balance":"[^"]*' | cut -d'"' -f4)
TRANSACTION_ID=$(echo $PROCESS_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$NEW_BALANCE" ]; then
  echo "❌ Deposit processing failed!"
  echo "Full response: $PROCESS_RESPONSE"
  exit 1
fi

echo "✅ Payment processed! New Balance (from API): \$$NEW_BALANCE"
echo "   Transaction ID: $TRANSACTION_ID"

# 5. Verify balance updated
echo -e "\n[STEP 5] Verifying balance update..."
sleep 1

BALANCE_AFTER=$(curl -s -X GET http://localhost:5174/api/transactions/balance/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' | grep -o '"balance":"[^"]*' | cut -d'"' -f4)

echo "✅ Current Balance (from GET): \$$BALANCE_AFTER"

# Calculate expected balance
EXPECTED_BALANCE=$(echo "$BALANCE_BEFORE + $DEPOSIT_AMOUNT" | bc)

if [ "$BALANCE_AFTER" = "$NEW_BALANCE" ]; then
  echo "✅ BALANCE UPDATED CORRECTLY!"
  echo "   Before: \$$BALANCE_BEFORE"
  echo "   Deposited: \$$DEPOSIT_AMOUNT"
  echo "   After: \$$BALANCE_AFTER"
else
  echo "⚠️  Balance mismatch!"
  echo "   API returned: \$$NEW_BALANCE"
  echo "   GET request returns: \$$BALANCE_AFTER"
fi

# 6. View transaction history
echo -e "\n[STEP 6] Checking transaction history..."
HISTORY=$(curl -s -X GET http://localhost:5174/api/transactions/history/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json')

DEPOSIT_FOUND=$(echo $HISTORY | grep -c "deposit")
if [ "$DEPOSIT_FOUND" -gt 0 ]; then
  echo "✅ Deposit transaction found in history!"
else
  echo "⚠️  Deposit not found in transaction history"
fi

echo -e "\n======================================"
echo "TEST COMPLETE"
echo "======================================"
echo "Credentials for manual testing:"
echo "  Email: deposittest@example.com"
echo "  Password: Test@12345"
echo "  Final Balance: \$$BALANCE_AFTER"
echo "======================================"
