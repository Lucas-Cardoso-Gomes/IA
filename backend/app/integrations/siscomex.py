class SiscomexClient:
    def authenticate(self): return "MOCK_TOKEN"
    def generate_due_payload(self, data: dict): return {"data": data}
    def register_due(self, payload: dict): return {"status": "success"}

siscomex_client = SiscomexClient()
