from fastapi import WebSocket, WebSocketDisconnect
from enum import StrEnum
import time
import json

from modules import observability
from modules import database
from modules import questions


class EventHeader(StrEnum):
    GET_QUESTION = "GET_QUESTION"
    QUESTION_DATA = "QUESTION_DATA"
    CHECK_ANSWER = "CHECK_ANSWER"
    ANSWER_VALIDATION = "ANSWER_VALIDATION"
    SET_CLIENT_ID = "SET_CLIENT_ID"
    EXAM_FINISH = "EXAM_FINISH"


def ws_response(event: EventHeader, data: dict | str | None) -> dict:
    return {
        "event": event,
        "content": data
    }


class WebSocketHandler:
    def __init__(self, client_id: str | None, ws_client: WebSocket, mode: str, manager_base: questions.QuestionsManagerABC) -> None:
        self.ws_client = ws_client
        self.client_id = client_id
        self.mode = mode
        self.manager: questions.QuestionsManagerABC | None = None
        self.__manager_base = manager_base

    async def initialize(self):
        if self.client_id != "anon":
            client_data = database.get_client(self.client_id)
            if client_data:
                self.client_data = client_data
            else:
                observability.client_logger.warning(f"Client started WS/{self.mode} connection with client_id={self.client_id} but no user with this ID found.")
                self.client_id = "anon"
        
        if self.client_id == "anon":
            self.client_id = database.create_anonymous_client()
            
            observability.client_logger.info(f"Created anonymous account for client_host={self.ws_client.client.host} with client_id={self.client_id}")
            observability.api_logger.info(f"Associated client_host={self.ws_client.client.host} connection with generated client_id={self.client_id}. Informing client...")
    
            await self.ws_client.send_json(ws_response(EventHeader.SET_CLIENT_ID, self.client_id))
            self.client_data = database.get_client(self.client_id)
    
        self.manager = self.__manager_base(self.client_data)
    
        await self.ws_client.accept()
        await self.receive()

    async def receive(self) -> None:
        while True:
            try:
                message = await self.ws_client.receive_json()
                observability.client_logger.debug(f"Received WS message from client_id={self.client_id} msg_content='{message}'")
                with observability.tracer.start_as_current_span(f"ws-{self.mode}-handle-message", attributes={"client_id": self.client_id, "event": message.get("event", "EVENTLESS?")}):
                    await self.handle_message(message)

            except (RuntimeError, WebSocketDisconnect) as error:
                observability.api_logger.error(f"WS/{self.mode} connection error: {error} with: client_id={self.client_id} from host={self.ws_client.client.host}")
                return
            
    async def handle_message(self, data: dict) -> None:
        event = data["event"]
        content = data["content"]
        
        match event:
            case EventHeader.GET_QUESTION:
                event_header, question_data = self.manager.provide_question()
                return await self.ws_client.send_json(ws_response(event_header, question_data))

            case EventHeader.CHECK_ANSWER:
                validation_response = self.manager.handle_answer(content)
                return await self.ws_client.send_json(ws_response(EventHeader.ANSWER_VALIDATION, validation_response))
