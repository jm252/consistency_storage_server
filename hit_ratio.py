#!/usr/bin/env python3
import os
import sys
import json
import cgi
import cgitb
import fcntl
import tempfile
import shutil

cgitb.enable()

DATA_FILE = "/var/www/hit_ratio.json"

print("Content-Type: application/json\n\n")

method = os.environ.get("REQUEST_METHOD", "GET").upper()

if method == "GET":
    try:
        with open(DATA_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)  
            data_str = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)
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
        num_success  = update.get("num_success", 0)
        num_failure  = update.get("num_failure", 0)

        data = {}
        try:
            with open(DATA_FILE, "r+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                data_str = f.read().strip()
                if data_str:
                    data = json.loads(data_str)
                fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            pass  

        if edge_name not in data:
            data[edge_name] = {}
        if func_name not in data[edge_name]:
            data[edge_name][func_name] = {
                "num_attempts": 0,
                "num_success": 0,
                "num_failure": 0
            }

        data[edge_name][func_name]["num_attempts"] += num_attempts
        data[edge_name][func_name]["num_success"]  += num_success
        data[edge_name][func_name]["num_failure"]  += num_failure

        with tempfile.NamedTemporaryFile('w', dir="/tmp", delete=False) as tmp_file:
            json.dump(data, tmp_file, indent=2)
            tempname = tmp_file.name

        shutil.move(tempname, DATA_FILE)

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

