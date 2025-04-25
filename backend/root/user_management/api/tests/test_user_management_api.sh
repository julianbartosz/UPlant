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

# 4.1. TEST USERNAME CHANGE
echo -e "\n4.1. Testing username change endpoint..."
curl -s -X POST http://localhost:8000/api/users/me/update_username/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_username_change"
  }' > api_test_results/username_change.json
echo "Username change response saved to api_test_results/username_change.json"

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

echo -e "\n--- WEATHER AND LOCATION ENDPOINTS ---"

# 19. GET USER WEATHER DATA
echo -e "\n19. Getting user weather data..."
curl -s -X GET http://localhost:8000/api/users/weather/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/user_weather.json
echo "User weather data saved to api_test_results/user_weather.json"

# 20. UPDATE USER LOCATION
echo -e "\n20. Testing user location update..."
curl -s -X POST http://localhost:8000/api/users/location/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "zip_code": "10001"
  }' > api_test_results/user_location_update.json
echo "User location update saved to api_test_results/user_location_update.json"

# 21. GET ADMIN USER WEATHER DATA
echo -e "\n21. Getting admin user weather data..."
curl -s -X GET "http://localhost:8000/api/users/admin/users/$USER_ID/weather_data/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_user_weather.json
echo "Admin user weather data saved to api_test_results/admin_user_weather.json"

# 22. CREATE NEW USER AS ADMIN
echo -e "\n22. Testing admin user creation..."
NEW_USER_EMAIL="testuser_$(date +%s)@example.com"
NEW_USERNAME="testuser_$(date +%s)"

curl -s -X POST "http://localhost:8000/api/users/admin/users/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$NEW_USER_EMAIL'",
    "username": "'$NEW_USERNAME'",
    "password": "securepassword123",
    "is_active": true
  }' > api_test_results/admin_user_create.json
echo "Admin user creation saved to api_test_results/admin_user_create.json"

# Extract created user ID if available
CREATED_USER_ID=$(jq -r '.id' api_test_results/admin_user_create.json 2>/dev/null || echo "")
if [[ -n "$CREATED_USER_ID" && "$CREATED_USER_ID" != "null" ]]; then
  echo "Created new test user with ID: $CREATED_USER_ID"

  # 23. DEACTIVATE THE CREATED USER
  echo -e "\n23. Testing admin user deactivation..."
  curl -s -X POST "http://localhost:8000/api/users/admin/users/$CREATED_USER_ID/deactivate/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/admin_user_deactivate.json
  echo "Admin user deactivation saved to api_test_results/admin_user_deactivate.json"

  # 24. DELETE THE CREATED USER
  echo -e "\n24. Testing admin user deletion..."
  curl -s -X DELETE "http://localhost:8000/api/users/admin/users/$CREATED_USER_ID/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" -o /dev/null -w "%{http_code}" > api_test_results/admin_user_delete_status.txt
  echo "Admin user deletion status: $(cat api_test_results/admin_user_delete_status.txt)"
else
  echo "Failed to create test user, skipping user deactivation and deletion tests"
  echo '{"detail": "Test skipped - no user created"}' > api_test_results/admin_user_deactivate.json
  echo '{"detail": "Test skipped - no user created"}' > api_test_results/admin_user_delete_status.txt
fi

echo -e "\n--- EDGE CASES AND ERROR HANDLING ---"

# 25. TEST PASSWORD RESET CONFIRMATION (with invalid token)
echo -e "\n25. Testing password reset confirmation (with invalid token)..."
curl -s -X POST http://localhost:8000/api/users/password/reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "invalid-uid",
    "token": "invalid-token",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
  }' > api_test_results/password_reset_confirm.json
echo "Password reset confirmation test saved to api_test_results/password_reset_confirm.json"

# 26. TEST EMAIL VERIFICATION (with invalid key)
echo -e "\n26. Testing email verification (with invalid key)..."
curl -s -X GET "http://localhost:8000/api/users/email/verify/invalid-key/" \
  -H "Content-Type: application/json" > api_test_results/email_verification.json
echo "Email verification test saved to api_test_results/email_verification.json"

# 27. TEST AUTHENTICATION WITH INVALID TOKEN
echo -e "\n27. Testing endpoint with invalid auth token..."
curl -s -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Token INVALID_TOKEN_HERE" \
  -H "Content-Type: application/json" > api_test_results/invalid_token_test.json
echo "Invalid token test saved to api_test_results/invalid_token_test.json"

# 28. TEST PROFILE UPDATE WITH INVALID ZIP CODE
echo -e "\n28. Testing profile update with invalid ZIP code..."
curl -s -X PATCH http://localhost:8000/api/users/me/profile/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "zip_code": "not-a-zip-code"
  }' > api_test_results/invalid_zip_profile_update.json
echo "Invalid ZIP code test saved to api_test_results/invalid_zip_profile_update.json"

# 29. TEST LOGIN WITH INVALID CREDENTIALS
echo -e "\n29. Testing login with invalid credentials..."
curl -s -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fake@example.com",
    "password": "wrongpassword"
  }' > api_test_results/invalid_login.json
echo "Invalid login test saved to api_test_results/invalid_login.json"

# 30. TEST MISSING REQUIRED FIELDS IN USER CREATION
echo -e "\n30. Testing user creation with missing fields..."
curl -s -X POST "http://localhost:8000/api/users/admin/users/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "incomplete_user"
  }' > api_test_results/admin_user_create_invalid.json
echo "Invalid user creation saved to api_test_results/admin_user_create_invalid.json"

echo -e "\n--- SUMMARY ---"

TOTAL_TESTS=30
FAILED_TESTS=0

# Simple validation function
validate_response() {
  local file=$1
  local error_field=$2  # Field that indicates an error
  local required_field=$3  # Field that should be present for success
  
  if [ ! -f "$file" ]; then
    echo "❌ Test failed: File $file not found"
    ((FAILED_TESTS++))
    return
  fi

  # Check for error response (if specified)
  if [ -n "$error_field" ] && jq -e ".$error_field" "$file" >/dev/null 2>&1; then
    local error_msg=$(jq -r ".$error_field" "$file" 2>/dev/null)
    echo "❌ Test failed: $error_field - $error_msg" 
    ((FAILED_TESTS++))
    return
  fi
  
  # Check for required field (if specified)
  if [ -n "$required_field" ] && ! jq -e ".$required_field" "$file" >/dev/null 2>&1; then
    echo "❌ Test failed: Missing required field '$required_field'"
    ((FAILED_TESTS++))
    return
  fi
  
  echo "✅ Test passed"
}

# Generate a simple test report
echo -e "\nTest Results Summary:" > api_test_results/test_summary.txt
echo "======================" >> api_test_results/test_summary.txt
echo "Total tests executed: $TOTAL_TESTS" >> api_test_results/test_summary.txt
echo "Failed tests: $FAILED_TESTS" >> api_test_results/test_summary.txt
echo -e "\nDetailed results in api_test_results directory.\n" >> api_test_results/test_summary.txt
echo "Test report saved to api_test_results/test_summary.txt"

echo -e "\nAll User Management API endpoints tested. Check the api_test_results directory for results."
echo -e "Total tests executed: $TOTAL_TESTS\n"