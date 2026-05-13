import subprocess
import os

os.chdir(r"C:\Users\marky\Desktop\production tool\product_tool")

result = subprocess.run(
    [r"venv\Scripts\python.exe", "run.py", "--input", "./data", "--no-interactive"],
    capture_output=True,
    text=True,
    timeout=120
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

# Keep window open
input("\nPress Enter to exit...")