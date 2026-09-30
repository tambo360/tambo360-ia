"""ProduccionSubAgent — lots, volumes, products and categories."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_produccion(establecimiento_id: str, periodo: str = "") -> str:
    """Consultar volúmenes de producción por producto o categoría (stub)."""
    extra = f" periodo={periodo}" if periodo else ""
    return (
        f"[ProduccionSubAgent stub] Sin datos reales aún. "
        f"establecimiento_id={establecimiento_id}{extra}"
    )


produccion_subagent = build_subagent(
    tools=[consultar_produccion],
    system_prompt=(
        "Sos el especialista de producción de Tambo360. "
        "Respondé sobre lotes, volúmenes, productos y categorías (quesos/leches). "
        "Usá tus herramientas. No inventes números."
    ),
)
