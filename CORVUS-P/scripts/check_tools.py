import shutil
import subprocess
import sys

TOOLS = [
    "subfinder",
    "nuclei",
    "httpx",
    "katana",
    "gau",
    "ffuf",
    "dalfox",
    "sqlmap"
]

def check_tools():
    missing = []
    print("--- Corvus Tool Checker ---")
    for tool in TOOLS:
        path = shutil.which(tool)
        if path:
            try:
                # Try to get version
                cmd = [tool, "--version"] if tool != "sqlmap" else [tool, "--version"]
                version = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).split('\n')[0]
                print(f"[OK] {tool.ljust(12)} -> {path} ({version})")
            except:
                print(f"[OK] {tool.ljust(12)} -> {path}")
        else:
            print(f"[ERROR] {tool.ljust(12)} -> MISSING")
            missing.append(tool)
            
    if missing:
        print(f"\nCRITICAL: {len(missing)} tools missing. Please run install_tools.sh")
        return False
    return True

if __name__ == "__main__":
    if not check_tools():
        sys.exit(1)
    sys.exit(0)
