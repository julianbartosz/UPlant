#!/bin/bash
# filepath: /UPlant/backend/root/gardens/api/tests/test_garden_api.sh

# Set up token
TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c" 

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== Garden API Testing ==="
echo "Testing all endpoints..."

# 1. LIST ALL GARDENS
echo -e "\n1. Listing all gardens..."
curl -s -X GET http://localhost:8000/api/gardens/gardens/ \
  -b "$SESSION_COOKIE" \ \
  -H "Content-Type: application/json" > api_test_results/gardens_list.json
echo "Garden list saved to api_test_results/gardens_list.json"

# 2. GET GARDEN DASHBOARD
echo -e "\n2. Getting garden dashboard..."
curl -s -X GET http://localhost:8000/api/gardens/gardens/dashboard/ \
  -b "$SESSION_COOKIE" \ \
  -H "Content-Type: application/json" > api_test_results/garden_dashboard.json
echo "Garden dashboard saved to api_test_results/garden_dashboard.json"

# 3. CREATE A NEW GARDEN
echo -e "\n3. Creating a new garden..."
curl -s -X POST http://localhost:8000/api/gardens/gardens/ \
  -b "$SESSION_COOKIE" \ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Complete API Test Garden",
    "size_x": 15,
    "size_y": 15
  }' > api_test_results/garden_create.json

# Extract garden ID using separate Python script
echo "Extracting garden ID..."
GARDEN_ID=$(python3 extract_id.py api_test_results/garden_create.json)
echo "Created garden with ID: $GARDEN_ID"

