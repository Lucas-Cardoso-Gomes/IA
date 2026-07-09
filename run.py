import subprocess
import sys
import os

def run():
    print("Iniciando a aplicação Streamlit...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nEncerrando processo...")

if __name__ == "__main__":
    run()
