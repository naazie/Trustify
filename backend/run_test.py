import asyncio
import os
import sys

# Ensure this script runs from trustify/backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tools.semgrep_runner import run_semgrep
from tools.pylint_runner import run_pylint
from tools.eslint_runner import run_eslint
from tools.gitleaks_runner import run_gitleaks

workspace = "/tmp/trustify_workspaces/test"
os.makedirs(workspace, exist_ok=True)
with open(f"{workspace}/test.py", "w") as f:
    f.write("import os\n")

print("Running pylint...")
try:
    print(run_pylint(workspace))
except Exception as e:
    print("PYLINT ERROR:", e)

print("Running semgrep...")
try:
    print(run_semgrep(workspace))
except Exception as e:
    print("SEMGREP ERROR:", e)

print("Running gitleaks...")
try:
    print(run_gitleaks(workspace))
except Exception as e:
    print("GITLEAKS ERROR:", e)

print("Running eslint...")
try:
    print(run_eslint(workspace))
except Exception as e:
    print("ESLINT ERROR:", e)
