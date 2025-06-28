from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import config
from src.services.jira_service import JiraService
from src.services.figma_service import FigmaService
from src.pdf_parser import PDFParser
from src.ai_processor import AIProcessor
from src.services.webhook_handler import WebhookHandler
from loguru import logger
from src.config import config

log_cfg = config.get("logging", {})
logger.add(
    log_cfg.get("file", "app.log"),
    rotation=log_cfg.get("max_size", "10 MB"),
    retention=log_cfg.get("backup_count", 3),  # <-- change here
    enqueue=True,
    level="INFO"
)

app = FastAPI(title="Figma-Jira Story Assistant Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jira_service = JiraService(config["jira"])
figma_service = FigmaService(config.get("figma", {}))
pdf_parser = PDFParser()
ai_processor = AIProcessor(api_key=config.get("openai_api_key") or config.get("ai", {}).get("openai_api_key"), config=config.get("ai", {}))
webhook_handler = WebhookHandler(jira_service, figma_service, pdf_parser, ai_processor)

@app.post("/webhook/jira")
async def jira_webhook(request: Request):
    try:
        payload = await request.json()
        return await webhook_handler.handle_jira_webhook(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}