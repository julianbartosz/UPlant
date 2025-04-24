#!/bin/bash

# filepath: /Users/julianbartosz/git/schoolwork/UPlant/backend/root/plants/api/tests/test_plant_api.sh

# Set up token
TOKEN="9811995a3db487b9cd8d772aac66cacbf6dc861c" 

# Set the session cookie from browser
SESSION_COOKIE="sessionid=iaw7sl43l7slynu4sxj6ozwie14lc1bs"

# Create output directory
mkdir -p api_test_results

echo "=== Plant API Testing ==="
echo "Testing all endpoints..."

# 1. LIST ALL PLANTS
echo -e "\n1. Listing all plants..."
if [ ! -f api_test_results/plants_list.json ] || [ "$FORCE_NEW_LIST" = true ]; then
  curl -s -X GET "http://localhost:8000/api/plants/plants/" \
      -b "$SESSION_COOKIE" \ \
    -H "Content-Type: application/json" > api_test_results/plants_list.json
  echo "Plants list saved to api_test_results/plants_list.json"
else
  echo "Using existing plants_list.json (use FORCE_NEW_LIST=true to refresh)"
fi

# 2. GET PLANT STATISTICS
echo -e "\n2. Getting plant statistics..."
curl -s -X GET "http://localhost:8000/api/plants/plants/statistics/" \
    -b "$SESSION_COOKIE" \ \
  -H "Content-Type: application/json" > api_test_results/plants_statistics.json
echo "Plant statistics saved to api_test_results/plants_statistics.json"

# 3. CREATE A CUSTOM PLANT
echo -e "\n3. Creating a custom plant..."
curl -s -X POST "http://localhost:8000/api/plants/plants/create-custom/" \
  -H "Authorization: Token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "common_name": "Test Plant",
    "scientific_name": "Testus plantus",
    "water_interval": 7,
    "sunlight_requirements": "Full sun",
    "soil_type": "Loamy",
    "min_temperature": 65,
    "max_temperature": 85,
    "detailed_description": "This is a test plant created via API",
    "care_instructions": "Water regularly",
    "nutrient_requirements": "Medium",
    "maintenance_notes": "Prune as needed",
    "rank": "species",
    "family": "Testaceae",
    "genus": "Testus"
  }' > api_test_results/plant_create.json

# Extract plant ID using helper script
echo "Extracting plant ID..."
PLANT_ID=$(python3 extract_id.py api_test_results/plant_create.json)
echo "Created plant with ID: $PLANT_ID"

