from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
import uvicorn
import dotenv

dotenv.load_dotenv(".env")

from modules import observability
from modules import connection
from modules import database


api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/media/{media_name}")
async def static_media(media_name: str) -> Response:
    with open("../media/" + media_name, "rb") as file:
        return Response(file.read(), media_type="video/mp4")

@api.get("/")
async def get_home() -> Response:
    return Response("200")

@api.websocket("/ws/practice")
async def ws_practice(ws_client: WebSocket) -> None:
    await ws_client.accept()
    await connection.WSQuizSessionHandler(ws_client).receive()
        
        
if __name__ == "__main__":
    uvicorn.run(api)