if [[ "$GARDEN_ID" =~ ^[0-9]+$ ]]; then
    # 4. GET A SPECIFIC GARDEN
    echo -e "\n4. Fetching garden details for ID: $GARDEN_ID..."
    curl -s -X GET "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/garden_detail_${GARDEN_ID}.json"
    echo "Garden details saved to api_test_results/garden_detail_${GARDEN_ID}.json"
    
    # 5. UPDATE A GARDEN - Simple update without changing dimensions
    echo -e "\n5. Updating garden metadata..."
    curl -s -X PATCH "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Updated Garden Name",
        "description": "This garden was updated via API"
      }' > "api_test_results/garden_update_${GARDEN_ID}.json"
    echo "Garden update saved to api_test_results/garden_update_${GARDEN_ID}.json"
    
    # 6. GET GRID LAYOUT
    echo -e "\n6. Fetching garden grid layout..."
    curl -s -X GET "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/grid/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/garden_grid_${GARDEN_ID}.json"
    echo "Garden grid layout saved to api_test_results/garden_grid_${GARDEN_ID}.json"
    
    # 7. UPDATE GRID LAYOUT
    echo -e "\n7. Updating garden grid layout..."
    # Creating a grid with a plant at position [2,3]
    curl -s -X POST "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/update_grid/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" \
      -d "{
        \"cells\": [
          $(for y in {0..14}; do
              echo -n "["
              for x in {0..14}; do
                if [[ $y -eq 2 && $x -eq 3 ]]; then
                  echo -n "{\"id\": 1}"
                else
                  echo -n "null"
                fi
                if [[ $x -lt 14 ]]; then echo -n ", "; fi
              done
              echo -n "]"
              if [[ $y -lt 14 ]]; then echo ", "; else echo ""; fi
          done)
        ]
      }" > "api_test_results/garden_grid_update_${GARDEN_ID}.json"
    echo "Garden grid update saved to api_test_results/garden_grid_update_${GARDEN_ID}.json"
    
    echo -e "\nVerifying grid update..."
    curl -s -X GET "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/grid/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/garden_grid_after_update_${GARDEN_ID}.json"
    echo "Updated grid saved to api_test_results/garden_grid_after_update_${GARDEN_ID}.json"
    
    # 8. ADD A PLANT TO GARDEN
    echo -e "\n8. Adding a plant to garden..."
    curl -s -X POST "http://localhost:8000/api/gardens/garden-logs/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" \
      -d "{
        \"garden\": $GARDEN_ID,
        \"plant\": 1,
        \"x_coordinate\": 5, 
        \"y_coordinate\": 7,
        \"planted_date\": \"2025-04-22\",
        \"notes\": \"Test plant added via API\",
        \"health_status\": \"Healthy\"
      }" > "api_test_results/garden_log_create.json"
    echo "Garden log created and saved to api_test_results/garden_log_create.json"
    
    # Extract garden log ID using the same helper script
    GARDEN_LOG_ID=$(python3 extract_id.py api_test_results/garden_log_create.json)
    echo "Created garden log with ID: $GARDEN_LOG_ID"
    
    if [[ "$GARDEN_LOG_ID" =~ ^[0-9]+$ ]]; then
        # 9. GET A SPECIFIC GARDEN LOG
        echo -e "\n9. Fetching garden log details for ID: $GARDEN_LOG_ID..."
        curl -s -X GET "http://localhost:8000/api/gardens/garden-logs/$GARDEN_LOG_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > "api_test_results/garden_log_detail_${GARDEN_LOG_ID}.json"
        echo "Garden log details saved to api_test_results/garden_log_detail_${GARDEN_LOG_ID}.json"
        
        # 10. UPDATE A GARDEN LOG
        echo -e "\n10. Updating garden log..."
        curl -s -X PATCH "http://localhost:8000/api/gardens/garden-logs/$GARDEN_LOG_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" \
          -d '{
            "notes": "Updated plant notes via API",
            "health_status": "Poor"
          }' > "api_test_results/garden_log_update_${GARDEN_LOG_ID}.json"
        echo "Garden log update saved to api_test_results/garden_log_update_${GARDEN_LOG_ID}.json"
        
        # 11. UPDATE PLANT HEALTH
        echo -e "\n11. Updating plant health status..."
        curl -s -X POST "http://localhost:8000/api/gardens/garden-logs/$GARDEN_LOG_ID/update_health/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" \
          -d '{
            "health_status": "Excellent"
          }' > "api_test_results/garden_log_health_update_${GARDEN_LOG_ID}.json"
        echo "Plant health update saved to api_test_results/garden_log_health_update_${GARDEN_LOG_ID}.json"

        # 12. LIST ALL GARDEN LOGS
        echo -e "\n12. Listing all garden logs..."
        curl -s -X GET "http://localhost:8000/api/gardens/garden-logs/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > "api_test_results/garden_logs_list.json"
        echo "Garden logs list saved to api_test_results/garden_logs_list.json"
        
        # 13. TEST GARDEN SIZE CHANGE
        echo -e "\n13. Testing garden size change..."
        curl -s -X PATCH "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" \
          -d '{
            "size_x": 10,
            "size_y": 10
          }' > "api_test_results/garden_size_update_${GARDEN_ID}.json"
        echo "Garden size update saved to api_test_results/garden_size_update_${GARDEN_ID}.json"
        
        # Get the grid again to verify the size change
        curl -s -X GET "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/grid/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > "api_test_results/garden_grid_after_resize_${GARDEN_ID}.json"
        echo "Grid after resize saved to api_test_results/garden_grid_after_resize_${GARDEN_ID}.json"
        
        # 14. DELETE A GARDEN LOG
        echo -e "\n14. Deleting garden log..."
        curl -s -X DELETE "http://localhost:8000/api/gardens/garden-logs/$GARDEN_LOG_ID/" \
          -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > "api_test_results/garden_log_delete_${GARDEN_LOG_ID}.json"
        echo "Garden log deletion response saved to api_test_results/garden_log_delete_${GARDEN_LOG_ID}.json"
    else
        echo "Error: Could not extract valid garden log ID"
    fi
    
    # 15. DELETE A GARDEN
    echo -e "\n15. Deleting garden..."
    curl -s -X DELETE "http://localhost:8000/api/gardens/gardens/$GARDEN_ID/" \
      -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/garden_delete_${GARDEN_ID}.json"
    echo "Garden deletion response saved to api_test_results/garden_delete_${GARDEN_ID}.json"
else
    echo "Error: Could not extract valid garden ID. Check api_test_results/garden_create.json"
fi

echo -e "\nAll endpoints tested. Check the api_test_results directory for results."