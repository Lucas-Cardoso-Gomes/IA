import subprocess
import sys
import os

def run():
    print("Instalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join("backend", "requirements.txt")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)

    print("Iniciando a aplicação Streamlit...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nEncerrando processo...")

if __name__ == "__main__":
    run()
