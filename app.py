import streamlit as st
import asyncio
import os
import uuid
import json

from backend.app.database import SessionLocal
from backend.app.models.models import Notebook, Document
import requests
import time
from backend.app.services.search import search_service
from backend.app.services.ingestion import ingestion_service
from backend.app.database import SessionLocal, engine, Base
from backend.app.tasks import ingest_document_task, audit_notebook_task
from backend.app.models.models import Notebook, Document, ChatMessage

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
    page = st.sidebar.radio("Ir para", ["Notebook Workspace", "Chat Avulso", "Admin Dashboard"])

    if page == "Notebook Workspace":
        render_notebook_workspace()
    elif page == "Chat Avulso":
        render_standalone_chat()
    elif page == "Admin Dashboard":
        render_admin_dashboard()

def render_standalone_chat():
    st.header("Chat Avulso")

    with get_db() as db:
        # Check if standalone notebook exists, create if not
        standalone_nb = db.query(Notebook).filter(Notebook.id == "standalone").first()
        if not standalone_nb:
            standalone_nb = Notebook(id="standalone", title="Chat Avulso", user_id="system")
            db.add(standalone_nb)
            db.commit()

        col1, col2 = st.columns([0.4, 0.6])

        with col1:
            st.write("### Anexos Temporários")
            uploaded_files = st.file_uploader("Adicionar Fonte(s) (PDF, DOCX, Imagem)", type=["pdf", "docx", "png", "jpg"], key="standalone_uploader", accept_multiple_files=True)

            if uploaded_files:
                if st.button("Adicionar Documento(s)"):
                    temp_dir = "temp_storage"
                    os.makedirs(temp_dir, exist_ok=True)

                    for uploaded_file in uploaded_files:
                        file_size_mb = uploaded_file.size / (1024 * 1024)
                        if file_size_mb > 100:
                            st.warning(f"O arquivo {uploaded_file.name} possui {file_size_mb:.2f}MB (maior que 100MB). O processamento em segundo plano pode demorar. Você pode fechar e voltar mais tarde.")

                        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        task = ingest_document_task.delay(file_path, uploaded_file.name, "standalone", False)
                        st.info(f"Tarefa de ingestão de {uploaded_file.name} enviada (ID: {task.id}).")

            docs = db.query(Document).filter(Document.notebook_id == "standalone").all()
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
            else:
                st.write("Nenhum documento temporário neste chat.")

        with col2:
            st.write("### Chat Interface")
            render_chat_interface("standalone")

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

        notebooks = db.query(Notebook).filter(Notebook.id != "standalone").all()
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
            uploaded_files = st.file_uploader("Adicionar Fonte(s) (PDF, DOCX, Imagem)", type=["pdf", "docx", "png", "jpg"], key="nb_uploader", accept_multiple_files=True)

            if uploaded_files:
                if st.button("Adicionar Documento(s)"):
                    temp_dir = "temp_storage"
                    os.makedirs(temp_dir, exist_ok=True)

                    for uploaded_file in uploaded_files:
                        file_size_mb = uploaded_file.size / (1024 * 1024)
                        if file_size_mb > 100:
                            st.warning(f"O arquivo {uploaded_file.name} possui {file_size_mb:.2f}MB (maior que 100MB). O processamento em segundo plano pode demorar. Você pode fechar e voltar mais tarde.")

                        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        task = ingest_document_task.delay(file_path, uploaded_file.name, selected_nb_id, False)
                        st.info(f"Tarefa de ingestão de {uploaded_file.name} enviada (ID: {task.id}).")

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
                    task = audit_notebook_task.delay(selected_nb_id)
                    st.session_state[f"audit_task_{selected_nb_id}"] = task.id
                    st.info(f"Auditoria enviada para a fila! (Task ID: {task.id})")

                if f"audit_task_{selected_nb_id}" in st.session_state:
                    task_id = st.session_state[f"audit_task_{selected_nb_id}"]
                    if st.button("Consultar Status da Auditoria"):
                        try:
                            res = requests.get(f"http://localhost:8000/tasks/{task_id}").json()
                            if res["task_status"] == "SUCCESS":
                                result = res["task_result"]
                                st.success("Auditoria Concluída!")
                                st.write("#### Resultado da Auditoria")
                                st.write(f"**Status:** {result.get('status')}")
                                st.write("**Divergências Encontradas:**")
                                for d in result.get('divergencias', []):
                                    st.write(f"- {d}")
                                st.write("**Riscos Aduaneiros:**")
                                for r in result.get('riscos_aduaneiros', []):
                                    st.write(f"- {r}")
                                del st.session_state[f"audit_task_{selected_nb_id}"]
                            elif res["task_status"] in ["PENDING", "STARTED"]:
                                st.warning("Ainda processando...")
                            else:
                                st.error(f"Erro na auditoria: {res['task_result']}")
                                del st.session_state[f"audit_task_{selected_nb_id}"]
                        except Exception as e:
                            st.error(f"Erro ao conectar com API de tarefas: {e}")
            else:
                st.write("Nenhum documento neste notebook ainda.")

        with col2:
            st.write("### Chat Interface")
            render_chat_interface(selected_nb_id)

