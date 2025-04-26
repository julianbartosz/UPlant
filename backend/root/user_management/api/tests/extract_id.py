import json
import sys

def extract_id(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if 'id' in data:
                print(data['id'])
            else:
                print("Error: No ID found in response")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_id(sys.argv[1])
    else:
        print("Error: No filename provided")