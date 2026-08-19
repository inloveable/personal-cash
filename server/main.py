"""FastAPI 入口：REST /api/v1 + MCP /mcp + 前端静态托管 + token 鉴权。

本地开发：
  uvicorn server.main:app --reload --port 8000
前端构建产物存在时，/ 直接托管；否则仅提供 API。
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import settings
from .db import init_db
from .api.routes import router as api_router
from .mcp_server import mcp

WEB_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "dist")

mcp_app = mcp.http_app(path="/", transport="streamable-http")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    async with mcp_app.lifespan(app):
        yield


class TokenGuardMiddleware(BaseHTTPMiddleware):
    """/mcp 路径的 Bearer 校验（REST 走 FastAPI dependency）。"""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            auth = request.headers.get("authorization", "")
            if not auth.lower().startswith("bearer ") or auth[7:] != settings.api_token:
                return JSONResponse({"detail": "无效或缺失的访问令牌"}, status_code=401)
        return await call_next(request)


app = FastAPI(title="AI Ledger", version="0.1.0", lifespan=lifespan)
app.add_middleware(TokenGuardMiddleware)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
app.mount("/mcp", mcp_app)


@app.get("/api/health")
def health():
    return {"ok": True}


class SPAStaticFiles(StaticFiles):
    """SPA 回退：静态文件 404 时回退到 index.html（history 路由刷新/直达链接）。"""

    async def get_response(self, path: str, scope):
        from starlette.exceptions import HTTPException as StarletteHTTPException

        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as e:
            if e.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


if os.path.isdir(WEB_DIST):
    app.mount("/", SPAStaticFiles(directory=WEB_DIST, html=True), name="web")
