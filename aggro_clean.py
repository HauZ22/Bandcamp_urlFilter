import os
import subprocess

files_to_delete = [
    "check_parser.py",
    "test_features.py",
    "test_headless.py",
    "test_parser.py",
    "cleanup_script.py",
    "git_status.tmp",
    "status.txt"
]

print("--- Starting aggressive cleanup ---")
for f in files_to_delete:
    if os.path.exists(f):
        try:
            os.chmod(f, 0o777)
            os.remove(f)
            print(f"DELETED: {f}")
        except Exception as e:
            print(f"FAILED to delete {f}: {e}")
    else:
        print(f"NOT FOUND: {f}")

print("\n--- Staging changes ---")
try:
    subprocess.run(["git", "add", "-A"], check=True)
    print("STAGED: git add -A success")
    res = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
    print("CURRENT STATUS:\n", res.stdout)
except Exception as e:
    print(f"GIT ERROR: {e}")
