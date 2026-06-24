from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from utils.rag_engine import get_retriever

def get_llm(model_name="gemma3:1b"):
    """
    Returns an instance of the Ollama LLM with the specified model.
    """
    # Requires Ollama to be running locally on default port 11434
    return Ollama(model=model_name)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain(model_name="gemma3:1b"):
    """
    Creates a conversational retrieval chain for the Admin Knowledge Base using LCEL.
    """
    llm = get_llm(model_name=model_name)
    retriever = get_retriever()
    
    # Define prompt template for RAG
    template = """Você é um assistente especialista em comércio exterior, importação e exportação.
Use os trechos de contexto a seguir para responder à pergunta. 
Se você não sabe a resposta baseada no contexto, diga que não sabe e não invente informações.

Contexto:
{context}

Pergunta: {question}

Resposta:"""
    
    prompt = PromptTemplate.from_template(template)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def get_document_qa_chain(model_name="gemma3:1b"):
    """
    Creates a simple QA chain for analyzing a specific uploaded document using LCEL.
    """
    llm = get_llm(model_name=model_name)
    
    template = """Você é um assistente especialista em comércio exterior. 
O usuário fez o upload de um documento de importação/exportação. 
Aqui está o texto extraído do documento:

{context}

Com base nesse documento, responda à pergunta do usuário. 
Se a informação não estiver no documento, diga que não encontrou.

Pergunta: {question}

Resposta:"""
    
    prompt = PromptTemplate.from_template(template)
    
    doc_chain = prompt | llm | StrOutputParser()
    
    return doc_chain

def ask_rag(question, model_name="gemma3:1b"):
    """
    Asks a question using the Admin Knowledge Base.
    """
    chain = get_rag_chain(model_name=model_name)
    response = chain.invoke(question)
    return response

def ask_document(question, document_text, model_name="gemma3:1b"):
    """
    Asks a question about a specific document context.
    """
    chain = get_document_qa_chain(model_name=model_name)
    response = chain.invoke({"question": question, "context": document_text})
    return response
