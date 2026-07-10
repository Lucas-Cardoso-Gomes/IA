import streamlit as st
import asyncio
import os
import uuid
import json

from backend.app.database import SessionLocal
from backend.app.models.models import Notebook, Document
from backend.app.services.ingestion import ingestion_service
from backend.app.services.search import search_service
from backend.app.agents.validator import auditor_agent
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.models import Notebook, Document

Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="PM Logística - Inteligência Documental", layout="wide")

import contextlib

# Helper to manage DB session in Streamlit
@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Main Layout Structure
def main():
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para", ["Notebook Workspace", "Admin Dashboard"])

    if page == "Notebook Workspace":
        render_notebook_workspace()
    elif page == "Admin Dashboard":
        render_admin_dashboard()

def render_notebook_workspace():
    st.header("Notebook Workspace")
    with get_db() as db:

        # Sidebar for Notebook selection
        st.sidebar.subheader("Notebooks")

        new_nb_title = st.sidebar.text_input("Novo Processo (Notebook)")
        if st.sidebar.button("Criar Notebook"):
            if new_nb_title:
                new_nb = Notebook(title=new_nb_title, user_id=str(uuid.uuid4()))
                db.add(new_nb)
                db.commit()
                st.sidebar.success("Criado!")
                st.rerun()

        notebooks = db.query(Notebook).all()
        if not notebooks:
            st.info("Crie um Notebook na barra lateral para começar.")
            return

        nb_options = {str(nb.id): nb.title for nb in notebooks}
        selected_nb_id = st.sidebar.selectbox("Selecionar Processo", options=list(nb_options.keys()), format_func=lambda x: nb_options[x])

        # Delete notebook option
        if st.sidebar.button("Apagar Notebook"):
            nb_to_delete = db.query(Notebook).filter(Notebook.id == selected_nb_id).first()
            if nb_to_delete:
                db.delete(nb_to_delete)
                db.commit()
                st.sidebar.success("Notebook apagado!")
                st.rerun()

        st.subheader(f"Processo: {nb_options[selected_nb_id]}")

        col1, col2 = st.columns([0.6, 0.4])

        with col1:
            st.write("### Fontes do Notebook")
            uploaded_file = st.file_uploader("Adicionar Fonte (PDF, DOCX, Imagem)", type=["pdf", "docx", "png", "jpg"], key="nb_uploader")

            if uploaded_file is not None:
                if st.button("Adicionar Documento"):
                    with st.spinner("Indexando..."):
                        temp_dir = "temp_storage"
                        os.makedirs(temp_dir, exist_ok=True)
                        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        asyncio.run(ingestion_service.ingest_document(db, file_path, uploaded_file.name, notebook_id=selected_nb_id))
                        st.success("Documento adicionado!")
                        st.rerun()

            docs = db.query(Document).filter(Document.notebook_id == selected_nb_id).all()
            if docs:
                for doc in docs:
                    doc_col1, doc_col2 = st.columns([0.8, 0.2])
                    with doc_col1:
                        st.write(f"- 📄 {doc.filename}")
                    with doc_col2:
                        if st.button("🗑️ Remover", key=f"del_doc_{doc.id}"):
                            db.delete(doc)
                            db.commit()
                            st.rerun()

                if st.button("Auditar Notebook (Processamento Inteligente)"):
                    with st.spinner("Analisando documentos (LLM Auditor)..."):
                        try:
                            result_str = asyncio.run(auditor_agent.audit_notebook(db, selected_nb_id))
                            result = json.loads(result_str)

                            st.write("#### Resultado da Auditoria")
                            st.write(f"**Status:** {result.get('status')}")
                            st.write("**Divergências Encontradas:**")
                            for d in result.get('divergencias', []):
                                st.write(f"- {d}")
                            st.write("**Riscos Aduaneiros:**")
                            for r in result.get('riscos_aduaneiros', []):
                                st.write(f"- {r}")
                        except Exception as e:
                            st.error(f"Erro na auditoria: {e}")
            else:
                st.write("Nenhum documento neste notebook ainda.")

        with col2:
            st.write("### Chat Interface")
            render_chat_interface(selected_nb_id)

from openai import OpenAI

def render_chat_interface(notebook_id):

    state_key = f"messages_{notebook_id}"

    # Initialize chat history
    if state_key not in st.session_state:
        st.session_state[state_key] = [{"role": "assistant", "content": "Olá! Sou seu assistente PM Logística. Como posso ajudar com os documentos deste processo hoje?"}]

    # Container for chat history
    chat_container = st.container(height=500)

    with chat_container:
        for message in st.session_state[state_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "citations" in message and message["citations"]:
                    st.caption("Fontes:")
                    for c in message["citations"]:
                        st.caption(f"- Doc ID: {c['document_id']} (Pág: {c.get('page', 'N/A')})")

    # Chat input
    if prompt := st.chat_input("Pergunte qualquer coisa sobre o processo..."):
        st.session_state[state_key].append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Buscando informações..."):
                    try:
                        with get_db() as db:
                            # 1. RAG Search
                            context_chunks = search_service.hybrid_search(db, prompt, str(notebook_id))

                        system_prompt = "Você é um assistente especialista em logística aduaneira da PM Logística. Use as fontes fornecidas para responder."
                        context_text = "\n\n".join([f"Fonte: {c.document_id} Pág: {c.page_number}\n{c.content}" for c in context_chunks])

                        api_messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"Contexto Recueperado:\n{context_text}"}]
                        api_messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state[state_key]])

                        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                        response = client.chat.completions.create(model="gemma3:1b", messages=api_messages)

                        answer = response.choices[0].message.content
                        citations = [{"document_id": str(c.document_id), "page": c.page_number} for c in context_chunks]

                        message_placeholder.markdown(answer)
                        st.session_state[state_key].append({"role": "assistant", "content": answer, "citations": citations})

                        if citations:
                            st.caption("Fontes:")
                            for c in citations:
                                st.caption(f"- Doc ID: {c['document_id']} (Pág: {c.get('page', 'N/A')})")

                    except Exception as e:
                        st.error(f"Erro ao processar consulta: {e}")

def render_admin_dashboard():
    st.header("Admin Dashboard (Base Global)")

    with get_db() as db:

        st.subheader("Upload de Regulamentação")
        uploaded_file = st.file_uploader("Clique para subir arquivos PDF", type=["pdf", "docx", "png", "jpg"], key="global_uploader")

        if uploaded_file is not None:
            if st.button("Enviar para Base Global"):
                with st.spinner("Processando..."):
                    temp_dir = "temp_storage"
                    os.makedirs(temp_dir, exist_ok=True)
                    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # run async function in sync context
                    asyncio.run(ingestion_service.ingest_document(db, file_path, uploaded_file.name, is_global=True))
                    st.success("Documento processado com sucesso!")
                    st.rerun()

        st.subheader("Documentos Globais")
        docs = db.query(Document).filter(Document.is_global == True).all()

        if not docs:
            st.info("Nenhum documento na base global.")
        else:
            for doc in docs:
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    st.write(f"📄 {doc.filename}")
                with col2:
                    if st.button("🗑️", key=f"del_global_{doc.id}"):
                        db.delete(doc)
                        db.commit()
                        st.rerun()

if __name__ == "__main__":
    main()
