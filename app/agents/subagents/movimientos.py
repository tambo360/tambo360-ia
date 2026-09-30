"""MovimientosSubAgent — stock, transfers and animal/product movements."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_movimientos(establecimiento_id: str, periodo: str = "") -> str:
    """Consultar movimientos de hacienda, stock o producto (stub)."""
    extra = f" periodo={periodo}" if periodo else ""
    return (
        f"[MovimientosSubAgent stub] Sin datos reales aún. "
        f"establecimiento_id={establecimiento_id}{extra}"
    )


movimientos_subagent = build_subagent(
    tools=[consultar_movimientos],
    system_prompt=(
        "Sos el especialista de movimientos de Tambo360. "
        "Respondé sobre altas, bajas, transferencias y stock. "
        "Usá tus herramientas. No inventes registros."
    ),
)
