#!/usr/bin/env python3
import os
import sys
import json
import cgi
import cgitb

cgitb.enable()

DATA_FILE = "/var/www/hit_ratio.json"
FUNCTION_DATA_FILE = "/var/www/hit_ratio_by_function.json"

print("Content-Type: application/json\n")

method = os.environ.get("REQUEST_METHOD", "GET").upper()

def write_hit_ratio_by_function(func_name, num_attempts, num_success, num_failure):
    try:
        if os.path.exists(FUNCTION_DATA_FILE):
            with open(FUNCTION_DATA_FILE, "r") as f:
                function_data = json.load(f)
        else:
            function_data = {}

        if func_name not in function_data:
            function_data[func_name] = {
                "num_attempts": 0,
                "num_success": 0,
                "num_failure": 0
            }

        function_data[func_name]["num_attempts"] += num_attempts
        function_data[func_name]["num_success"] += num_success
        function_data[func_name]["num_failure"] += num_failure

        with open(FUNCTION_DATA_FILE, "w") as f:
            json.dump(function_data, f, indent=2)

    except Exception as e:
        print(json.dumps({"error": f"Failed to write function data: {str(e)}"}))

if method == "GET":
    try:
        with open(FUNCTION_DATA_FILE, "r") as f:
            data_str = f.read()
        print(data_str if data_str.strip() else "{}")
    except FileNotFoundError:
        print("{}")
    except Exception as e:
        print(json.dumps({"error": str(e)}))

elif method == "POST":
    try:
        input_data = sys.stdin.read()
        update = json.loads(input_data) 

        edge_name = update.get("edge")
        func_name = update.get("function")

        if not edge_name or not func_name:
            print(json.dumps({"error": "Missing 'edge' or 'function' in JSON"}))
            sys.exit(0)

        num_attempts = update.get("num_attempts", 0)
        num_success = update.get("num_success", 0)
        num_failure = update.get("num_failure", 0)

        try:
            with open(DATA_FILE, "r") as f:
                data_str = f.read().strip()
                data = json.loads(data_str) if data_str else {}
        except FileNotFoundError:
            data = {}

        if edge_name not in data:
            data[edge_name] = {}
        if func_name not in data[edge_name]:
            data[edge_name][func_name] = {
                "num_attempts": 0,
                "num_success": 0,
                "num_failure": 0
            }

        data[edge_name][func_name]["num_attempts"] += num_attempts
        data[edge_name][func_name]["num_success"] += num_success
        data[edge_name][func_name]["num_failure"] += num_failure

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

        write_hit_ratio_by_function(func_name, num_attempts, num_success, num_failure)

        print(json.dumps({
            "status": "success",
            "updated": data[edge_name][func_name]
        }))

    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON"}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

else:
    print(json.dumps({"error": "Method not allowed"}))

