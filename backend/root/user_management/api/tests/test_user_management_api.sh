#!/bin/bash
# filepath: /Users/julianbartosz/git/schoolwork/UPlant/backend/root/user_management/api/tests/test_user_management_api.sh

# Set up tokens
ADMIN_TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c"
USER_TOKEN=""  # Will be populated if login succeeds

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== User Management API Testing ==="
echo "Testing all endpoints..."

# 1. LOGIN TEST
echo -e "\n1. Testing login endpoint..."
curl -s -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bartoszjul@gmail.com",
    "password": "qajquH-0xebgo-kuggid"
  }' > api_test_results/login.json
echo "Login response saved to api_test_results/login.json"

# Extract token from login response for user endpoints
LOGIN_TOKEN=$(jq -r '.token' api_test_results/login.json 2>/dev/null || echo "")
if [[ -n "$LOGIN_TOKEN" && "$LOGIN_TOKEN" != "null" ]]; then
  echo "Successfully logged in and retrieved user token"
  USER_TOKEN=$LOGIN_TOKEN
else
  echo "Login failed, falling back to admin token for user requests"
  USER_TOKEN=$ADMIN_TOKEN
fi

echo -e "\n--- USER ENDPOINTS ---"

# 2. GET USER DETAILS
echo -e "\n2. Getting user details..."
curl -s -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/user_details.json
echo "User details saved to api_test_results/user_details.json"

# 3. GET USER PROFILE
echo -e "\n3. Getting user profile..."
curl -s -X GET http://localhost:8000/api/users/me/profile/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/user_profile.json
echo "User profile saved to api_test_results/user_profile.json"

# 4. UPDATE USER PROFILE
echo -e "\n4. Updating user profile..."
curl -s -X PATCH http://localhost:8000/api/users/me/profile/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Updated via API test",
    "zip_code": "12345"
  }' > api_test_results/user_profile_update.json
echo "User profile update saved to api_test_results/user_profile_update.json"

# 5. TEST PASSWORD CHANGE (using wrong password to avoid changing the actual password)
echo -e "\n5. Testing password change endpoint (simulated)..."
curl -s -X POST http://localhost:8000/api/users/password/change/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "wrongpassword",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
  }' > api_test_results/password_change.json
echo "Password change response saved to api_test_results/password_change.json"

# 6. TEST PASSWORD RESET REQUEST
echo -e "\n6. Testing password reset request..."
curl -s -X POST http://localhost:8000/api/users/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bartoszjul@gmail.com"
  }' > api_test_results/password_reset_request.json
echo "Password reset request response saved to api_test_results/password_reset_request.json"

# 7. TEST RESEND VERIFICATION EMAIL
echo -e "\n7. Testing resend verification email..."
curl -s -X POST http://localhost:8000/api/users/email/resend-verification/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/resend_verification.json
echo "Resend verification response saved to api_test_results/resend_verification.json"

# 8. TEST EMAIL CHANGE REQUEST (using wrong password)
echo -e "\n8. Testing email change request..."
curl -s -X POST http://localhost:8000/api/users/email/change/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_email": "new_test_email@example.com",
    "password": "wrongpassword"
  }' > api_test_results/email_change_request.json
echo "Email change request response saved to api_test_results/email_change_request.json"

# 9. TEST GET EMAILS
echo -e "\n9. Getting user emails..."
curl -s -X GET http://localhost:8000/api/users/email/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/user_emails.json
echo "User emails saved to api_test_results/user_emails.json"

# 10. TEST SET PRIMARY EMAIL
echo -e "\n10. Testing set primary email..."
curl -s -X POST http://localhost:8000/api/users/email/set-primary/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bartoszjul@gmail.com"
  }' > api_test_results/set_primary_email.json
echo "Set primary email response saved to api_test_results/set_primary_email.json"

# 11. SOCIAL ACCOUNT TESTS
echo -e "\n11. Getting social accounts..."
curl -s -X GET http://localhost:8000/api/users/social/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/social_accounts.json
echo "Social accounts saved to api_test_results/social_accounts.json"

# Check if there are any social accounts available
SOCIAL_ACCOUNT_ID=$(jq -r '.[0].id' api_test_results/social_accounts.json 2>/dev/null)
if [[ "$SOCIAL_ACCOUNT_ID" != "null" && -n "$SOCIAL_ACCOUNT_ID" ]]; then
  echo -e "\n12. Testing social account disconnect with account ID: $SOCIAL_ACCOUNT_ID..."
  curl -s -X POST http://localhost:8000/api/users/social/disconnect/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": '$SOCIAL_ACCOUNT_ID'
    }' > api_test_results/social_disconnect.json
  echo "Social account disconnect response saved to api_test_results/social_disconnect.json"
else
  echo -e "\n12. No social accounts found for testing disconnect - skipping this test..."
  echo "{\"detail\": \"Test skipped - no social accounts available\"}" > api_test_results/social_disconnect.json
fi

# --- ADMIN ENDPOINTS ---
echo -e "\n--- ADMIN ENDPOINTS ---"
echo "Using admin token for admin endpoints"

# 13. LIST ALL USERS (admin only)
echo -e "\n13. Listing all users (admin endpoint)..."
curl -s -X GET http://localhost:8000/api/users/admin/users/ \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_users_list.json
echo "Admin users list saved to api_test_results/admin_users_list.json"

# Try to extract a user ID for admin operations
USER_ID=$(jq -r '.[1].id // .[0].id' api_test_results/admin_users_list.json 2>/dev/null || echo "2")
echo "Using user ID: $USER_ID for admin operations"

# 14. GET USER DETAILS (admin endpoint)
echo -e "\n14. Getting user details by ID (admin endpoint)..."
curl -s -X GET "http://localhost:8000/api/users/admin/users/$USER_ID/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_user_detail.json
echo "Admin user detail saved to api_test_results/admin_user_detail.json"

# 15. UPDATE USER (admin endpoint)
echo -e "\n15. Updating user (admin endpoint)..."
curl -s -X PATCH "http://localhost:8000/api/users/admin/users/$USER_ID/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "username": "admin_updated_username"
  }' > api_test_results/admin_user_update.json
echo "Admin user update saved to api_test_results/admin_user_update.json"

# 16. TEST ADMIN USER ACTIVATION
echo -e "\n16. Activating user (admin endpoint)..."
curl -s -X POST "http://localhost:8000/api/users/admin/users/$USER_ID/activate/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true
  }' > api_test_results/admin_user_activate.json
echo "Admin user activate saved to api_test_results/admin_user_activate.json"

# 17. TEST ADMIN RESET USER PASSWORD
echo -e "\n17. Resetting user password (admin endpoint)..."
curl -s -X POST "http://localhost:8000/api/users/admin/users/$USER_ID/reset-password/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_password_reset.json
echo "Admin password reset saved to api_test_results/admin_password_reset.json"

# 18. TEST ADMIN STATS
echo -e "\n18. Getting admin user statistics..."
curl -s -X GET http://localhost:8000/api/users/admin/stats/ \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_stats.json
echo "Admin stats saved to api_test_results/admin_stats.json"

echo -e "\nAll User Management API endpoints tested. Check the api_test_results directory for results."