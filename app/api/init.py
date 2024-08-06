from fastapi import APIRouter
from app.api.endpoints import chatbot, session, paramView, userView

router = APIRouter()

router.include_router(chatbot.router)
router.include_router(session.router)
router.include_router(paramView.router)
router.include_router(userView.router)
# router.include_router(speech.router)