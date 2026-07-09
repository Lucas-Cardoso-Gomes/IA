#!/bin/bash

echo "Instalando dependências..."
pip install -r backend/requirements.txt

# Inicia o streamlit
echo "Iniciando a aplicação..."
streamlit run app.py
