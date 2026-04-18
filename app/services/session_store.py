"""跨进程共享的 session 存储（Redis）；不可用时回退到内存 dict（仅单进程可用）。"""
import json
import logging
from typing import Any, Optional

from app.config.config import SESSION_REDIS_TTL_SECONDS
from app.models.Session import Message, Session, sessions

KEY_PREFIX = "weldgpt:session:"


def session_key(external_id: str) -> str:
    return f"{KEY_PREFIX}{external_id}"


def session_to_json(session: Session) -> str:
    rag: list[dict[str, Any]] = []
    for m in session.rag_messages:
        if isinstance(m, Message):
            rag.append({"query": m.query, "response": m.response})
        else:
            rag.append({"query": m["query"], "response": m["response"]})
    payload = {
        "id": session.id,
        "shared_data": session.shared_data,
        "original_data": session.original_data,
        "messages": session.messages,
        "rag_messages": rag,
        "state": session.state,
        "messages_all_user": session.messages_all_user,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def session_from_json(raw: str) -> Session:
    d = json.loads(raw)
    s = Session.__new__(Session)
    s.id = d["id"]
    s.shared_data = dict(d.get("shared_data") or {})
    s.original_data = dict(d.get("original_data") or {})
    s.messages = list(d.get("messages") or [])
    s.rag_messages = []
    for m in d.get("rag_messages") or []:
        s.rag_messages.append(Message(query=m["query"], response=m["response"]))
    s.state = int(d.get("state", 0))
    s.messages_all_user = list(d.get("messages_all_user") or [])
    return s


async def get_session(redis: Any, external_id: str) -> Optional[Session]:
    if redis is not None:
        try:
            raw = await redis.get(session_key(external_id))
            if raw:
                return session_from_json(raw)
        except Exception:
            logging.exception("Redis get session failed for id=%s", external_id)
            raise
        # Redis 已启用且 key 不存在：再查本进程内存（兼容预置 test-id-*）
        return sessions.get(external_id)
    return sessions.get(external_id)


async def save_session(redis: Any, session: Session, external_id: str) -> None:
    if redis is not None:
        try:
            await redis.set(
                session_key(external_id),
                session_to_json(session),
                ex=SESSION_REDIS_TTL_SECONDS,
            )
            return
        except Exception as e:
            logging.exception("Redis save session failed for id=%s", external_id)
            raise RuntimeError(
                "Redis session save failed; refusing in-memory fallback while Redis is enabled"
            ) from e
    sessions[external_id] = session
