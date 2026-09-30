"""Conversational supervisor endpoint (multi-agent)."""

from fastapi import APIRouter, HTTPException

from app.agents.supervisor import ask_supervisor
from app.core.logging import get_logger
from app.models.schemas import AgentAskRequest, AgentAskResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/ask", response_model=AgentAskResponse)
async def ask_agents(body: AgentAskRequest):
    """Route a natural-language question through the supervisor and domain subagents."""
    query = body.query
    if body.establecimiento_id:
        query = f"[establecimiento_id={body.establecimiento_id}] {query}"

    try:
        respuesta = await ask_supervisor(query)
    except Exception as e:
        logger.error(f"Supervisor failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"El coordinador no pudo completar la consulta: {e}",
        )

    return AgentAskResponse(respuesta=respuesta)
