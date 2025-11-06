from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import dotenv
import os

dotenv.load_dotenv(".env")

from modules import observability
from modules import connection
from modules import questions


api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.middleware("http")
async def measure_response_time(request: Request, call_next):
    tracking_id = request.method + " /" + request.url.path.split("/")[1]
    with observability.REQUEST_TIME_METRICS.labels(endpoint=tracking_id).time():
        with observability.tracer.start_as_current_span(tracking_id + "-endpoint"):
            return await call_next(request)


@api.get("/")
async def get_home() -> Response:
    return Response("200")

@api.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@api.get("/media/{media_name}")
async def static_media(media_name: str, request: Request) -> Response:
    path = "../media/" + media_name
    if not os.path.exists(path):
        observability.api_logger.error(f"Failed to access media: medianame={media_name} from client_host={request.client.host} (FILE NOT FOUND)")
        return Response(None, 404)
    
    with open(path, "rb") as file:
        observability.api_logger.info(f"Accessing media: medianame={media_name} from: client_host={request.client.host}")
        return Response(file.read(), media_type="video/mp4")

@api.get("/test-result/{result}")
async def get_test_result(result: str) -> Response:
    """ Increment metrics based on the result from the test process """
    if result == "pass":
        observability.PASSED_TESTS.inc()
    if result == "fail":
        observability.FAILED_TESTS.inc()

@api.websocket("/ws/{mode}/{client_id}")
async def ws_quiz_loop(mode: str, ws_client: WebSocket, client_id: str) -> None:
    if mode not in ("practice", "exam"):
        observability.api_logger.error(f"Failed to initiate WS connection: invalid mode={mode} by client_id={client_id} client_host={ws_client.client.host}")    
        return
        
    observability.api_logger.info(f"Started WS connection for mode={mode} by client_id={client_id} client_host={ws_client.client.host}")

    questions_manager = questions.get_questions_manager_base(mode)
    await connection.WebSocketHandler(client_id, ws_client, mode, questions_manager).initialize()
        
        
if __name__ == "__main__":
    FastAPIInstrumentor.instrument_app(api)
    uvicorn.run(api)
