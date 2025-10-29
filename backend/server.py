from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import dotenv
import os

dotenv.load_dotenv(".env")

from modules import observability
from modules import database


api = FastAPI()
api.mount('/media/', StaticFiles(directory="../media/"), name="media")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/")
async def home() -> Response:
    return Response("200")

@api.get("/q/random")
async def question_random() -> JSONResponse:
    return database.fetch_random_question()

if __name__ == "__main__":
    uvicorn.run(api)


