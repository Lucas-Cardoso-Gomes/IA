from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import documents, chat, actions

app = FastAPI(title="PM Logística - Inteligência Documental")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bem-vindo à API de Inteligência Documental da PM Logística"}

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
