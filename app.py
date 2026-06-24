import streamlit as st
import os
import io
from utils.rag_engine import ingest_document
from utils.document_parser import extract_text_from_file
from utils.llm_integration import ask_rag, ask_document

# Set up page config
st.set_page_config(page_title="Comex AI Assistant", layout="wide", initial_sidebar_state="expanded")

from utils.config_manager import load_config, save_config

# Initialize session state variables
if "chat_history_rag" not in st.session_state:
    st.session_state.chat_history_rag = []
if "chat_history_doc" not in st.session_state:
    st.session_state.chat_history_doc = []
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = ""
if "current_doc_name" not in st.session_state:
    st.session_state.current_doc_name = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

config = load_config()

st.sidebar.title("Configurações")
model_choice = st.sidebar.selectbox("Modelo Ollama:", ["gemma3:1b", "gemma3:4b"], index=0)

st.title("Assistente Inteligente para Importação e Exportação")

# Create tabs for User and Admin
tab_user, tab_admin = st.tabs(["Área do Usuário (Chat)", "Área Admin (Base de Conhecimento)"])

with tab_admin:
    if not st.session_state.admin_logged_in:
        st.header("Acesso Restrito")
        st.write("Por favor, faça login para acessar a área administrativa.")
        login_user = st.text_input("Usuário")
        login_pass = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if login_user == config.get("admin_user", "admin") and login_pass == config.get("admin_pass", "admin"):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    else:
        if st.button("Sair"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.header("Configurações de Acesso")
        with st.expander("Alterar Credenciais de Admin"):
            new_user = st.text_input("Novo Usuário", value=config.get("admin_user", "admin"))
            new_pass = st.text_input("Nova Senha", type="password", value=config.get("admin_pass", "admin"))
            if st.button("Salvar Credenciais"):
                config["admin_user"] = new_user
                config["admin_pass"] = new_pass
                save_config(config)
                st.success("Credenciais atualizadas com sucesso!")

        st.header("Configuração de Prompts da IA")
        with st.expander("Personalizar Prompts"):
            new_prompt_rag = st.text_area("Prompt do RAG (Base de Conhecimento Geral)", value=config.get("prompt_rag", ""), height=200)
            new_prompt_doc = st.text_area("Prompt de Análise de Documento", value=config.get("prompt_doc", ""), height=200)
            if st.button("Salvar Prompts"):
                config["prompt_rag"] = new_prompt_rag
                config["prompt_doc"] = new_prompt_doc
                save_config(config)
                st.success("Prompts atualizados com sucesso!")

        st.header("Treinamento da Base de Conhecimento (Fase 2)")
        
        st.subheader("Opção 1: Upload de Documentos")
        st.write("Faça upload de procedimentos, manuais, legislações ou pacotes ZIP para treinar o assistente.")
        
        from utils.rag_engine import ingest_document, ingest_from_directory
        from utils.document_parser import extract_text_from_file

        uploaded_kb_files = st.file_uploader(
            "Selecione documentos ou arquivo ZIP", 
            accept_multiple_files=True, 
            key="kb_uploader"
        )
        
        if st.button("Processar e Treinar Documentos (Upload)"):
            if uploaded_kb_files:
                with st.spinner("Processando documentos..."):
                    for file in uploaded_kb_files:
                        # Ingest using our utility function
                        file_bytes = io.BytesIO(file.read())
                        success, msg = ingest_document(file_bytes, file.name)
                        if success:
                            st.success(msg)
                        else:
                            st.error(f"Erro ao processar {file.name}: {msg}")
            else:
                st.warning("Por favor, selecione ao menos um documento.")

        st.markdown("---")
        st.subheader("Opção 2: Treinar a partir do Servidor Local")
        st.write("Processa e ingere automaticamente todos os arquivos e pastas colocados na pasta `importar_treino` no servidor. Os arquivos serão apagados após o processamento.")
        
        if st.button("Processar Pasta 'importar_treino'"):
            with st.spinner("Processando pasta local..."):
                success, msg = ingest_from_directory("importar_treino")
                if success:
                    st.success(msg)
                else:
                    st.warning(msg)

with tab_user:
    st.header("Análise de Documentos e Assistente (Fase 1 e 2)")
    
    with st.expander("Anexar Documento para Análise Específica", expanded=not st.session_state.current_doc_text):
        st.write("Anexe um ou mais documentos de importação/exportação (ex: Invoice, PL, ZIP com todo o processo) para analisar ou deixe em branco para usar a Base de Conhecimento geral.")
        
        user_docs = st.file_uploader(
            "Anexar documento(s) ou ZIP", 
            accept_multiple_files=True, 
            key="user_doc_uploader"
        )
        
        if user_docs:
            combined_names = ", ".join([doc.name for doc in user_docs])
            if combined_names != st.session_state.current_doc_name:
                with st.spinner("Lendo e extraindo texto dos documentos..."):
                    all_extracted_text = ""
                    for doc in user_docs:
                        file_bytes = io.BytesIO(doc.read())
                        extracted_text = extract_text_from_file(file_bytes, doc.name)
                        all_extracted_text += f"\n\n--- Início do Documento: {doc.name} ---\n\n"
                        all_extracted_text += extracted_text
                        all_extracted_text += f"\n\n--- Fim do Documento: {doc.name} ---\n\n"
                        
                    st.session_state.current_doc_text = all_extracted_text
                    st.session_state.current_doc_name = combined_names
                    st.session_state.chat_history_doc = [] # Reset chat when new docs uploaded
                st.success(f"Documentos carregados!")
            
            st.text_area("Texto Extraído (Visualização Parcial)", st.session_state.current_doc_text[:1000] + "..." if len(st.session_state.current_doc_text) > 1000 else st.session_state.current_doc_text, height=150, disabled=True)
                
            if st.button("Limpar Documentos Anexados"):
                st.session_state.current_doc_text = ""
                st.session_state.current_doc_name = ""
                st.rerun()

    mode = "Documento Específico" if st.session_state.current_doc_text else "Base de Conhecimento Geral"
    st.info(f"Modo de Chat atual: **{mode}**")
    
    # Display chat messages in the main area to allow chat_input to stick to bottom
    chat_history = st.session_state.chat_history_doc if st.session_state.current_doc_text else st.session_state.chat_history_rag
    
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input at the root level of the tab
    if prompt := st.chat_input("Digite sua pergunta..."):
        # Add user message to history
        chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    if st.session_state.current_doc_text:
                        # Ask about specific document
                        response = ask_document(prompt, st.session_state.current_doc_text, model_name=model_choice)
                    else:
                        # Ask RAG
                        response = ask_rag(prompt, model_name=model_choice)
                    
                    st.markdown(response)
                    chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Erro ao se comunicar com a IA: {str(e)}\n\n(Verifique se o Ollama está rodando com o modelo selecionado)")
