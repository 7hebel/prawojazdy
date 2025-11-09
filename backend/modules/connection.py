from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from enum import StrEnum

from modules import observability
from modules import questions
from modules import accounts
from modules import database


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

open_handlers: dict[str, "WebSocketHandler"] = {} 


class WebSocketHandler:
    def __init__(self, client_id: str | None, ws_client: WebSocket, mode: str, manager_base: questions.QuestionsManagerABC) -> None:
        self.ws_client = ws_client
        self.client_id = client_id
        self.mode = mode
        self.manager: questions.QuestionsManagerABC | None = None
        self.__manager_base = manager_base

    async def initialize(self):
        if self.client_id != "anon":
            client_data = accounts.get_client_by_id(self.client_id)
            if client_data:
                self.client_data = client_data
            else:
                observability.client_logger.warning(f"Client started WS/{self.mode} connection with client_id={self.client_id} but no user with this ID found.")
                self.client_id = "anon"
        
        if self.client_id == "anon":
            self.client_id = accounts.create_anonymous_client()
            
            observability.client_logger.info(f"Created anonymous account for client_host={self.ws_client.client.host} with client_id={self.client_id}")
            observability.api_logger.info(f"Associated client_host={self.ws_client.client.host} connection with generated client_id={self.client_id}. Informing client...")
    
            await self.ws_client.send_json(ws_response(EventHeader.SET_CLIENT_ID, self.client_id))
            self.client_data = accounts.get_client_by_id(self.client_id)
    
        self.manager = self.__manager_base(self.client_data)
    
        if self.client_id in open_handlers:
            await open_handlers[self.client_id].abort()
            
        open_handlers[self.client_id] = self
    
        await self.ws_client.accept()
        await self.receive()

    async def receive(self) -> None:
        while True:
            try:
                message = await self.ws_client.receive_json()
                observability.client_logger.debug(f"Received WS message from client_id={self.client_id} msg_content='{message}'")
                with observability.tracer.start_as_current_span(f"ws-{self.mode}-handle-message", attributes={"client_id": self.client_id, "event": message.get("event", "EVENTLESS?")}):
                    await self.handle_message(message)
            except (RuntimeError, WebSocketDisconnect):
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

    async def abort(self) -> None:
        observability.api_logger.warning(f"Abort action was called on WS/{self.mode} connection with client_id={self.client_id} from host={self.ws_client.client.host} Most likely another Handler was created for this client...")
        if self.ws_client.client_state != WebSocketState.DISCONNECTED:
            await self.ws_client.close()