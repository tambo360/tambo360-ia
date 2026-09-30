"""FinanzasSubAgent — direct costs, margins and monetary KPIs."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_finanzas(establecimiento_id: str, periodo: str = "") -> str:
    """Consultar costos directos y métricas económicas de lotes (stub)."""
    extra = f" periodo={periodo}" if periodo else ""
    return (
        f"[FinanzasSubAgent stub] Sin datos reales aún. "
        f"establecimiento_id={establecimiento_id}{extra}"
    )


finanzas_subagent = build_subagent(
    tools=[consultar_finanzas],
    system_prompt=(
        "Sos el especialista financiero de Tambo360. "
        "Respondé sobre costos directos, márgenes y KPIs monetarios. "
        "Usá tus herramientas. No inventes montos."
    ),
)
