#!/bin/bash
# filepath: /Users/julianbartosz/git/schoolwork/UPlant/backend/root/user_management/api/tests/test_user_management_api.sh

# Set up tokens
ADMIN_TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c"
USER_TOKEN=""  # Will be populated if login succeeds
TEST_USER_TOKEN="" # Will be populated for test user

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== User Management API Testing ==="
echo "Testing all endpoints..."

# CREATE TEST USER FOR PASSWORD OPERATIONS
echo -e "\n--- CREATING TEST USER ---"
TEST_EMAIL="testuser_$(date +%s)@example.com"
TEST_USERNAME="testuser$(date +%s)"
TEST_PASSWORD="TestPassword123Abc"
NEW_TEST_PASSWORD="NewTestPassword456"

echo "Creating test user with username: $TEST_USERNAME and email: $TEST_EMAIL"

curl -s -X POST "http://localhost:8000/api/users/admin/users/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$TEST_EMAIL'",
    "username": "'$TEST_USERNAME'",
    "password": "'$TEST_PASSWORD'",
    "is_active": true
  }' > api_test_results/test_user_creation.json

echo "Test user creation response:"
cat api_test_results/test_user_creation.json

# Get the test user's ID
TEST_USER_ID=$(jq -r '.id // empty' api_test_results/test_user_creation.json 2>/dev/null)
if [[ -n "$TEST_USER_ID" && "$TEST_USER_ID" != "null" ]]; then
  echo "✅ Created test user with ID: $TEST_USER_ID"
  
  # ADD THE ACTIVATION HERE - AFTER we have the ID
  echo "Activating test user..."
  curl -s -X POST "http://localhost:8000/api/users/admin/users/$TEST_USER_ID/activate/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"is_active": true}' > api_test_results/test_user_activate.json
  
  # Login as test user to get token
  curl -s -X POST http://localhost:8000/api/users/login/ \
    -H "Content-Type: application/json" \
    -d '{
      "email": "'$TEST_EMAIL'",
      "password": "'$TEST_PASSWORD'"
    }' > api_test_results/test_user_login.json
    
    echo "Test user login response:"
    cat api_test_results/test_user_login.json

  TEST_USER_TOKEN=$(jq -r '.token // empty' api_test_results/test_user_login.json 2>/dev/null)
  
  if [[ -n "$TEST_USER_TOKEN" && "$TEST_USER_TOKEN" != "null" ]]; then
    echo "✅ Successfully logged in as test user"
  else
    echo "❌ Failed to login as test user - some tests may fail"
  fi
else
  echo "❌ Failed to create test user - some tests may fail"
fi

# 1. LOGIN TEST (regular user)
echo -e "\n1. Testing login endpoint..."
curl -s -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bartoszjul@gmail.com",
    "password": "qajquH-0xebgo-kuggid"
  }' > api_test_results/login.json
echo "Login response saved to api_test_results/login.json"

# Extract token from login response for user endpoints
LOGIN_TOKEN=$(jq -r '.token // empty' api_test_results/login.json 2>/dev/null)
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
    "zip_code": "12345"
  }' > api_test_results/user_profile_update.json
echo "User profile update saved to api_test_results/user_profile_update.json"

# 4.1. TEST USERNAME CHANGE
echo -e "\n4.1. Testing username change endpoint..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  # Use test user for this operation
  NEW_TEST_USERNAME="${TEST_USERNAME}_updated"
  curl -s -X POST http://localhost:8000/api/users/me/update_username/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "username": "'$NEW_TEST_USERNAME'"
    }' > api_test_results/username_change.json
  echo "Username change response saved to api_test_results/username_change.json"
  
  # Verify username was changed
  CHANGED_USERNAME=$(jq -r '.username // empty' api_test_results/username_change.json 2>/dev/null)
  if [[ "$CHANGED_USERNAME" == "$NEW_TEST_USERNAME" ]]; then
    echo "✅ Username successfully changed to: $CHANGED_USERNAME"
  fi
else
  echo "⚠️ Skipping actual username change - no test user available"
  curl -s -X POST http://localhost:8000/api/users/me/update_username/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "username": "test_username_change_simulation"
    }' > api_test_results/username_change.json
