from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import dotenv
import os

dotenv.load_dotenv(".env")

from modules import observability
from modules import connection
from modules import questions
from modules import accounts


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

def api_response(status: bool, content: str | dict | None = None) -> JSONResponse:
    status_code = 200 if status else 400
    observability.api_logger.debug(f"Sending API Response status_code={status_code} content={content}")
        
    return JSONResponse({
        "status": status,
        "content": content
    }, status_code)


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

@api.get("/test-result/{result}/{total_time}/{n_workers}")
async def get_test_result(result: str, total_time: float, n_workers: int) -> Response:
    """ Increment metrics based on the result from the test process """
    if result == "pass":
        observability.PASSED_TESTS.inc()
        observability.TEST_TIME.labels(n_workers=n_workers).observe(total_time)
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
        
@api.post("/account/register")
async def post_account_register(data: accounts.AccountRegisterModel, request: Request) -> JSONResponse:
    if len(data.username) < 5:
        return api_response(False, "Zbyt krótka nazwa użytkownika.")
    if len(data.username) > 32:
        return api_response(False, "Zbyt długa nazwa użytkownika.")
    if len(data.password) < 3:
        return api_response(False, "Zbyt krótkie hasło.")

    if await accounts.get_client_by_name(data.username) is not None:
        return api_response(False, "Ta nazwa użytkownika jest już zajęta.")

    iphash = accounts.hash_ip(request.client.host)
    status = await accounts.register_account(data.client_id, data.username, data.password, iphash)

    if not status:
        return api_response(False, "Rejestracja nie powiodła się.")
    return api_response(True, status)
        
@api.post("/account/login")
async def post_account_login(data: accounts.AccountLoginModel, request: Request) -> JSONResponse:
    iphash = accounts.hash_ip(request.client.host)

    if not await accounts.login_account(data.username, data.password, iphash):
        return api_response(False, "Nieprawidłowa nazwa użytkownika lub hasło.")

    account = await accounts.get_client_by_name(data.username)
    return api_response(True, account['client_id'])
        
@api.get("/account/check-username/{username}")
async def post_account_login(username: str, request: Request) -> JSONResponse:
    is_account = await accounts.get_client_by_name(username) is not None
    return api_response(is_account)

@api.get("/account/validate-session/{client_id}")
async def get_account_validate_session(client_id: str = None, request: Request = None) -> JSONResponse:
    if not client_id:
        observability.client_logger.warning(f"client tried to validate session with no client_id set by iphash={iphash}")
        return api_response(False)
    
    iphash = accounts.hash_ip(request.client.host)
    account = await accounts.get_client_by_id(client_id)
    
    if account is None:
        observability.client_logger.warning(f"session validation failed for client_id={client_id} by iphash={iphash} (account not found)")
        return api_response(False)
    
    if iphash not in account['logged_ips']:
        observability.client_logger.warning(f"session validation failed for client_id={client_id} by iphash={iphash}")
        return api_response(False)

    observability.client_logger.info(f"successfull session validation for client_id={client_id} by iphash={iphash}")
    return api_response(True, {"username": account['name']})

@api.get("/account/logout/{client_id}")
async def get_account_logout(client_id: str, request: Request) -> JSONResponse:
    iphash = accounts.hash_ip(request.client.host)
    await accounts.logout(client_id, iphash)
    return api_response(True)

        
if __name__ == "__main__":
    FastAPIInstrumentor.instrument_app(api)
    uvicorn.run(api)
