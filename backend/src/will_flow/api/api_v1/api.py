from fastapi import APIRouter

from will_flow.api.api_v1.endpoints import users, flows, chat, knowledge_base

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(flows.router, prefix="/flows", tags=["flows"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-bases", tags=["knowledge-bases"]) 