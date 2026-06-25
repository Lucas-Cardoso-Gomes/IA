from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from utils.rag_engine import get_retriever

def get_llm(model_name="gemma3:1b"):
    """
    Returns an instance of the Ollama LLM with the specified model.
    """
    # Requires Ollama to be running locally on default port 11434
    return Ollama(model=model_name)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

from utils.config_manager import load_config

def get_rag_chain(model_name="gemma3:1b"):
    """
    Creates a conversational retrieval chain for the Admin Knowledge Base using LCEL with chat history.
    """
    llm = get_llm(model_name=model_name)
    retriever = get_retriever()
    config = load_config()
    
    # Contextualize question prompt
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # QA prompt
    system_prompt = config.get("prompt_rag")
    # We will format this into a ChatPromptTemplate. Assuming prompt_rag has {context} placeholder.
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

def get_document_qa_chain(model_name="gemma3:1b"):
    """
    Creates a conversational QA chain for analyzing a specific uploaded document.
    """
    llm = get_llm(model_name=model_name)
    config = load_config()
    
    system_prompt = config.get("prompt_doc")
    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    doc_chain = create_stuff_documents_chain(llm, qa_prompt)
    return doc_chain

def ask_rag(question, chat_history=[], model_name="gemma3:1b"):
    """
    Returns the chain to enable streaming and retrieving source documents in app.py
    """
    return get_rag_chain(model_name=model_name)

def ask_document(question, document_text, chat_history=[], model_name="gemma3:1b"):
    """
    Returns the chain to enable streaming in app.py
    """
    return get_document_qa_chain(model_name=model_name)
