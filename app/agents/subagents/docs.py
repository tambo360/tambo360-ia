"""DocsSubAgent — RAG over cow types, protocols and operational manuals."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def buscar_documentacion(consulta: str) -> str:
    """Buscar en documentos internos: razas, protocolos, SOPs (stub RAG)."""
    return (
        f"[DocsSubAgent stub] RAG aún no conectado. "
        f"consulta={consulta}"
    )


docs_subagent = build_subagent(
    tools=[buscar_documentacion],
    system_prompt=(
        "Sos el especialista de documentación de Tambo360. "
        "Respondé con protocolos, tipos de vacas y procedimientos usando la herramienta de búsqueda. "
        "Si no hay resultado, decí que no está en la base documental."
    ),
)
