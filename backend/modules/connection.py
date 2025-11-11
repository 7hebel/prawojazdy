from datetime import datetime, timezone, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from threading import Thread
from enum import StrEnum
import asyncio
import time

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
        await self.ws_client.accept()
        
        if self.client_id != "anon":
            client_data = await accounts.get_client_by_id(self.client_id)
            if client_data:
                self.client_data = client_data
            else:
                observability.client_logger.warning(f"Client started WS/{self.mode} connection with client_id={self.client_id} but no user with this ID found.")
                self.client_id = "anon"
        
        if self.client_id == "anon":
            self.client_id = await accounts.create_anonymous_client()
            
            observability.client_logger.info(f"Created anonymous account for client_host={self.ws_client.client.host} with client_id={self.client_id}")
            observability.api_logger.info(f"Associated client_host={self.ws_client.client.host} connection with generated client_id={self.client_id}. Informing client...")
    
            await self.ws_client.send_json(ws_response(EventHeader.SET_CLIENT_ID, self.client_id))
            self.client_data = await accounts.get_client_by_id(self.client_id)
    
        self.manager = self.__manager_base(self.client_data)
        await self.manager.initialize()
    
        if self.client_id in open_handlers:
            await open_handlers[self.client_id].abort()
            
        open_handlers[self.client_id] = self
    
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
                event_header, question_data = await self.manager.provide_question()
                return await self.ws_client.send_json(ws_response(event_header, question_data))

            case EventHeader.CHECK_ANSWER:
                validation_response = await self.manager.handle_answer(content)
                return await self.ws_client.send_json(ws_response(EventHeader.ANSWER_VALIDATION, validation_response))

    async def abort(self) -> None:
        observability.api_logger.warning(f"Abort action was called on WS/{self.mode} connection with client_id={self.client_id} from host={self.ws_client.client.host} Most likely another Handler was created for this client...")
        try:
            await self.ws_client.close()
        except:
            pass
            

def orphan_connection_handlers_cleaner() -> None:
    while True:
        orphan_count = 0
        now = datetime.now(timezone.utc)
        
        for client_id, handler in open_handlers.copy().items():
            if handler.ws_client.client_state != WebSocketState.DISCONNECTED:
                continue
            
            account = database._sync_supabase.table("Clients").select("*").eq("client_id", client_id).single().execute().model_dump()["data"]
            if account is None:
                return
            
            created_at = datetime.fromisoformat(account['created_at'])
            if account['practice_index'] < 5 and (now - created_at > timedelta(minutes=5)):
                observability.client_logger.warning(f"found orphan connection with only {account['practice_index']}<5 questions answered client_id={client_id} deleteing account...")
                accounts.remove_account(client_id)
                
                del handler
                del open_handlers[client_id]
                
                orphan_count += 1
                
        if orphan_count > 0:
            observability.client_logger.warning(f"Removed orphan_count={orphan_count} orphan connection handlers and their accounts")
        else:
            observability.client_logger.debug("No orphan connection handlers found.")
            
        time.sleep(30)

def forgotten_anon_accounts_cleaner() -> None:
    while True:
        forgotten_count = 0
        now = datetime.now(timezone.utc)
        
        for anon_client in accounts.get_all_anon_and_test_clients():
            client_id = anon_client['client_id']

            if client_id in open_handlers or client_id is None:  
                # Has (possibly) open WS connection. If connection is orphaned, orphan cleaner will close it
                # and the forgotten account will be removed in the next check.
                continue

            created_at = datetime.fromisoformat(anon_client['created_at'])
            if now - created_at < timedelta(minutes=5):
                continue
            
            if anon_client['practice_index'] < 5:
                observability.client_logger.warning(f"found forgotten account client_id={client_id} created_at={anon_client['created_at']} >5minutes, removing...")
                accounts.remove_account(client_id)
                forgotten_count += 1 

        if forgotten_count > 0:
            observability.client_logger.warning(f"Removed forgotten_count={forgotten_count} forgotten accounts")
        else:
            observability.client_logger.debug("No forgotten accounts found.")

        time.sleep(60)


# Thread(target=orphan_connection_handlers_cleaner, daemon=True).start()
# Thread(target=forgotten_anon_accounts_cleaner, daemon=True).start()
