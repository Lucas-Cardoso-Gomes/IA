import subprocess
import sys
import os
import platform
import signal
import time

def run():
    print("Instalando dependências do frontend se necessário...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

    try:
        subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)
    except Exception as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)

    print("Iniciando backend e frontend...")

    # Using python -m uvicorn ensures it uses the correct environment path
    backend_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000"])
    frontend_process = subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir)

    def signal_handler(sig, frame):
        print("\nEncerrando processos...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        # Handling the KeyboardInterrupt to also cover manual exits gracefully if signal handler doesn't catch it
        print("\nEncerrando processos...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    run()