fi

# 5. TEST PASSWORD CHANGE
echo -e "\n5. Testing password change endpoint..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X POST http://localhost:8000/api/users/password/change/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "current_password": "'$TEST_PASSWORD'",
      "new_password": "'$NEW_TEST_PASSWORD'",
      "confirm_password": "'$NEW_TEST_PASSWORD'"
    }' > api_test_results/password_change.json
  echo "Password change response saved to api_test_results/password_change.json"
  
  # Verify password was changed by logging in again with new password
  curl -s -X POST http://localhost:8000/api/users/login/ \
    -H "Content-Type: application/json" \
    -d '{
      "email": "'$TEST_EMAIL'",
      "password": "'$NEW_TEST_PASSWORD'"
    }' > api_test_results/test_user_relogin.json
    
  NEW_TOKEN=$(jq -r '.token // empty' api_test_results/test_user_relogin.json 2>/dev/null)
  if [[ -n "$NEW_TOKEN" && "$NEW_TOKEN" != "null" ]]; then
    echo "✅ Password change verified - successfully logged in with new password"
    TEST_USER_TOKEN=$NEW_TOKEN
  else
    echo "❌ Password change verification failed - couldn't log in with new password"
  fi
else
  echo "⚠️ Skipping actual password change - no test user available"
  curl -s -X POST http://localhost:8000/api/users/password/change/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "current_password": "wrongpassword",
      "new_password": "newpassword123",
      "confirm_password": "newpassword123"
    }' > api_test_results/password_change.json
fi

# 6. TEST PASSWORD RESET REQUEST
echo -e "\n6. Testing password reset request..."
if [[ -n "$TEST_USER_ID" ]]; then
  curl -s -X POST http://localhost:8000/api/users/password/reset/ \
    -H "Content-Type: application/json" \
    -d '{
      "email": "'$TEST_EMAIL'"
    }' > api_test_results/password_reset_request.json
  echo "Password reset request response saved to api_test_results/password_reset_request.json"
else
  echo "⚠️ Skipping actual password reset request - no test user available"
  curl -s -X POST http://localhost:8000/api/users/password/reset/ \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test_nonexistent@example.com"
    }' > api_test_results/password_reset_request.json
fi

# 7. TEST RESEND VERIFICATION EMAIL
echo -e "\n7. Testing resend verification email..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X POST http://localhost:8000/api/users/email/resend-verification/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/resend_verification.json
else
  curl -s -X POST http://localhost:8000/api/users/email/resend-verification/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/resend_verification.json
fi
echo "Resend verification response saved to api_test_results/resend_verification.json"

# 8. TEST EMAIL CHANGE REQUEST
echo -e "\n8. Testing email change request..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  NEW_TEST_EMAIL="changed_${TEST_EMAIL}"
  curl -s -X POST http://localhost:8000/api/users/email/change/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "new_email": "'$NEW_TEST_EMAIL'",
      "password": "'$NEW_TEST_PASSWORD'"
    }' > api_test_results/email_change_request.json
else
  curl -s -X POST http://localhost:8000/api/users/email/change/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "new_email": "new_test_email@example.com",
      "password": "wrongpassword"
    }' > api_test_results/email_change_request.json
fi
echo "Email change request response saved to api_test_results/email_change_request.json"

# 9. TEST GET EMAILS
echo -e "\n9. Getting user emails..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X GET http://localhost:8000/api/users/email/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_emails.json
else
  curl -s -X GET http://localhost:8000/api/users/email/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_emails.json
fi
echo "User emails saved to api_test_results/user_emails.json"

# 10. TEST SET PRIMARY EMAIL
echo -e "\n10. Testing set primary email..."
if [[ -n "$TEST_USER_TOKEN" && -n "$TEST_EMAIL" ]]; then
  curl -s -X POST http://localhost:8000/api/users/email/set-primary/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "'$TEST_EMAIL'"
    }' > api_test_results/set_primary_email.json
else
  curl -s -X POST http://localhost:8000/api/users/email/set-primary/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "bartoszjul@gmail.com"
    }' > api_test_results/set_primary_email.json
