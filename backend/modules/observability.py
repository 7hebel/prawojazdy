from prometheus_client import Summary, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response, Request
from opentelemetry import trace
import logging_loki
import logging
import uvicorn
import random
import time
import sys
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LogsEnrichment(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            record.trace_id = format(ctx.trace_id, '032x')
            record.span_id = format(ctx.span_id, '016x')
        else:
            record.trace_id = None
            record.span_id = None
        return True


def __get_logger(name: str) -> logging.Logger:
    loki_logs_handler = logging_loki.LokiHandler(
        url=os.getenv("LGTM_LOKI_API"),
        tags={"app": name},
        version="1",
    )
    formatter = logging.Formatter('[%(name)s] %(asctime)s - %(levelname)s - %(message)s  trace_id=%(trace_id)s span_id=%(span_id)s')
    loki_logs_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addFilter(LogsEnrichment())
    logger.addHandler(loki_logs_handler)
    return logger

def __get_tracer() -> trace.Tracer:
    trace_resource = Resource.create({
        "service.name": "prawojazdy"
    })
    trace.set_tracer_provider(TracerProvider(resource=trace_resource))
    tracer_provider = trace.get_tracer_provider()
    
    otlp_exporter = OTLPSpanExporter(endpoint=os.getenv("LGTM_OTEL_API"))
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    return tracer_provider.get_tracer(__name__)


client_logger = __get_logger("client-log")
api_logger = __get_logger("api-log")
db_logger = __get_logger("db-log")

tracer = __get_tracer()


REQUEST_TIME_METRICS = Summary("request_processing_time", "Time spent processing the request.", ["endpoint"])
