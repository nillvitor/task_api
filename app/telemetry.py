from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from .config import settings

# from opentelemetry.sdk.trace.export import ConsoleSpanExporter


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

        # # Optional: Add console exporter for debugging
        # self.tracer_provider.add_span_processor(
        #     BatchSpanProcessor(ConsoleSpanExporter())
        # )

        # Set the tracer provider
        trace.set_tracer_provider(self.tracer_provider)

        # Set up context propagation
        self.propagator = TraceContextTextMapPropagator()

    def instrument_fastapi(self, app):
        """Instrument FastAPI before app startup"""
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=self.tracer_provider,
            excluded_urls="^/docs,^/openapi.json",
        )

    def instrument_other(self, engine):
        """Instrument other components like SQLAlchemy and Redis"""
        # Instrument SQLAlchemy - use sync_engine for async engines
        if hasattr(engine, "sync_engine"):
            SQLAlchemyInstrumentor().instrument(
                engine=engine.sync_engine,
                tracer_provider=self.tracer_provider,
            )
        else:
            # Fallback for synchronous engines
            SQLAlchemyInstrumentor().instrument(
                engine=engine,
                tracer_provider=self.tracer_provider,
            )

        # Instrument Redis
        RedisInstrumentor().instrument(
            tracer_provider=self.tracer_provider,
        )


def setup_telemetry():
    """Configure OpenTelemetry with OTLP exporter."""
    return TelemetryProvider()
