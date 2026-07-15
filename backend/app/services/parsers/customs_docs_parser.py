from backend.app.services.parsers.base_parser import BaseParser, LocalParsedDocument

class CustomsDocsParser(BaseParser):
    def can_handle(self, ext: str) -> bool:
        return ext in ['pdf', 'png', 'jpg']

    def parse(self, file_path: str, ext: str) -> list[LocalParsedDocument]:
        return [LocalParsedDocument(text="[Customs Doc Parsed Content: DI, DU-E, MIC-DTA extraídos com foco em cruzamento fiscal]", page_number=1)]
