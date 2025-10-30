from fastapi import WebSocket, WebSocketDisconnect

from modules import database


class WSQuizSessionHandler:
    def __init__(self, ws_client: WebSocket) -> None:
        self.ws_client = ws_client
            
    async def receive(self) -> None:
        while True:
            try:
                message = await self.ws_client.receive_json()
                print("Received:", message)
                await self.handle_message(message)
            except (RuntimeError, WebSocketDisconnect) as error:
                return
        
    def ws_response(self, event: str, data: dict | None) -> dict:
        return {
            "event": event,
            "content": data
        }        

    async def handle_message(self, data: dict) -> None:
        event = data["event"]
        content = data["content"]
        
        match event:
            case "GET_QUESTION":
                question_data = database.fetch_random_question()
                return await self.ws_client.send_json(self.ws_response("QUESTION_DATA", question_data))
        
        