if [[ "$PLANT_ID" =~ ^[0-9]+$ ]]; then
    # 4. GET A SPECIFIC PLANT
    echo -e "\n4. Fetching plant details for ID: $PLANT_ID..."
    curl -s -X GET "http://localhost:8000/api/plants/plants/$PLANT_ID/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/plant_detail_${PLANT_ID}.json"
    echo "Plant details saved to api_test_results/plant_detail_${PLANT_ID}.json"
    
    # 5. UPDATE A USER PLANT
    echo -e "\n5. Updating plant via user-update endpoint..."
    curl -s -X PATCH "http://localhost:8000/api/plants/plants/$PLANT_ID/user-update/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" \
      -d '{
        "detailed_description": "This plant was updated via API test",
        "care_instructions": "Water every 5 days"
      }' > "api_test_results/plant_update_${PLANT_ID}.json"
    echo "Plant update saved to api_test_results/plant_update_${PLANT_ID}.json"

    # 6. LIST USER'S PLANTS
    echo -e "\n6. Listing user plants..."
    curl -s -X GET "http://localhost:8000/api/plants/plants/user-plants/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/user_plants_list.json
    echo "User plants list saved to api_test_results/user_plants_list.json"

    # Trefle plant ID from  database
    TREFLE_PLANT_ID=77116

    # 7. SUBMIT A CHANGE REQUEST
    echo -e "\n7. Submitting a change request for plant ID: $TREFLE_PLANT_ID..."
    curl -s -X POST "http://localhost:8000/api/plants/plants/$TREFLE_PLANT_ID/submit-change/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" \
      -d '{
        "field_name": "care_instructions",
        "new_value": "Water weekly, fertilize monthly",
        "reason": "More detailed instructions for better care"
      }' > api_test_results/change_request_submit.json
    echo "Change request submission saved to api_test_results/change_request_submit.json"

    # 8. LIST CHANGE REQUESTS
    echo -e "\n8. Listing all change requests..."
    curl -s -X GET "http://localhost:8000/api/plants/changes/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/change_requests_list.json
    echo "Change requests list saved to api_test_results/change_requests_list.json"
    
    # 9. LIST USER CHANGE REQUESTS
    echo -e "\n9. Listing user's change requests..."
    curl -s -X GET "http://localhost:8000/api/plants/changes/user-changes/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/user_change_requests.json
    echo "User change requests saved to api_test_results/user_change_requests.json"

    # Extract a change request ID if possible
    CHANGE_ID=$(python3 -c "
import json
try:
    with open('api_test_results/change_request_submit.json', 'r') as f:
        data = json.load(f)
        if 'id' in data:
            print(data['id'])
        else:
            print('')
except:
    print('')
")
    
    if [[ "$CHANGE_ID" =~ ^[0-9]+$ ]]; then
        # 10. GET SPECIFIC CHANGE REQUEST
        echo -e "\n10. Getting specific change request ID: $CHANGE_ID..."
        curl -s -X GET "http://localhost:8000/api/plants/changes/$CHANGE_ID/" \
            -b "$SESSION_COOKIE" \ \
          -H "Content-Type: application/json" > "api_test_results/change_request_${CHANGE_ID}.json"
        echo "Change request details saved to api_test_results/change_request_${CHANGE_ID}.json"
    else
        echo "Could not extract change request ID for detailed testing"
    fi

    # 11. DELETE THE TEST PLANT
    echo -e "\n11. Deleting the test plant ID: $PLANT_ID..."
    curl -s -X DELETE "http://localhost:8000/api/plants/plants/$PLANT_ID/" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > "api_test_results/plant_delete_${PLANT_ID}.json"
    echo "Plant deletion response saved to api_test_results/plant_delete_${PLANT_ID}.json"
    else
        echo "Error: Could not extract valid plant ID. Check api_test_results/plant_create.json"
    fi

    # 12. TEST PLANT SEARCH API
    echo -e "\n12. Testing plant search API..."
    curl -s -X GET "http://localhost:8000/api/plants/search/?q=oak&limit=10" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/plant_search_results.json
    echo "Search results saved to api_test_results/plant_search_results.json"

    # 13. TEST PLANT SEARCH WITH FILTERS
    echo -e "\n13. Testing plant search with filters..."
    curl -s -X GET "http://localhost:8000/api/plants/search/?q=oak&family=Fagaceae&limit=5" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/plant_search_filtered.json
    echo "Filtered search results saved to api_test_results/plant_search_filtered.json"

    # 14. TEST SEARCH SUGGESTIONS API
    echo -e "\n14. Testing plant search suggestions API..."
    curl -s -X GET "http://localhost:8000/api/plants/search/suggestions/?q=ma&field=common_name&limit=5" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/plant_search_suggestions.json
    echo "Search suggestions saved to api_test_results/plant_search_suggestions.json"

    # 15. TEST SEARCH API WITH ORDERING
    echo -e "\n15. Testing plant search with custom ordering..."
    curl -s -X GET "http://localhost:8000/api/plants/search/?q=maple&order_by=common_name&limit=10" \
        -b "$SESSION_COOKIE" \ \
      -H "Content-Type: application/json" > api_test_results/plant_search_ordered.json
    echo "Ordered search results saved to api_test_results/plant_search_ordered.json"

    echo -e "\nAll plant API endpoints tested, including search functionality. Check the api_test_results directory for results."