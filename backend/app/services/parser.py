import os

# Classe que imita a estrutura de retorno do LlamaParse para não quebrar o ingestion.py
class LocalParsedDocument:
    def __init__(self, text, page_number):
        self.text = text
        self.metadata = {
            "page_number": page_number,
            "bounding_box": {}
        }

class ParserService:
    def __init__(self):
        # Nenhuma API Key é necessária para rodar localmente
        pass

    async def parse_file(self, file_path: str):
        documents = []
        ext = file_path.lower().split('.')[-1]

        try:
            # Processamento de arquivos PDF
            if ext == "pdf":
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for i, page in enumerate(doc):
                    text = page.get_text("text")
                    if text.strip():
                        documents.append(LocalParsedDocument(text=text, page_number=i + 1))

            # Processamento de arquivos Word
            elif ext == "docx":
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                documents.append(LocalParsedDocument(text=text, page_number=1))

            # Adicione outras extensões se necessário
            else:
                documents.append(LocalParsedDocument(
                    text=f"[Conteúdo não extraído. Formato {ext} requer OCR ou biblioteca específica]", 
                    page_number=1
                ))

        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
            
        # Fallback caso o documento seja uma imagem ou PDF escaneado (sem texto selecionável)
        if not documents:
             documents.append(LocalParsedDocument(text="[Documento vazio ou necessita de OCR (Reconhecimento Óptico de Caracteres)]", page_number=1))
             
        return documents

parser_service = ParserService()