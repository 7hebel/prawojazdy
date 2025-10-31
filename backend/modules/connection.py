from fastapi import WebSocket, WebSocketDisconnect
import random
import os

from modules import database


TOTAL_QUESTIONS = int(os.environ.get("TOTAL_QUESTIONS"))


class WSQuizSessionHandler:
    def __init__(self, client_id: str | None, ws_client: WebSocket) -> None:
        self.ws_client = ws_client
        self.client_id = client_id
        
    async def initialize(self) -> None:
        if self.client_id == "anon":
            self.client_id = database.create_anonymous_client()
            await self.ws_client.send_json(self.ws_response("SET_CLIENT_ID", self.client_id))
        
        self.client_data = database.get_client(self.client_id)
        self.questions_line = list(range(1, TOTAL_QUESTIONS))
        
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
                hard_questions = self.client_data['practice_hard_questions']
                hard_questions_percentage = len(hard_questions) / TOTAL_QUESTIONS
                if hard_questions and random.random() < hard_questions_percentage:
                    hard_question_index = hard_questions[0]
                    question_data = database.fetch_question(hard_question_index)
                    question_data["is_hard"] = True

                else:
                    question_index = self.questions_line[self.client_data['practice_index']]
                    question_data = database.fetch_question(question_index)
                    question_data["is_hard"] = False
                
                question_data["number"] = self.client_data['practice_index']
                question_data["_total_hard"] = len(hard_questions)
                self.__current_question = question_data.copy()
                del question_data["correct_answer"]

                return await self.ws_client.send_json(self.ws_response("QUESTION_DATA", question_data))
        
            case "CHECK_ANSWER":
                if not self.__current_question["is_hard"]:
                    self.increment_question_index()
                
                if self.__current_question['correct_answer'] == content:
                    if self.__current_question["is_hard"]:
                        self.client_data['practice_hard_questions'] = database.unmark_as_hard_question(self.client_data, self.__current_question['index'])

                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": True,
                        "correct_answer": content,
                        "given_answer": content
                    }))
                    
                else:
                    if not self.__current_question["is_hard"]:
                        self.client_data['practice_hard_questions'] = database.mark_as_hard_question(self.client_data, self.__current_question['index'])
                        
                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": False,
                        "correct_answer": self.__current_question['correct_answer'],
                        "given_answer": content
                    }))
                    
