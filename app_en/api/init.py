from fastapi import APIRouter
from app_en.api.endpoints import chatbot, session

router = APIRouter()

router.include_router(chatbot.router)
router.include_router(session.router)
# router.include_router(speech.router)