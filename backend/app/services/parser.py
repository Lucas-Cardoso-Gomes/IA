import os
from llama_parse import LlamaParse

class ParserService:
    def __init__(self):
        self.api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            num_workers=4,
            verbose=True,
            parsing_instruction="Extract tables clearly. Provide coordinates if possible."
        )

    async def parse_file(self, file_path: str):
        documents = await self.parser.aload_data(file_path)
        return documents

parser_service = ParserService()
