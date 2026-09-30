"""ClimaSubAgent — weather context that may affect production or health."""

from langchain.tools import tool

from app.agents.runtime import build_subagent


@tool
def consultar_clima(ubicacion: str, fecha: str = "") -> str:
    """Consultar clima o pronóstico relevante para el tambo (stub)."""
    extra = f" fecha={fecha}" if fecha else ""
    return (
        f"[ClimaSubAgent stub] Sin datos reales aún. "
        f"ubicacion={ubicacion}{extra}"
    )


clima_subagent = build_subagent(
    tools=[consultar_clima],
    system_prompt=(
        "Sos el especialista climático de Tambo360. "
        "Respondé sobre temperatura, precipitaciones y estrés calórico. "
        "Usá tus herramientas. No inventes mediciones."
    ),
)