from openai import OpenAI

def render_chat_interface(notebook_id):

    state_key = f"messages_{notebook_id}"

    with get_db() as db:
        if state_key not in st.session_state:
            db_messages = db.query(ChatMessage).filter(ChatMessage.notebook_id == str(notebook_id)).order_by(ChatMessage.created_at).all()
            if db_messages:
                st.session_state[state_key] = [{"role": m.role, "content": m.content, "citations": m.citations} for m in db_messages]
            else:
                initial_msg = {"role": "assistant", "content": "Olá! Sou seu assistente PM Logística. Como posso ajudar com os documentos deste processo hoje?"}
                st.session_state[state_key] = [initial_msg]
                db_msg = ChatMessage(notebook_id=str(notebook_id), role=initial_msg["role"], content=initial_msg["content"])
                db.add(db_msg)
                db.commit()

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
            user_msg = {"role": "user", "content": prompt}
            st.session_state[state_key].append(user_msg)

            db_user_msg = ChatMessage(notebook_id=str(notebook_id), role=user_msg["role"], content=user_msg["content"])
            db.add(db_user_msg)
            db.commit()

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

                        system_prompt = """
                            Você é um assistente especialista em logística aduaneira da PM Logística.
                            Regras OBRIGATÓRIAS:
                            1. Responda APENAS com base no 'Contexto Recuperado' fornecido.
                            2. NUNCA invente nomes, datas, números ou informações que não estejam explicitamente no texto.
                            3. Se a informação não estiver no contexto, responda: 'Não encontrei essa informação no documento'.
                            """
                        context_text = "\n\n".join([f"Fonte: {c.document_id} Pág: {c.page_number}\n{c.content}" for c in context_chunks])

                        api_messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"Contexto Recueperado:\n{context_text}"}]
                        api_messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state[state_key]])

                        from backend.app.config import settings
                        import os

                        if settings.OPENAI_TELEMETRY.lower() == 'false':
                            os.environ["OPENAI_TELEMETRY"] = "0"
                            os.environ["OPENAI_DISABLE_TELEMETRY"] = "1"

                        client = OpenAI(base_url=settings.OLLAMA_BASE_URL, api_key=settings.OLLAMA_API_KEY)
                        response = client.chat.completions.create(model="gemma3:4b", messages=api_messages, temperature=0.0)

                        answer = response.choices[0].message.content
                        citations = [{"document_id": str(c.document_id), "page": c.page_number} for c in context_chunks]

                        message_placeholder.markdown(answer)
                        assistant_msg = {"role": "assistant", "content": answer, "citations": citations}
                        st.session_state[state_key].append(assistant_msg)

                        db_assistant_msg = ChatMessage(notebook_id=str(notebook_id), role=assistant_msg["role"], content=assistant_msg["content"], citations=citations)
                        db.add(db_assistant_msg)
                        db.commit()

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
        uploaded_files = st.file_uploader("Clique para subir arquivos PDF", type=["pdf", "docx", "png", "jpg"], key="global_uploader", accept_multiple_files=True)

        if uploaded_files:
            if st.button("Enviar para Base Global"):
                with st.spinner("Processando..."):
                    temp_dir = "temp_storage"
                    os.makedirs(temp_dir, exist_ok=True)

                    for uploaded_file in uploaded_files:
                        file_size_mb = uploaded_file.size / (1024 * 1024)
                        if file_size_mb > 100:
                            st.warning(f"O arquivo {uploaded_file.name} possui {file_size_mb:.2f}MB (maior que 100MB). O processamento em segundo plano pode demorar. Você pode fechar e voltar mais tarde.")

                        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # run async function in sync context
                        asyncio.run(ingestion_service.ingest_document(db, file_path, uploaded_file.name, is_global=True))
                    st.success("Documento(s) processado(s) com sucesso!")
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
