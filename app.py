import streamlit as st
import os
import io
from utils.rag_engine import ingest_document
from utils.document_parser import extract_text_from_file
from utils.llm_integration import ask_rag, ask_document

# Set up page config
st.set_page_config(page_title="Comex AI Assistant", layout="wide", initial_sidebar_state="expanded")

# Initialize session state variables
if "chat_history_rag" not in st.session_state:
    st.session_state.chat_history_rag = []
if "chat_history_doc" not in st.session_state:
    st.session_state.chat_history_doc = []
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = ""
if "current_doc_name" not in st.session_state:
    st.session_state.current_doc_name = ""

st.sidebar.title("Configurações")
model_choice = st.sidebar.selectbox("Modelo Ollama:", ["gemma3:1b", "gemma3:4b"], index=0)

st.title("Assistente Inteligente para Importação e Exportação")

# Create tabs for User and Admin
tab_user, tab_admin = st.tabs(["Área do Usuário (Chat)", "Área Admin (Base de Conhecimento)"])

with tab_admin:
    st.header("Treinamento da Base de Conhecimento (Fase 2)")
    st.write("Faça upload de procedimentos, manuais e legislações para treinar o assistente.")
    
    uploaded_kb_files = st.file_uploader(
        "Selecione documentos (PDF, DOCX, etc)", 
        accept_multiple_files=True, 
        key="kb_uploader"
    )
    
    if st.button("Processar e Treinar Documentos"):
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

with tab_user:
    st.header("Análise de Documentos e Assistente (Fase 1 e 2)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Documento para Análise Específica")
        st.write("Anexe um documento de importação/exportação (ex: Invoice, PL) para analisar ou deixe em branco para usar a Base de Conhecimento geral.")
        
        user_doc = st.file_uploader(
            "Anexar documento (opcional)", 
            accept_multiple_files=False, 
            key="user_doc_uploader"
        )
        
        if user_doc:
            if user_doc.name != st.session_state.current_doc_name:
                with st.spinner("Lendo e extraindo texto do documento..."):
                    file_bytes = io.BytesIO(user_doc.read())
                    extracted_text = extract_text_from_file(file_bytes, user_doc.name)
                    st.session_state.current_doc_text = extracted_text
                    st.session_state.current_doc_name = user_doc.name
                    st.session_state.chat_history_doc = [] # Reset chat when new doc uploaded
                st.success(f"Documento '{user_doc.name}' carregado!")
            
            with st.expander("Ver Texto Extraído (OCR/Leitura)"):
                st.text(st.session_state.current_doc_text[:1000] + "..." if len(st.session_state.current_doc_text) > 1000 else st.session_state.current_doc_text)
                
            if st.button("Limpar Documento Anexado"):
                st.session_state.current_doc_text = ""
                st.session_state.current_doc_name = ""
                st.rerun()

    with col2:
        st.subheader("Chat")
        
        mode = "Documento Específico" if st.session_state.current_doc_text else "Base de Conhecimento Geral"
        st.info(f"Modo atual: **{mode}**")
        
        # Display chat messages
        chat_history = st.session_state.chat_history_doc if st.session_state.current_doc_text else st.session_state.chat_history_rag
        
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
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
