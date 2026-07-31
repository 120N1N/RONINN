import sys
import os
import subprocess
import time

# Tambahkan direktori saat ini ke sys.path agar bisa import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_db():
    print("[*] Checking Database...")
    os.environ["DATABASE_URL"] = "sqlite:///./corvus_red.db"
    os.environ["USE_LOCAL_TASK_RUNNER"] = "true"
    from backend.db.database import engine, Base
    # Import models agar terbaca oleh SQLAlchemy
    from backend.db import models 
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("""
    =========================================
          CORVUS - STANDALONE RUNNER
    =========================================
    """)
    
    # Inisialisasi DB di proses utama sebelum spawning
    setup_db()
    
    print("[+] Starting Corvus Backend (Standalone)...")
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///./corvus_red.db"
    env["USE_LOCAL_TASK_RUNNER"] = "true"
    
    def start_backend():
        print("[+] Starting Corvus Backend (Standalone)...")
        return subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            env=env
        )

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    def start_frontend():
        if os.path.exists(frontend_dir):
            print("[+] Starting Corvus Frontend (Vite)...")
            return subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)
        else:
            print("[!] Frontend directory not found!")
            return None

    backend_process = start_backend()
    time.sleep(2) # Beri waktu backend siap
    frontend_process = start_frontend()

    try:
        # Auto-restart monitor loop
        while True:
            if backend_process and backend_process.poll() is not None:
                print("\n[!] Backend crashed or stopped. Restarting automatically...")
                backend_process = start_backend()
                
            if frontend_process and frontend_process.poll() is not None:
                print("\n[!] Frontend crashed or stopped. Restarting automatically...")
                frontend_process = start_frontend()
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[-] Shutting down Corvus...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
