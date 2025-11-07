from abc import ABC, abstractmethod
import random
import json
import time
import os

from modules import observability
from modules import database

TOTAL_QUESTIONS = int(os.environ.get("TOTAL_QUESTIONS"))


def get_questions_manager_base(mode: str) -> "QuestionsManagerABC":
    if mode == "exam":
        return ExamManager
    if mode == "practice":
        return PracticeManager
    

class QuestionsManagerABC(ABC):
    client_data: dict
    current_question: dict | None = None
    response_span: observability.trace.Span | None = None 
    question_sent_time: float | None = None
    
    @abstractmethod
    def provide_question(self) -> tuple[str, dict]:
        ...
        
    @abstractmethod
    def handle_answer(self) -> dict | str:
        ...
    

class PracticeManager(QuestionsManagerABC):
    def __init__(self, client_data: dict) -> None:
        self.client_data = client_data
        self.client_id = client_data['client_id']
        self.prepare_questions_line()

    def provide_question(self) -> tuple[str, dict]:
        is_inserting_hard = self.should_insert_hard_question()
        hard_questions = self.client_data["practice_hard_questions"]
        
        if is_inserting_hard:
            question_index = hard_questions[0]
            observability.client_logger.debug(f"Hard question question_index={question_index} inserted to the line for client_id={self.client_id}")
        else:
            question_index = self.questions_line[self.client_data['practice_index']]
            
        question_data = database.fetch_question(question_index)
        question_data['is_hard'] = is_inserting_hard
        
        question_data["number"] = self.client_data['practice_index']
        question_data["_total_hard"] = len(hard_questions)

        self.current_question = question_data.copy()
        self.response_span = observability.tracer.start_span("quiz-practice-response", attributes={"client_id": self.client_id, "question_index": question_index})
        self.question_sent_time = time.time()
        
        observability.client_logger.info(f"Sending censored mode=practice question_index={question_index} question_data='{json.dumps(question_data)}' for client_id={self.client_id}")
        del question_data["correct_answer"]
    
        return ("QUESTION_DATA", question_data)
    
    def handle_answer(self, answer: str):
        question_index = self.current_question['index']

        if not self.current_question['is_hard']:
            self.increment_question_index()
            
        # Observability.
        self.response_span.add_event("Received response", attributes={"answer": answer, "question_index": question_index})
        answering_time = time.time() - self.question_sent_time
        observability.TOTAL_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
        observability.TIME_ANSWERING.labels(question_index=question_index, client_id=self.client_id).observe(answering_time)
        
        # Correct answer.
        if answer == self.current_question['correct_answer']:
            if self.current_question["is_hard"]:
                observability.client_logger.debug(f"Correctly answered question_index={question_index} was marked as HARD by client_id={self.client_id}. Unmarking...")
                self.client_data['practice_hard_questions'] = database.unmark_as_hard_question(self.client_data, question_index)
    
            observability.client_logger.info(f"Correct mode=practice answer={answer} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
            observability.CORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
            self.response_span.end()

            return {
                "is_correct": True,
                "correct_answer": answer,
                "given_answer": answer
            }
            
        # Incorrect answer.
        else:
            if not self.current_question["is_hard"]:
                observability.client_logger.debug(f"Inorrectly answered question_index={question_index} is being marked as HARD by client_id={self.client_id}. Marking...")
                self.client_data['practice_hard_questions'] = database.mark_as_hard_question(self.client_data, question_index)
    
            observability.client_logger.info(f"Incorrect mode=practice answer={answer} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
            observability.INCORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
            self.response_span.end()

            return {
                "is_correct": False,
                "correct_answer": self.current_question['correct_answer'],
                "given_answer": answer
            }
    
    def prepare_questions_line(self) -> list[int]:
        self.questions_line = list(range(1, TOTAL_QUESTIONS))
        random.Random(self.client_data['practice_seed']).shuffle(self.questions_line)  # Thread-safe
        observability.client_logger.debug(f"Shuffled questions for client_id={self.client_id} with seed={self.client_data['practice_seed']}. The questions line starts with: shuffled_line='{self.questions_line[:3]}'")

    def increment_question_index(self) -> None:
        self.client_data['practice_index'] += 1
        database.set_practice_index(self.client_id, self.client_data['practice_index'])
        observability.client_logger.info(f"Incremented practice_index={self.client_data['practice_index']} for client_id={self.client_id}")

    def should_insert_hard_question(self) -> bool:
        hard_questions = self.client_data['practice_hard_questions']
        hard_questions_percentage = len(hard_questions) / TOTAL_QUESTIONS
        observability.client_logger.debug(f"Chance for hard question for client_id={self.client_id} with total_hard_questions={len(hard_questions)} is: hard_question_chance={hard_questions_percentage}")
        return hard_questions and random.random() < hard_questions_percentage


class ExamManager(QuestionsManagerABC):
    def __init__(self, client_data: dict) -> None:
        self.client_data = client_data
        self.client_id = client_data['client_id']
        self.questions_line = database.generate_exam_line()

        self.line_index = 0
        self.points = 0
        self.incorrect = []
        self.start_time = time.time()
        
    def provide_question(self) -> tuple[str, dict]:
        if self.line_index > len(self.questions_line) - 1:
            if self.points >= 68:
                observability.EXAM_PASSED.labels(client_id=self.client_id).inc()
            else:
                observability.EXAM_FAILED.labels(client_id=self.client_id).inc()
                
            total_time_s = time.time() - self.start_time  
            observability.EXAM_TOTAL_TIME.labels(client_id=self.client_id).observe(total_time_s)

            observability.EXAM_POINTS.labels(client_id=self.client_id).observe(self.points)
            
            return (
                "EXAM_FINISH",
                self.prepare_exam_result()  
            )
            
        question_data = self.questions_line[self.line_index]

        self.current_question = question_data.copy()
        self.response_span = observability.tracer.start_span("quiz-exam-response", attributes={"client_id": self.client_id, "question_index": question_data['index']})
        self.question_sent_time = time.time()
        
        observability.client_logger.info(f"Sending censored mode=exam question_index={question_data['index']} question_data='{json.dumps(question_data)}' for client_id={self.client_id}")
        del question_data["correct_answer"]
        question_data['number'] = self.line_index + 1
        self.line_index += 1

        return ("QUESTION_DATA", question_data)
    
    def handle_answer(self, answer: str) -> str:
        question_index = self.current_question['index']
        
        # Observability.
        self.response_span.add_event("Received response", attributes={"answer": answer, "question_index": question_index})
        answering_time = time.time() - self.question_sent_time
        observability.TOTAL_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
        observability.TIME_ANSWERING.labels(question_index=question_index, client_id=self.client_id).observe(answering_time)
        
        # Correct answer.
        if answer == self.current_question['correct_answer']:
            observability.client_logger.info(f"Correct mode=exam answer={answer} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
            observability.CORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
            self.response_span.end()
            
            self.points += self.current_question['points']
            
        # Incorrect answer.
        else:
            observability.client_logger.info(f"Incorrect mode=exam answer={answer} for question_index={question_index} by client_id={self.client_id} answering took time={answering_time} seconds")
            observability.INCORRECT_ANSWERS.labels(question_index=question_index, client_id=self.client_id).inc()
            self.response_span.end()
            
            question_data_dump = self.current_question.copy()
            question_data_dump['client_answer'] = answer
            
            self.incorrect.append(question_data_dump)

        return "OK"
        
    def prepare_exam_result(self) -> dict:
        is_passed = self.points >= 68

        return {
            "result": is_passed,
            "points": self.points,
            "incorrect": self.incorrect
        }