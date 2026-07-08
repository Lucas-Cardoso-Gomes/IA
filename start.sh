#!/bin/bash

# Instala as dependências se não existirem
cd frontend && npm install && cd ..

# Inicia o backend em background
echo "Iniciando backend..."
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Inicia o frontend em background
echo "Iniciando frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Aguarda os processos
wait $BACKEND_PID $FRONTEND_PID
