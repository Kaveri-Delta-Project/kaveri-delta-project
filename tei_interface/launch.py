import os
import sys
import subprocess
import platform

def create_venv():
    """Create a virtual environment if it doesn't exist."""
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    else:
        print("Virtual environment already exists.")

def install_requirements():
    """Install dependencies into the venv."""
    venv_dir = "venv"
    if platform.system() == "Windows":
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(venv_dir, "bin", "pip")
    
    print("Upgrading pip...")
    subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
    
    print("Installing requirements...")
    subprocess.check_call([pip_exe, "install", "-r", "requirements.txt"])

def run_app():
    """Run the Flask app inside the venv."""
    venv_dir = "venv"
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
    
    print("Launching app...")
    subprocess.check_call([python_exe, "run_app.py"])

if __name__ == "__main__":
    create_venv()
    install_requirements()
    run_app()