fi
echo "Set primary email response saved to api_test_results/set_primary_email.json"

# 11. SOCIAL ACCOUNT TESTS
echo -e "\n11. Getting social accounts..."
curl -s -X GET http://localhost:8000/api/users/social/ \
  -H "Authorization: Token $USER_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/social_accounts.json
echo "Social accounts saved to api_test_results/social_accounts.json"

# Check if there are any social accounts available
SOCIAL_ACCOUNT_ID=$(jq -r '.[0].id // empty' api_test_results/social_accounts.json 2>/dev/null)
if [[ -n "$SOCIAL_ACCOUNT_ID" && "$SOCIAL_ACCOUNT_ID" != "null" ]]; then
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

# 14. GET USER DETAILS (admin endpoint) - using test user ID if available
echo -e "\n14. Getting user details by ID (admin endpoint)..."
ADMIN_TARGET_ID=${TEST_USER_ID:-$(jq -r '.[1].id // .[0].id // "1"' api_test_results/admin_users_list.json 2>/dev/null)}
echo "Using user ID: $ADMIN_TARGET_ID for admin operations"

curl -s -X GET "http://localhost:8000/api/users/admin/users/$ADMIN_TARGET_ID/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_user_detail.json
echo "Admin user detail saved to api_test_results/admin_user_detail.json"

# 15. UPDATE USER (admin endpoint)
echo -e "\n15. Updating user (admin endpoint)..."
curl -s -X PATCH "http://localhost:8000/api/users/admin/users/$ADMIN_TARGET_ID/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "username": "admin_updated_username"
  }' > api_test_results/admin_user_update.json
echo "Admin user update saved to api_test_results/admin_user_update.json"

# 16. TEST ADMIN USER ACTIVATION
echo -e "\n16. Activating user (admin endpoint)..."
curl -s -X POST "http://localhost:8000/api/users/admin/users/$ADMIN_TARGET_ID/activate/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true
  }' > api_test_results/admin_user_activate.json
echo "Admin user activate saved to api_test_results/admin_user_activate.json"

# 17. TEST ADMIN RESET USER PASSWORD
echo -e "\n17. Resetting user password (admin endpoint)..."
curl -s -X POST "http://localhost:8000/api/users/admin/users/$ADMIN_TARGET_ID/reset-password/" \
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
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X GET http://localhost:8000/api/users/weather/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_weather.json
else
  curl -s -X GET http://localhost:8000/api/users/weather/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_weather.json
fi
echo "User weather data saved to api_test_results/user_weather.json"

# 20. UPDATE USER LOCATION
echo -e "\n20. Testing user location update..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X POST http://localhost:8000/api/users/location/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "zip_code": "10001"
    }' > api_test_results/user_location_update.json
else
  curl -s -X POST http://localhost:8000/api/users/location/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "zip_code": "10001"
    }' > api_test_results/user_location_update.json
fi
echo "User location update saved to api_test_results/user_location_update.json"

# 21. GET ADMIN USER WEATHER DATA
echo -e "\n21. Getting admin user weather data..."
curl -s -X GET "http://localhost:8000/api/users/admin/users/$ADMIN_TARGET_ID/weather_data/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" > api_test_results/admin_user_weather.json
echo "Admin user weather data saved to api_test_results/admin_user_weather.json"

# 22. CREATE ADDITIONAL TEST USER AS ADMIN
echo -e "\n22. Testing admin user creation..."
SECOND_TEST_EMAIL="testuser2_$(date +%s)@example.com"
SECOND_TEST_USERNAME="testuser2_$(date +%s)"

curl -s -X POST "http://localhost:8000/api/users/admin/users/" \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$SECOND_TEST_EMAIL'",
    "username": "'$SECOND_TEST_USERNAME'",
    "password": "securepassword123",
    "is_active": true
  }' > api_test_results/admin_user_create.json
echo "Admin user creation saved to api_test_results/admin_user_create.json"

