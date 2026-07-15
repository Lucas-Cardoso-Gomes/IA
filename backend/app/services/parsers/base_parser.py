class LocalParsedDocument:
    def __init__(self, text, page_number):
        self.text = text
        self.metadata = {
            "page_number": page_number,
            "bounding_box": {}
        }

class BaseParser:
    def can_handle(self, ext: str) -> bool:
        raise NotImplementedError

    def parse(self, file_path: str, ext: str) -> list[LocalParsedDocument]:
        raise NotImplementedError
