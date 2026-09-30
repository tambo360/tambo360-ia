"""SanidadSubAgent — health events, treatments and veterinary records."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_sanidad(establecimiento_id: str, periodo: str = "") -> str:
    """Consultar eventos sanitarios, tratamientos o indicadores de salud (stub)."""
    extra = f" periodo={periodo}" if periodo else ""
    return (
        f"[SanidadSubAgent stub] Sin datos reales aún. "
        f"establecimiento_id={establecimiento_id}{extra}"
    )


sanidad_subagent = build_subagent(
    tools=[consultar_sanidad],
    system_prompt=(
        "Sos el especialista de sanidad de Tambo360. "
        "Respondé sobre salud animal, tratamientos y eventos veterinarios. "
        "Usá tus herramientas. No inventes diagnósticos."
    ),
)
