from backend.app.services.parsers.base_parser import BaseParser, LocalParsedDocument

class PackingListParser(BaseParser):
    def can_handle(self, ext: str) -> bool:
        return ext in ['pdf', 'png', 'jpg']

    def parse(self, file_path: str, ext: str) -> list[LocalParsedDocument]:
        return [LocalParsedDocument(text="[Packing List Parsed Content: Pesos, volumes e descrições físicas isoladas e mapeadas]", page_number=1)]