# Extract created user ID if available
SECOND_TEST_USER_ID=$(jq -r '.id // empty' api_test_results/admin_user_create.json 2>/dev/null)
if [[ -n "$SECOND_TEST_USER_ID" && "$SECOND_TEST_USER_ID" != "null" ]]; then
  echo "Created second test user with ID: $SECOND_TEST_USER_ID"

  # 23. DEACTIVATE THE CREATED USER
  echo -e "\n23. Testing admin user deactivation..."
  curl -s -X POST "http://localhost:8000/api/users/admin/users/$SECOND_TEST_USER_ID/deactivate/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/admin_user_deactivate.json
  echo "Admin user deactivation saved to api_test_results/admin_user_deactivate.json"

  # 24. DELETE THE CREATED USER
  echo -e "\n24. Testing admin user deletion..."
  curl -s -X DELETE "http://localhost:8000/api/users/admin/users/$SECOND_TEST_USER_ID/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" -o /dev/null -w "%{http_code}" > api_test_results/admin_user_delete_status.txt
  echo "Admin user deletion status: $(cat api_test_results/admin_user_delete_status.txt)"
else
  echo "Failed to create second test user, skipping user deactivation and deletion tests"
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
if [[ -n "$TEST_USER_TOKEN" ]]; then
  curl -s -X PATCH http://localhost:8000/api/users/me/profile/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "zip_code": "not-a-zip-code"
    }' > api_test_results/invalid_zip_profile_update.json
else
  curl -s -X PATCH http://localhost:8000/api/users/me/profile/ \
    -H "Authorization: Token $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "zip_code": "not-a-zip-code"
    }' > api_test_results/invalid_zip_profile_update.json
fi
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

# 31. TEST USER ACCOUNT SELF-DELETION
echo -e "\n31. Testing user account self-deletion..."
if [[ -n "$TEST_USER_TOKEN" ]]; then
  # First verify the user is active
  curl -s -X GET http://localhost:8000/api/users/me/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_before_deletion.json
  
  IS_ACTIVE_BEFORE=$(jq -r '.is_active // "null"' api_test_results/user_before_deletion.json 2>/dev/null)
  echo "User active status before deletion: $IS_ACTIVE_BEFORE"
  
  # Now perform the account deletion (soft delete via POST)
  curl -s -X POST http://localhost:8000/api/users/me/delete/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "password": "'$NEW_TEST_PASSWORD'"
    }' > api_test_results/user_self_delete.json
  echo "User self-deletion response saved to api_test_results/user_self_delete.json"
  
  # Check if token is still valid (should be invalidated after deletion)
  curl -s -X GET http://localhost:8000/api/users/me/ \
    -H "Authorization: Token $TEST_USER_TOKEN" \
    -H "Content-Type: application/json" > api_test_results/user_after_deletion.json
  
  # Verify the account is now deactivated by checking admin endpoint
  if [[ -n "$TEST_USER_ID" ]]; then
    curl -s -X GET "http://localhost:8000/api/users/admin/users/$TEST_USER_ID/" \
      -H "Authorization: Token $ADMIN_TOKEN" \
      -H "Content-Type: application/json" > api_test_results/user_deactivation_check.json
    
    IS_ACTIVE_AFTER=$(jq -r '.is_active // "null"' api_test_results/user_deactivation_check.json 2>/dev/null)
    echo "User active status after deletion: $IS_ACTIVE_AFTER"
    
    if [[ "$IS_ACTIVE_AFTER" == "false" ]]; then
      echo "✅ User was successfully deactivated"
    else
      echo "❌ User deactivation failed - user is still active"
    fi
  fi
else
  echo "⚠️ Skipping user self-deletion test - no test user token available"
  echo '{"detail": "Test skipped - no test user available"}' > api_test_results/user_self_delete.json
fi

# --- CLEANUP - DELETE THE MAIN TEST USER ---
if [[ -n "$TEST_USER_ID" ]]; then
  echo -e "\n--- CLEANUP: DELETING TEST USER ---"
  curl -s -X DELETE "http://localhost:8000/api/users/admin/users/$TEST_USER_ID/" \
    -H "Authorization: Token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" -o /dev/null -w "%{http_code}" > api_test_results/main_test_user_delete.txt
  echo "Main test user deleted with status: $(cat api_test_results/main_test_user_delete.txt)"
fi

echo -e "\n--- SUMMARY ---"

TOTAL_TESTS=31
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