"""MermaSubAgent — losses, waste, and lot deviation vs category baseline."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_mermas(establecimiento_id: str, periodo: str = "") -> str:
    """Consultar mermas, desvíos y outliers de lotes (stub)."""
    extra = f" periodo={periodo}" if periodo else ""
    return (
        f"[MermaSubAgent stub] Sin datos reales aún. "
        f"establecimiento_id={establecimiento_id}{extra}"
    )


merma_subagent = build_subagent(
    tools=[consultar_mermas],
    system_prompt=(
        "Sos el especialista de merma de Tambo360. "
        "Respondé solo sobre pérdidas, desvíos de lote y comparación con el promedio de categoría. "
        "Usá tus herramientas. No inventes números: si no hay datos, decilo."
    ),
)
