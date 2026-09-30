import json
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1 import tambo
from app.models.schemas import PredictionRequest, PredictionResponse, PredictionResult
from app.services import tambo_engine

VALID_REQUEST = {
    "tema": "produccion",
    "datos": {"historial": [10, 12, 14]},
    "configuracion": {"horizonte_dias": 7},
}


def test_prediction_request_accepts_supported_topic():
    request = PredictionRequest.model_validate(VALID_REQUEST)

    assert request.tema == "produccion"


@pytest.mark.parametrize(
    "overrides",
    [
        {"tema": "desconocido"},
        {"datos": {}},
        {"configuracion": {"x": 1}, "campo_extra": True},
    ],
)
def test_prediction_request_rejects_invalid_input(overrides):
    payload = {**VALID_REQUEST, **overrides}

    with pytest.raises(ValidationError):
        PredictionRequest.model_validate(payload)


def test_prediction_request_rejects_non_finite_nested_numbers():
    payload = {**VALID_REQUEST, "datos": {"historial": [1.0, float("nan")]}}

    with pytest.raises(ValidationError):
        PredictionRequest.model_validate(payload)


def test_prediction_response_validates_confidence():
    with pytest.raises(ValidationError):
        PredictionResponse(
            tema="produccion",
            prediccion={"estimacion": 15},
            horizonte="7 días",
            confianza=1.2,
            explicacion="Estimación basada en el historial.",
        )


@pytest.mark.asyncio
async def test_prediction_service_sends_validated_payload_to_ai(monkeypatch):
    request = PredictionRequest.model_validate(VALID_REQUEST)
    generated = PredictionResult(
        prediccion={"estimacion": 15},
        horizonte="7 días",
        confianza=0.82,
        explicacion="Estimación basada en el historial.",
    )
    generate_prediction = AsyncMock(return_value=generated)
    monkeypatch.setattr(
        tambo_engine.ai_service,
        "generate_prediction",
        generate_prediction,
    )

    response = await tambo_engine.predict(request)

    messages = generate_prediction.await_args.args[0]
    sent_payload = json.loads(messages[1].content)
    assert sent_payload == request.model_dump(mode="json")
    assert response.tema == request.tema
    assert response.prediccion == generated.prediccion


def test_predict_endpoint_returns_structured_prediction(monkeypatch):
    async def fake_predict(data):
        return PredictionResponse(
            tema=data.tema,
            prediccion={"estimacion": 15},
            horizonte="7 días",
            confianza=0.82,
            explicacion="Estimación basada en el historial.",
        )

    monkeypatch.setattr(tambo_engine, "predict", fake_predict)
    app = FastAPI()
    app.include_router(tambo.router, prefix="/api/v1")

    response = TestClient(app).post("/api/v1/tambo/predict", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json() == {
        "tema": "produccion",
        "prediccion": {"estimacion": 15},
        "horizonte": "7 días",
        "confianza": 0.82,
        "explicacion": "Estimación basada en el historial.",
    }


def test_predict_endpoint_rejects_unknown_topic():
    app = FastAPI()
    app.include_router(tambo.router, prefix="/api/v1")

    response = TestClient(app).post(
        "/api/v1/tambo/predict",
        json={**VALID_REQUEST, "tema": "desconocido"},
    )

    assert response.status_code == 422
