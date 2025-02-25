from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import settings


class TelemetryProvider:
    def __init__(self):
        resource = Resource.create(
            attributes={
                "service.name": settings.PROJECT_NAME,
                "service.version": "1.0.0",
                "deployment.environment": settings.ENVIRONMENT,
            }
        )

        # Configure the tracer
        self.tracer_provider = TracerProvider(resource=resource)

        # Configure the OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT, insecure=True)

        # Add BatchSpanProcessor to the tracer
        self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set the tracer provider
        trace.set_tracer_provider(self.tracer_provider)

    def instrument_fastapi(self, app):
        """Instrument FastAPI before app startup"""
        FastAPIInstrumentor.instrument_app(app)

    def instrument_other(self, engine):
        """Instrument other components after app startup"""
        # Instrument SQLAlchemy using the sync engine
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
            service_name=settings.PROJECT_NAME,
        )

        # Instrument Redis
        RedisInstrumentor().instrument()


def setup_telemetry():
    """Configure OpenTelemetry with OTLP exporter."""
    return TelemetryProvider()
