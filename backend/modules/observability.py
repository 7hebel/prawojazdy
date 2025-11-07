from prometheus_client import Summary, Gauge
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
import logging_loki
import logging
import os


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


class ColoredLogsFormatter(logging.Formatter):
    reset = "\x1b[0m"
    format = "%(levelname)s | %(asctime)s - %(message)s \033[90m(%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: "\033[36m" + format + reset,
        logging.INFO: "\033[34m" + format + reset,
        logging.WARNING: "\033[33m" + format + reset,
        logging.ERROR: "\033[31m" + format + reset,
        logging.CRITICAL: "\033[35m" + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%H:%M:%S")
        return formatter.format(record)


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
    
    ch = logging.StreamHandler()
    ch.setFormatter(ColoredLogsFormatter())
    logger.addHandler(ch)
    
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


# Loggers (Loki)
client_logger = __get_logger("client-log")
api_logger = __get_logger("api-log")
db_logger = __get_logger("db-log")
test_logger = __get_logger("test-log")

# Tracer (Tempo)
tracer = __get_tracer()

# Metrics (Prometheus -> Mimir)
REQUEST_TIME_METRICS = Summary(
    "request_processing_time", 
    "Time spent processing the request.", 
    ["endpoint"]
)

TOTAL_ANSWERS = Gauge(
    "quiz_total_answers", 
    "Total answers given per question.",
    ["question_index", "client_id"]
)

CORRECT_ANSWERS = Gauge(
    "quiz_correct_answers",
    "Correct answers given per question.",
    ["question_index", "client_id"]
)

INCORRECT_ANSWERS = Gauge(
    "quiz_incorrect_answers",
    "Incorrect answers given per question.",
    ["question_index", "client_id"]
)

TIME_ANSWERING = Summary(
    "quiz_time_answering_seconds",
    "Time spent answering each question.",
    ["question_index", "client_id"]
)

PASSED_TESTS = Gauge(
    "tests_passed",
    "Total completly passed test sequences amount."
)

FAILED_TESTS = Gauge(
    "tests_failed",
    "Total failed tests amount."
)

EXAM_PASSED = Gauge(
    "exam_passed",
    "Total passed exams",
    ["client_id"]
)

EXAM_FAILED = Gauge(
    "exam_failed",
    "Total failed exams",
    ["client_id"]
)

EXAM_TOTAL_TIME = Summary(
    "exam_total_time_seconds",
    "Time spent resolving the entire exam.",
    ["client_id"]
) 

EXAM_POINTS = Summary(
    "exam_points",
    "Amount of points in each exam",
    ["client_id"]
)

