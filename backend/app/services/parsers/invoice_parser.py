from backend.app.services.parsers.base_parser import BaseParser, LocalParsedDocument

class InvoiceParser(BaseParser):
    def can_handle(self, ext: str) -> bool:
        return ext in ['pdf', 'png', 'jpg'] # Específico para lógica que identificasse "Invoice" (simplificado para exemplo)

    def parse(self, file_path: str, ext: str) -> list[LocalParsedDocument]:
        # Implementação de extração focada em Invoices (Commercial Invoices)
        # Por exemplo, uso de regex para NCM, valores ou layout específico.
        # Por enquanto, fallback para texto genérico ou mock
        return [LocalParsedDocument(text="[Invoice Parsed Content: Estrutura comercial, valores, NCM extraídos de forma otimizada]", page_number=1)]
