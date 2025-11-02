from fastapi import WebSocket, WebSocketDisconnect
import random
import time
import json
import os

from modules import observability
from modules import database


TOTAL_QUESTIONS = int(os.environ.get("TOTAL_QUESTIONS"))


class WSQuizSessionHandler:
    def __init__(self, client_id: str | None, ws_client: WebSocket) -> None:
        self.ws_client = ws_client
        self.client_id = client_id
        
    async def initialize(self) -> None:
        self.questions_line = list(range(1, TOTAL_QUESTIONS))
        
        if self.client_id != "anon":
            client_data = database.get_client(self.client_id)
            if client_data is None:
                observability.client_logger.warning(f"Client started WS/practice connection with client_id={self.client_id} but no user with this ID found.")
                self.client_id = "anon"
            else:
                self.client_data = client_data
        
        if self.client_id == "anon":
            self.client_id = database.create_anonymous_client()
            
            observability.client_logger.info(f"Created anonymous account for client_host={self.ws_client.client.host} with client_id={self.client_id}")
            observability.api_logger.info(f"Associated client_host={self.ws_client.client.host} connection with generated client_id={self.client_id}. Informing client...")

            await self.ws_client.send_json(self.ws_response("SET_CLIENT_ID", self.client_id))
        
            self.client_data = database.get_client(self.client_id)

        random.Random(self.client_data['practice_seed']).shuffle(self.questions_line)  # Thread-safe
        observability.client_logger.debug(f"Shuffled questions for client_id={self.client_id} with seed={self.client_data['practice_seed']}. The questions line starts with: shuffled_line='{self.questions_line[:3]}'")
        
        self.__current_question: dict | None = None
        self.__response_span = None
        self.__question_sent_time: float | None = None
        
        await self.receive()
            
    async def receive(self) -> None:
        while True:
            try:
                message = await self.ws_client.receive_json()
                observability.client_logger.debug(f"Received WS message from client_id={self.client_id} msg_content='{message}'")
                with observability.tracer.start_as_current_span("ws-practice-handle-message", attributes={"client_id": self.client_id, "event": message.get("event", "EVENTLESS?")}):
                    await self.handle_message(message)
            except (RuntimeError, WebSocketDisconnect) as error:
                observability.api_logger.error(f"WS/practice connection error: {error} with: client_id={self.client_id} from host={self.ws_client.client.host}")
                return
        
    def ws_response(self, event: str, data: dict | str | None) -> dict:
        return {
            "event": event,
            "content": data
        }        

    def increment_question_index(self) -> None:
        self.client_data['practice_index'] += 1
        database.set_practice_index(self.client_id, self.client_data['practice_index'])
        observability.client_logger.info(f"Incremented practice_index={self.client_data['practice_index']} for client_id={self.client_id}")

    async def handle_message(self, data: dict) -> None:
        event = data["event"]
        content = data["content"]
        
        match event:
            case "GET_QUESTION":
                hard_questions = self.client_data['practice_hard_questions']
                hard_questions_percentage = len(hard_questions) / TOTAL_QUESTIONS
                observability.client_logger.debug(f"Chance for hard question for client_id={self.client_id} with total_hard_questions={len(hard_questions)} is: hard_question_chance={hard_questions_percentage}")
                
                if hard_questions and random.random() < hard_questions_percentage:
                    hard_question_index = hard_questions[0]
                    question_data = database.fetch_question(hard_question_index)
                    question_data["is_hard"] = True
                    observability.client_logger.debug(f"Hard question question_index={hard_question_index} chosen for client_id={self.client_id} with hard_question_chance={hard_questions_percentage}")

                else:
                    question_index = self.questions_line[self.client_data['practice_index']]
                    question_data = database.fetch_question(question_index)
                    question_data["is_hard"] = False
                
                question_data["number"] = self.client_data['practice_index']
                question_data["_total_hard"] = len(hard_questions)
                self.__current_question = question_data.copy()
                
                observability.client_logger.info(f"Sending censored question_data='{json.dumps(question_data)}' for client_id={self.client_id}")
                del question_data["correct_answer"]

                self.__response_span = observability.tracer.start_span("quiz-practice-response", attributes={"client_id": self.client_id, "question_index": question_index})
                self.__question_sent_time = time.time()
                return await self.ws_client.send_json(self.ws_response("QUESTION_DATA", question_data))
        
            case "CHECK_ANSWER":
                if not self.__current_question["is_hard"]:
                    self.increment_question_index()
                
                question_index = self.__current_question['index']
                
                self.__response_span.add_event("Received response", attributes={"answer": content, "question_index": question_index})
                answering_time = time.time() - self.__question_sent_time
                
                observability.TOTAL_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
                observability.TIME_ANSWERING.labels(question_index=question_index, client_id=self.client_id).observe(answering_time)
                
                if self.__current_question['correct_answer'] == content:
                    observability.client_logger.info(f"Correct answer={content} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
                    if self.__current_question["is_hard"]:
                        observability.client_logger.debug(f"Correctly answered question_index={question_index} was marked as HARD by client_id={self.client_id}. Unmarking...")
                        self.client_data['practice_hard_questions'] = database.unmark_as_hard_question(self.client_data, question_index)

                    observability.CORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
                    self.__response_span.end()
                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": True,
                        "correct_answer": content,
                        "given_answer": content
                    }))
                    
                else:
                    observability.client_logger.info(f"Incorrect answer={content} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
                    if not self.__current_question["is_hard"]:
                        observability.client_logger.debug(f"Inorrectly answered question_index={question_index} is being marked as HARD by client_id={self.client_id}. Marking...")
                        self.client_data['practice_hard_questions'] = database.mark_as_hard_question(self.client_data, question_index)

                    observability.INCORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
                    self.__response_span.end()
                    return await self.ws_client.send_json(self.ws_response("ANSWER_VALIDATION", {
                        "is_correct": False,
                        "correct_answer": self.__current_question['correct_answer'],
                        "given_answer": content
                    }))
                    
