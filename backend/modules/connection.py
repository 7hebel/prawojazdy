from fastapi import WebSocket, WebSocketDisconnect
import random
import os

from modules import database


class WSQuizSessionHandler:
    def __init__(self, client_id: str | None, ws_client: WebSocket) -> None:
        self.ws_client = ws_client
        self.client_id = client_id
        
    async def initialize(self) -> None:
        if self.client_id == "anon":
            self.client_id = database.create_anonymous_client()
            await self.ws_client.send_json(self.ws_response("SET_CLIENT_ID", self.client_id))
        
        self.client_data = database.get_client(self.client_id)
        self.questions_line = list(range(1, int(os.environ.get("TOTAL_QUESTIONS"))))
        
        random.seed(self.client_data['practice_seed'])
        random.shuffle(self.questions_line)
        
        self.__current_question: dict | None = None
        
        await self.receive()
            
    async def receive(self) -> None:
        while True:
            try:
                message = await self.ws_client.receive_json()
                await self.handle_message(message)
            except (RuntimeError, WebSocketDisconnect) as error:
                return
        
    def ws_response(self, event: str, data: dict | str | None) -> dict:
        return {
            "event": event,
            "content": data
        }        

    def increment_question_index(self) -> None:
        self.client_data['practice_index'] += 1
        database.set_practice_index(self.client_id, self.client_data['practice_index'])

    async def handle_message(self, data: dict) -> None:
        event = data["event"]
        content = data["content"]
        
        match event:
            case "GET_QUESTION":
                question_index = self.questions_line[self.client_data['practice_index']]
                question_data = database.fetch_question(question_index)
                self.__current_question = question_data    

                return await self.ws_client.send_json(self.ws_response("QUESTION_DATA", question_data))
        
            case "CHECK_ANSWER":
                self.increment_question_index()
                
                if self.__current_question['correct_answer'] == content:
                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": True,
                        "correct_answer": content,
                        "given_answer": content
                    }))
                else:
                    #TODO: add to practice_wrong answers
                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": False,
                        "correct_answer": self.__current_question['correct_answer'],
                        "given_answer": content
                    }))
                    
