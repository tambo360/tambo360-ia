"""Coordinator agent: routes user questions to domain subagents."""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from app.agents.llm import get_chat_model
from app.agents.runtime import as_supervisor_tool, extract_last_text
from app.agents.subagents.clima import clima_subagent
from app.agents.subagents.docs import docs_subagent
from app.agents.subagents.finanzas import finanzas_subagent
from app.agents.subagents.merma import merma_subagent
from app.agents.subagents.movimientos import movimientos_subagent
from app.agents.subagents.produccion import produccion_subagent
from app.agents.subagents.sanidad import sanidad_subagent

SUPERVISOR_PROMPT = """Sos el coordinador de Tambo360.

Tu trabajo es entender la pregunta del usuario y delegar a uno o más especialistas.
Podés llamar varias herramientas en paralelo si la consulta cruza dominios.

Especialistas:
- call_merma_subagent: mermas, pérdidas y desvíos de lotes vs promedio de categoría
- call_produccion_subagent: volúmenes, lotes, productos y categorías
- call_finanzas_subagent: costos directos, márgenes y KPIs monetarios
- call_movimientos_subagent: movimientos de hacienda, stock y transferencias
- call_sanidad_subagent: salud animal, tratamientos y eventos veterinarios
- call_clima_subagent: clima y su impacto operativo
- call_docs_subagent: RAG de tipos de vacas, protocolos y documentación interna

Reglas:
1. No calculees vos números de negocio: delegá.
2. Si falta contexto (establecimiento, período), pedilo o pasalo en la query al subagente.
3. Sintetizá las respuestas de los subagentes en un informe claro en español.
4. El análisis batch de merma (POST /tambo/analyze) sigue en TamboEngine; vos sos el canal conversacional.
"""


def _build_supervisor():
    tools = [
        as_supervisor_tool(
            merma_subagent,
            name="call_merma_subagent",
            description="Delegá consultas de merma, pérdidas y outliers de lotes.",
        ),
        as_supervisor_tool(
            produccion_subagent,
            name="call_produccion_subagent",
            description="Delegá consultas de producción, lotes y volúmenes.",
        ),
        as_supervisor_tool(
            finanzas_subagent,
            name="call_finanzas_subagent",
            description="Delegá consultas de costos, márgenes y finanzas.",
        ),
        as_supervisor_tool(
            movimientos_subagent,
            name="call_movimientos_subagent",
            description="Delegá consultas de movimientos de hacienda o stock.",
        ),
        as_supervisor_tool(
            sanidad_subagent,
            name="call_sanidad_subagent",
            description="Delegá consultas de sanidad y salud animal.",
        ),
        as_supervisor_tool(
            clima_subagent,
            name="call_clima_subagent",
            description="Delegá consultas climáticas relevantes al tambo.",
        ),
        as_supervisor_tool(
            docs_subagent,
            name="call_docs_subagent",
            description="Delegá búsquedas en protocolos, razas y documentación (RAG).",
        ),
    ]
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=SUPERVISOR_PROMPT,
    )


_supervisor = None


def get_supervisor():
    """Lazy singleton so FastAPI import does not build 8 graphs twice."""
    global _supervisor
    if _supervisor is None:
        _supervisor = _build_supervisor()
    return _supervisor


async def ask_supervisor(query: str) -> str:
    """Run one user question through the coordinator."""
    response = await get_supervisor().ainvoke(
        {"messages": [HumanMessage(content=query)]}
    )
    return extract_last_text(response)
