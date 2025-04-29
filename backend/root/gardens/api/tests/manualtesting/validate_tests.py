#!/usr/bin/env python3
# filepath: /Users/julianbartosz/git/schoolwork/UPlant/backend/root/gardens/api/tests/validate_tests.py

import json
import os
import sys
from pathlib import Path
import re
from datetime import datetime

# Configuration
results_dir = Path("api_test_results")
passed = 0
failed = 0
failures = []
warnings = []

def validate_json_response(data, validation_spec):
    """
    Validate JSON data against a validation specification.
    
    Args:
        data: The parsed JSON data
        validation_spec: Dict with validation rules
            - type: 'array', 'object'
            - fields: list of field names (for objects)
            - min_length: minimum length (for arrays)
            - array_item_fields: fields each array item should have
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if 'type' in validation_spec:
        # Validate data type
        expected_type = validation_spec['type']
        
        if expected_type == 'array':
            if not isinstance(data, list):
                return False, f"Expected array, got {type(data).__name__}"
                
            # Check minimum length if specified
            if 'min_length' in validation_spec and len(data) < validation_spec['min_length']:
                return False, f"Array length {len(data)} is less than minimum {validation_spec['min_length']}"
                
            # Check array item fields if specified
            if 'array_item_fields' in validation_spec and data:
                fields = validation_spec['array_item_fields']
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        return False, f"Array item {i} is not an object"
                    
                    missing = [field for field in fields if field not in item]
                    if missing:
                        return False, f"Array item {i} missing fields: {', '.join(missing)}"
        
        elif expected_type == 'object':
            if not isinstance(data, dict):
                return False, f"Expected object, got {type(data).__name__}"
    
    # Check for specific fields in objects
    if isinstance(data, dict) and 'fields' in validation_spec:
        fields = validation_spec['fields']
        missing = [field for field in fields if field not in data]
        if missing:
            return False, f"Missing fields: {', '.join(missing)}"
    
    # Run custom validation function if provided
    if 'custom_check' in validation_spec and callable(validation_spec['custom_check']):
        is_valid, error = validation_spec['custom_check'](data)
        if not is_valid:
            return False, error
    
    return True, None


def validate_file(test_name, filename, validation_spec=None, expected_status=None, is_weather_endpoint=False):
    """
    Validate a test result file against expected values.
    
    Args:
        test_name: Display name for the test
        filename: Name of the result file to validate
        validation_spec: What to validate in the JSON response
        expected_status: Expected HTTP status code
        is_weather_endpoint: Whether this is a weather-related endpoint that might fail
    """
    global passed, failed, warnings
    
    filepath = results_dir / filename
    if not filepath.exists():
        failed += 1
        failures.append(f"{test_name}: File not found - {filename}")
        print(f"❌ {test_name} - File not found")
        return False
    
    # Status code validation for status files
    if expected_status and filename.endswith('_status.txt'):
        with open(filepath, 'r') as f:
            status = f.read().strip()
            
            # Special handling for weather endpoints
            if is_weather_endpoint and status != str(expected_status):
                warnings.append(f"{test_name}: Got status {status}, expected {expected_status} (Weather API limitation)")
                print(f"⚠️ {test_name} - Weather API limitation: status {status} (expected {expected_status})")
                return True  # We still count this as "passing" since it's an external limitation
            
            if status == str(expected_status):
                passed += 1
                print(f"✅ {test_name}")
                return True
            else:
                failed += 1
                failures.append(f"{test_name}: Status {status} != {expected_status}")
                print(f"❌ {test_name} - Expected status {expected_status}, got {status}")
                return False
    
    # JSON validation
    if filename.endswith('.json'):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if not content.strip():
                    failed += 1
                    failures.append(f"{test_name}: Empty response")
                    print(f"❌ {test_name} - Empty response")
                    return False
                
                data = json.loads(content)
                
                # Special handling for weather endpoints
                if is_weather_endpoint:
                    # Check for error responses which are expected
                    if isinstance(data, dict) and ('error' in data or 'detail' in data):
                        warnings.append(f"{test_name}: Weather API limitation - {data.get('error') or data.get('detail')}")
                        print(f"⚠️ {test_name} - Weather API limitation: {data.get('error') or data.get('detail')}")
                        return True  # Count as "passing" since it's an expected limitation
                
                # If we have validation specs, validate against them
                if validation_spec:
                    is_valid, error = validate_json_response(data, validation_spec)
                    
                    if not is_valid:
                        failed += 1
                        failures.append(f"{test_name}: {error}")
                        print(f"❌ {test_name} - {error}")
                        return False
                
                passed += 1
                print(f"✅ {test_name}")
                return True
                
        except json.JSONDecodeError as e:
            failed += 1
            error_msg = f"Invalid JSON: {str(e)}"
            failures.append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name} - {error_msg}")
            return False
    
    # Default pass if we made it here with an unhandled file type
    passed += 1
    print(f"✅ {test_name}")
    return True


def find_garden_id():
    """Extract the garden ID from test results to use in other tests"""
    try:
        # Find the most recent garden_create.json file
        with open(results_dir / "garden_create.json", 'r') as f:
            data = json.loads(f.read())
            if isinstance(data, dict) and 'id' in data:
                return data['id']
    except:
        pass
    
    # If we can't find it directly, try to infer from filenames
    pattern = re.compile(r"garden_detail_(\d+)\.json")
    for file in results_dir.glob("garden_detail_*.json"):
        match = pattern.match(file.name)
        if match:
            return match.group(1)
    
    return None


def find_garden_log_id():
    """Extract the garden log ID from test results"""
    try:
        with open(results_dir / "garden_log_create.json", 'r') as f:
            data = json.loads(f.read())
            if isinstance(data, dict) and 'id' in data:
                return data['id']
    except:
        pass
    
    # If we can't find it directly, try to infer from filenames
    pattern = re.compile(r"garden_log_detail_(\d+)\.json")
    for file in results_dir.glob("garden_log_detail_*.json"):
        match = pattern.match(file.name)
        if match:
            return match.group(1)
    
    return None


def save_test_report():
    """Save test results to a report file for tracking"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = results_dir / f"test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(f"==== API TEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====\n\n")
        f.write(f"Total tests: {passed + failed}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        
        if warnings:
            f.write(f"\n==== WARNINGS ({len(warnings)}) ====\n")
            for warning in warnings:
                f.write(f"- {warning}\n")
        
        if failures:
            f.write(f"\n==== FAILURES ({len(failures)}) ====\n")
            for failure in failures:
                f.write(f"- {failure}\n")
                
        f.write("\n==== END OF REPORT ====\n")
    
    print(f"\nTest report saved to: {report_file}")


# Run validations
print("\n==== VALIDATING TEST RESULTS ====\n")

# Find IDs for dynamic tests
garden_id = find_garden_id()
garden_log_id = find_garden_log_id()

print(f"Found garden ID: {garden_id}")
print(f"Found garden log ID: {garden_log_id}")

# ================ BASIC TESTS ================

# 1. List all gardens
validate_file("Gardens list", "gardens_list.json", {
    'type': 'array',
    'min_length': 1,
    'array_item_fields': ['id', 'name', 'size_x', 'size_y']
})

# 2. Garden dashboard
validate_file("Garden dashboard", "garden_dashboard.json", {
    'type': 'object',
    'fields': ['gardens']
})

# 2.1 Invalid authentication
validate_file("Invalid auth", "invalid_auth_test.json", {
    'type': 'object',
    'fields': ['detail']
})

# 2.2 Invalid garden creation
validate_file("Invalid garden creation", "garden_create_invalid.json", {
    'type': 'object',
    'custom_check': lambda data: (
        any(key in data for key in ['name', 'size_x', 'size_y', 'non_field_errors']), 
        "Expected validation error fields"
    )
})

# 3. Garden create
validate_file("Garden create", "garden_create.json", {
    'type': 'object',
    'fields': ['id', 'name', 'size_x', 'size_y']
})

# ================ GARDEN SPECIFIC TESTS ================

if garden_id:
    # 4. Garden details
    validate_file(f"Garden details", f"garden_detail_{garden_id}.json", {
        'type': 'object',
        'fields': ['id', 'name', 'size_x', 'size_y']
    })
    
    # 5. Garden update
    validate_file(f"Garden update", f"garden_update_{garden_id}.json", {
        'type': 'object',
        'fields': ['id', 'name']
    })
    
    # 6. Garden grid
    validate_file(f"Garden grid", f"garden_grid_{garden_id}.json", {
        'type': 'object',
        'fields': ['cells']
    })
    
    # 7. Garden grid update
    validate_file(f"Garden grid update", f"garden_grid_update_{garden_id}.json", {
        'type': 'object',  # Just check that it's an object, but don't require specific fields
    })
    
    # 7.1 Boundary plant placement
    validate_file("Boundary plant placement", "garden_log_boundary_test.json", {
        'type': 'object',
        'fields': ['id', 'garden', 'plant']
    })
    
    # 7.2 Out-of-bounds plant placement
    validate_file("Out-of-bounds placement", "garden_log_out_of_bounds.json", {
        'type': 'object',
        'custom_check': lambda data: (
            'x_coordinate' in data or 'y_coordinate' in data or 'position' in data or 'detail' in data,
            "Expected validation error for out-of-bounds coordinates"
        )
    })
    
    # 13. Garden resize
    validate_file("Garden resize", f"garden_size_update_{garden_id}.json", {
        'type': 'object',
        'fields': ['id', 'size_x', 'size_y']
    })
    
    validate_file("Grid after resize", f"garden_grid_after_resize_{garden_id}.json", {
        'type': 'object',
        'fields': ['cells']
    })

# ================ GARDEN LOG TESTS ================

# 8. Adding plant to garden
validate_file("Garden log create", "garden_log_create.json", {
    'type': 'object',
    'fields': ['id', 'garden', 'plant', 'x_coordinate', 'y_coordinate']
})

# 8.1 Position conflict
validate_file("Position conflict", "garden_log_conflict_status.txt", expected_status=400)

if garden_log_id:
    # 9. Garden log details
    validate_file(f"Garden log details", f"garden_log_detail_{garden_log_id}.json", {
        'type': 'object',
        'fields': ['id', 'garden', 'plant', 'x_coordinate', 'y_coordinate']
    })
    
    # 10. Garden log update
    validate_file(f"Garden log update", f"garden_log_update_{garden_log_id}.json", {
        'type': 'object',
        'fields': ['id']
    })
    
    # 11. Plant health update
    validate_file("Plant health update", f"garden_log_health_update_{garden_log_id}.json", {
        'type': 'object',
        'fields': ['id', 'health_status']
    })
    
    # 17. Garden log deletion
    validate_file("Garden log delete", "garden_log_delete_status.txt", expected_status=204)

# 12. List all garden logs
validate_file("Garden logs list", "garden_logs_list.json", {
    'type': 'array',
    'array_item_fields': ['id', 'garden', 'plant']
})

# 12.1 Filtered garden logs
validate_file("Filtered garden logs", "garden_logs_filtered.json", {
    'type': 'array'
    # No need to check specific fields as it depends on what's in the garden
})

# 17.1 Delete non-existent garden log
validate_file("Non-existent garden log delete", "garden_log_delete_nonexistent_status.txt", expected_status=404)

# ================ WEATHER & RECOMMENDATIONS TESTS ================

# 14. Setting user ZIP code
# This is a setup step, no validation needed

# 15. Garden recommendations - special handling for weather API
validate_file("Garden recommendations", "garden_recommendations.json", {
    'type': 'object',
    # Very flexible validation as this can return either recommendations or error
}, is_weather_endpoint=True)

# 16. Plant weather compatibility - special handling for weather API
validate_file("Weather compatibility", "weather_compatibility.json", {
    'type': 'object',
    # Very flexible validation as this can return either compatibility data or error
}, is_weather_endpoint=True)

# ================ DELETION TESTS ================

# 18. Garden deletion
validate_file("Garden delete", "garden_delete_status.txt", expected_status=204)

# 19. Access to deleted garden
validate_file("Access deleted garden", "garden_access_after_deletion_status.txt", expected_status=404)

# ================ SUMMARY ================
print("\n==== SUMMARY ====")
print(f"Total tests: {passed + failed}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")

if warnings:
    print(f"\n⚠️ WARNINGS: {len(warnings)}")
    for warning in warnings:
        print(f"- {warning}")

if failures:
    print("\n==== FAILURES ====")
    for failure in failures:
        print(f"- {failure}")
    
    # Save a report file with detailed results
    save_test_report()
    
    sys.exit(1)
else:
    print("\n✨ All tests passed! ✨")
    
    if warnings:
        print("Note: Some tests have warnings (expected for weather API endpoints)")
    
    # Save a report file even on success
    save_test_report()
    
    sys.exit(0)