"""
API Router Exports – Centralised registration for all API routers.

Usage in main.py:
    from app.api import chat_router
    app.include_router(chat_router)
"""

from app.api.chat import router as chat_router

__all__ = ["chat_router"]
