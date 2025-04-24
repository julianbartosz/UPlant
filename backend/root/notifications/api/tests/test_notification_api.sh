#!/bin/bash
# filepath: /Users/julianbartosz/git/schoolwork/UPlant/backend/root/notifications/api/tests/test_notification_api.sh

# Set up token
TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c" 

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== Notification API Testing ==="
echo "Testing all endpoints..."

# 1. LIST ALL NOTIFICATIONS
echo -e "\n1. Listing all notifications..."
curl -s -X GET "http://localhost:8000/api/notifications/notifications/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" > api_test_results/notifications_list.json
echo "Notifications list saved to api_test_results/notifications_list.json"

# 2. GET DASHBOARD VIEW
echo -e "\n2. Getting notification dashboard..."
curl -s -X GET "http://localhost:8000/api/notifications/notifications/dashboard/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" > api_test_results/notifications_dashboard.json
echo "Dashboard data saved to api_test_results/notifications_dashboard.json"

# 3. CREATE A NEW NOTIFICATION (need a garden ID from user's gardens)
echo -e "\n3. Getting user's gardens first..."
curl -s -X GET "http://localhost:8000/api/gardens/gardens/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" > api_test_results/gardens_list.json

# Extract the first garden ID - using jq for JSON parsing 
GARDEN_ID=$(jq '.[0].id' api_test_results/gardens_list.json 2>/dev/null || echo "null")

if [ "$GARDEN_ID" == "null" ] || [ -z "$GARDEN_ID" ]; then
    echo "Error: No gardens found. Please create a garden first."
else
    echo "Using garden ID: $GARDEN_ID"
    
    echo -e "\nCreating a new notification..."
    curl -s -X POST "http://localhost:8000/api/notifications/notifications/" \
      -H "Authorization: Token $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "garden": '$GARDEN_ID',
        "name": "Test Watering Notification",
        "type": "WA",
        "interval": 7
      }' > api_test_results/notification_create.json
    
    # Extract notification ID using extract_id.py
    NOTIFICATION_ID=$(python3 extract_id.py api_test_results/notification_create.json)
    
    if [[ ! "$NOTIFICATION_ID" =~ ^[0-9]+$ ]]; then
        echo "Error: Failed to create notification. Check api_test_results/notification_create.json"
    else
        echo "Created notification with ID: $NOTIFICATION_ID"
        
        # 4. GET NOTIFICATION DETAILS
        echo -e "\n4. Fetching notification details..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -H "Authorization: Token $TOKEN" \
          -H "Content-Type: application/json" > api_test_results/notification_detail.json
        echo "Notification details saved to api_test_results/notification_detail.json"
        
        # 5. UPDATE NOTIFICATION
        echo -e "\n5. Updating notification..."
        curl -s -X PATCH "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -H "Authorization: Token $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{
            "name": "Updated Test Notification",
            "interval": 10
          }' > api_test_results/notification_update.json
        echo "Notification update saved to api_test_results/notification_update.json"
        
        # 6. GET NOTIFICATIONS BY GARDEN
        echo -e "\n6. Getting notifications by garden..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/by_garden/?garden_id=$GARDEN_ID" \
          -H "Authorization: Token $TOKEN" \
          -H "Content-Type: application/json" > api_test_results/notifications_by_garden.json
        echo "Notifications by garden saved to api_test_results/notifications_by_garden.json"
        
        # 7. ADD PLANT TO NOTIFICATION
        # First get a plant ID
        echo -e "\n7. Getting user plants first..."
        curl -s -X GET "http://localhost:8000/api/plants/plants/user-plants/" \
          -H "Authorization: Token $TOKEN" \
          -H "Content-Type: application/json" > api_test_results/user_plants.json
        
        # Extract first plant ID using jq
        PLANT_ID=$(jq '.[0].id' api_test_results/user_plants.json 2>/dev/null || echo "null")
        
        if [ "$PLANT_ID" == "null" ] || [ -z "$PLANT_ID" ]; then
            echo "No user plants found. Skipping plant association tests."
        else
            echo "Using plant ID: $PLANT_ID"
            
            # Add plant to notification
            echo -e "\nAdding plant to notification..."
            curl -s -X POST "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/add_plant/" \
              -H "Authorization: Token $TOKEN" \
              -H "Content-Type: application/json" \
              -d '{
                "plant_id": '$PLANT_ID',
                "custom_interval": 5
              }' > api_test_results/add_plant_notification.json
            echo "Plant addition saved to api_test_results/add_plant_notification.json"
            
            # 8. LIST NOTIFICATION INSTANCES
            echo -e "\n8. Listing notification instances..."
            curl -s -X GET "http://localhost:8000/api/notifications/instances/?notification=$NOTIFICATION_ID" \
              -H "Authorization: Token $TOKEN" \
              -H "Content-Type: application/json" > api_test_results/notification_instances.json
            echo "Notification instances saved to api_test_results/notification_instances.json"
            
            # Extract instance ID using jq
            INSTANCE_ID=$(jq '.[0].id' api_test_results/notification_instances.json 2>/dev/null || echo "null")
            
            if [ "$INSTANCE_ID" == "null" ] || [ -z "$INSTANCE_ID" ]; then
                echo "No notification instances found. Skipping instance tests."
            else
                echo "Using instance ID: $INSTANCE_ID"
                
                # 9. COMPLETE NOTIFICATION INSTANCE
                echo -e "\n9. Completing notification instance..."
                curl -s -X POST "http://localhost:8000/api/notifications/instances/$INSTANCE_ID/complete/" \
                  -H "Authorization: Token $TOKEN" \
                  -H "Content-Type: application/json" > api_test_results/complete_instance.json
                echo "Instance completion saved to api_test_results/complete_instance.json"
                
                # 10. GET UPCOMING INSTANCES
                echo -e "\n10. Getting upcoming instances..."
                curl -s -X GET "http://localhost:8000/api/notifications/instances/upcoming/?days=14" \
                  -H "Authorization: Token $TOKEN" \
                  -H "Content-Type: application/json" > api_test_results/upcoming_instances.json
                echo "Upcoming instances saved to api_test_results/upcoming_instances.json"
            fi
            
            # 11. REMOVE PLANT FROM NOTIFICATION
            echo -e "\n11. Removing plant from notification..."
            curl -s -X POST "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/remove_plant/" \
              -H "Authorization: Token $TOKEN" \
              -H "Content-Type: application/json" \
              -d '{
                "plant_id": '$PLANT_ID'
              }' > api_test_results/remove_plant_notification.json
            echo "Plant removal saved to api_test_results/remove_plant_notification.json"
        fi
        
        # 12. DELETE NOTIFICATION
        echo -e "\n12. Deleting notification..."
        curl -s -X DELETE "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -H "Authorization: Token $TOKEN" \
          -H "Content-Type: application/json" > api_test_results/notification_delete.json
        echo "Notification deletion saved to api_test_results/notification_delete.json"
    fi
fi

echo -e "\nAll notification API endpoints tested. Check the api_test_results directory for results."