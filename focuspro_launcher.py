import socket
import subprocess
import sys
import os
import time

PORT = 65432

def main():
    # Try to connect to running instance first
    try:
        s = socket.create_connection(("localhost", PORT), timeout=1)
        s.sendall(b"focus")
        s.close()
        return
    except:
        pass  # No instance running, continue
    
    # Find the FocusPro EXE
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    focuspro_exe = os.path.join(exe_dir, "Remeinium FocusPro.exe")
    
    if not os.path.exists(focuspro_exe):
        print("❌ Cannot find FocusPro executable at:", focuspro_exe)
        sys.exit(1)
    
    # Launch with any protocol args
    args = [focuspro_exe] + sys.argv[1:]
    
    try:
        # Use CREATE_NEW_PROCESS_GROUP flag to prevent hanging
        creationflags = 0x00000200 if sys.platform == "win32" else 0
        subprocess.Popen(args, cwd=exe_dir, creationflags=creationflags)
    except Exception as e:
        print("❌ Failed to launch:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()