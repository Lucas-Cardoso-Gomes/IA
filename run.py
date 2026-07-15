import subprocess
import sys
import os
import time

def run():
    print("Instalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join("backend", "requirements.txt")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)

    print("Iniciando migrações Alembic...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd="backend", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar migrações: {e}")

    print("Iniciando a aplicação FastAPI...")
    fastapi_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"])

    print("Iniciando o Celery Worker...")
    celery_process = subprocess.Popen([sys.executable, "-m", "celery", "-A", "backend.app.celery_app.celery_app", "worker", "--loglevel=info"])

    # Pequeno atraso para garantir que os serviços de backend subam
    time.sleep(3)

    print("Iniciando a aplicação Streamlit...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nEncerrando processos...")
    finally:
        fastapi_process.terminate()
        celery_process.terminate()

if __name__ == "__main__":
    run()
