-- Habilitar a extensão vetorial 
CREATE EXTENSION IF NOT EXISTS vector; 
 
-- Tabela de Espaços de Trabalho (Notebooks) 
CREATE TABLE notebooks ( 
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    title VARCHAR(255) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    user_id UUID NOT NULL 
); 
 
-- Tabela de Documentos (Fontes de Conhecimento) 
CREATE TABLE documents ( 
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    notebook_id UUID REFERENCES notebooks(id) ON DELETE CASCADE, -- NULL indica Base Global (Admin) 
    filename VARCHAR(255) NOT NULL, 
    storage_path TEXT NOT NULL, 
    is_global BOOLEAN DEFAULT FALSE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP 
); 
 
-- Tabela de Fragmentos Semânticos (Chunks / i-RAG) 
CREATE TABLE document_chunks ( 
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE, 
    content TEXT NOT NULL, 
    embedding VECTOR(1536), -- Ajustar dimensionalidade conforme o modelo (ex: OpenAI, Nomic, Qwen) 
    page_number INT, 
    bounding_box JSONB, -- Coordenadas espaciais na página original 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP 
);
