"""Domain subagents. Each one owns a narrow set of tools."""

from app.agents.subagents.clima import clima_subagent
from app.agents.subagents.docs import docs_subagent
from app.agents.subagents.finanzas import finanzas_subagent
from app.agents.subagents.merma import merma_subagent
from app.agents.subagents.movimientos import movimientos_subagent
from app.agents.subagents.produccion import produccion_subagent
from app.agents.subagents.sanidad import sanidad_subagent

__all__ = [
    "clima_subagent",
    "docs_subagent",
    "finanzas_subagent",
    "merma_subagent",
    "movimientos_subagent",
    "produccion_subagent",
    "sanidad_subagent",
]
