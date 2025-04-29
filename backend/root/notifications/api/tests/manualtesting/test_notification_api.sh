#!/bin/bash
# filepath: /UPlant/backend/root/notifications/api/tests/test_notification_api.sh

# Set up token
TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c" 

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== Notification API Testing ==="
echo "Testing all endpoints..."

# 1. CREATE A NEW NOTIFICATION (need a garden ID from user's gardens)
echo -e "\n1. Getting user's gardens first..."
curl -s -X GET "http://localhost:8000/api/gardens/gardens/" \
  -b "$SESSION_COOKIE" \ \
  -H "Content-Type: application/json" > api_test_results/gardens_list.json

# Extract the first garden ID - using jq for JSON parsing 
GARDEN_ID=$(jq '.[0].id' api_test_results/gardens_list.json 2>/dev/null || echo "null")

if [[ ! "$GARDEN_ID" =~ ^[0-9]+$ ]]; then
    echo "Error: No gardens found. Please create a garden first."
else
    echo "Using garden ID: $GARDEN_ID"
    
    # 2. CREATE NOTIFICATION
    echo -e "\n2. Creating a new notification..."
    curl -s -X POST "http://localhost:8000/api/notifications/notifications/" \
      -b "$SESSION_COOKIE" \ \
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
        
        # 3. LIST ALL NOTIFICATIONS (now that we have one)
        echo -e "\n3. Listing all notifications..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > api_test_results/notifications_list.json
        echo "Notifications list saved to api_test_results/notifications_list.json"
        
        # 4. GET DASHBOARD VIEW
        echo -e "\n4. Getting notification dashboard..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/dashboard/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > api_test_results/notifications_dashboard.json
        echo "Dashboard data saved to api_test_results/notifications_dashboard.json"
        
        # 5. GET NOTIFICATION DETAILS
        echo -e "\n5. Fetching notification details..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > api_test_results/notification_detail.json
        echo "Notification details saved to api_test_results/notification_detail.json"
        
        # 6. GET NOTIFICATIONS BY GARDEN
        echo -e "\n6. Getting notifications by garden..."
        curl -s -X GET "http://localhost:8000/api/notifications/notifications/by_garden/?garden_id=$GARDEN_ID" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > api_test_results/notifications_by_garden.json
        echo "Notifications by garden saved to api_test_results/notifications_by_garden.json"
        
        # 7. UPDATE NOTIFICATION
        echo -e "\n7. Updating notification..."
        curl -s -X PATCH "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" \
          -d '{
            "name": "Updated Test Notification",
            "interval": 10
          }' > api_test_results/notification_update.json
        echo "Notification update saved to api_test_results/notification_update.json"
        
        # 8. TEST PLANT ASSOCIATION
        # First get a plant ID
        echo -e "\n8. Getting user plants first..."
        curl -s -X POST "http://localhost:8000/api/plants/plants/create-custom/" \
            -b "$SESSION_COOKIE" \ \
            -H "Content-Type: application/json" \
            -d '{
            "common_name": "Notification Test Plant",
            "scientific_name": "Testus notificus",
            "water_interval": 7,
            "detailed_description": "Plant created for notification testing",
            "rank": "species",
            "family": "Testaceae",
            "genus": "Testus",
            "care_instructions": "Water when notification tells you to"
            }' > api_test_results/test_plant_create.json
        
        # Extract the plant ID
        PLANT_ID=$(python3 extract_id.py api_test_results/test_plant_create.json)
        
        if [[ "$PLANT_ID" =~ ^[0-9]+$ ]]; then
            echo "Using plant ID: $PLANT_ID"
            
            # 9. ADD PLANT TO NOTIFICATION
            echo -e "\n9. Adding plant to notification..."
            curl -s -X POST "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/add_plant/" \
              -b "$SESSION_COOKIE" \ \
              -H "Content-Type: application/json" \
              -d '{
                "plant_id": '$PLANT_ID',
                "custom_interval": 5
              }' > api_test_results/add_plant_notification.json
            echo "Plant addition saved to api_test_results/add_plant_notification.json"
            
            # 10. LIST NOTIFICATION INSTANCES
            echo -e "\n10. Listing notification instances..."
            curl -s -X GET "http://localhost:8000/api/notifications/instances/?notification=$NOTIFICATION_ID" \
              -b "$SESSION_COOKIE" \ \
              -H "Content-Type: application/json" > api_test_results/notification_instances.json
            echo "Notification instances saved to api_test_results/notification_instances.json"
            
            # Extract instance ID using jq
            INSTANCE_ID=$(jq '.[0].id' api_test_results/notification_instances.json 2>/dev/null || echo "null")

            if [[ "$INSTANCE_ID" =~ ^[0-9]+$ ]]; then
                echo "Using instance ID: $INSTANCE_ID"
                
                # 11. COMPLETE NOTIFICATION INSTANCE
                echo -e "\n11. Completing notification instance..."
                curl -s -X POST "http://localhost:8000/api/notifications/instances/$INSTANCE_ID/complete/" \
                  -b "$SESSION_COOKIE" \ \
                  -H "Content-Type: application/json" > api_test_results/complete_instance.json
                echo "Instance completion saved to api_test_results/complete_instance.json"
            else
                echo "No notification instances found. Skipping instance completion test."
            fi
            
            # 12. GET UPCOMING INSTANCES
            echo -e "\n12. Getting upcoming instances..."
            curl -s -X GET "http://localhost:8000/api/notifications/instances/upcoming/?days=14" \
              -b "$SESSION_COOKIE" \ \
              -H "Content-Type: application/json" > api_test_results/upcoming_instances.json
            echo "Upcoming instances saved to api_test_results/upcoming_instances.json"
            
            # 13. REMOVE PLANT FROM NOTIFICATION
            echo -e "\n13. Removing plant from notification..."
            curl -s -X POST "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/remove_plant/" \
              -b "$SESSION_COOKIE" \ \
              -H "Content-Type: application/json" \
              -d '{
                "plant_id": '$PLANT_ID'
              }' > api_test_results/remove_plant_notification.json
            echo "Plant removal saved to api_test_results/remove_plant_notification.json"
            
            # 14. CHECK NOTIFICATIONS AGAIN AFTER CHANGES
            echo -e "\n14. Getting updated notification list..."
            curl -s -X GET "http://localhost:8000/api/notifications/notifications/" \
              -b "$SESSION_COOKIE" \ \
              -H "Content-Type: application/json" > api_test_results/notifications_list_after.json
            echo "Updated notifications list saved to api_test_results/notifications_list_after.json"
            
        else
            echo "Failed to get or create a plant. Skipping plant association tests."
        fi
        
        # 15. DELETE THE NOTIFICATION
        echo -e "\n15. Deleting notification..."
        curl -s -X DELETE "http://localhost:8000/api/notifications/notifications/$NOTIFICATION_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > api_test_results/notification_delete.json
        echo "Notification deletion saved to api_test_results/notification_delete.json"
    fi
fi

echo -e "\nAll notification API endpoints tested. Check the api_test_results directory for results."