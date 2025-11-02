from supabase import create_client, Client
import postgrest
import random
import uuid
import os

from modules import observability


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def execute_query(query: postgrest.SyncRequestBuilder) -> postgrest.APIResponse:
    try:
        return query.execute()
    except postgrest.APIError as query_error:
        observability.db_logger.error(f"Request error: {query_error} ({query_error._raw_error})")


def __parse_answers(question_data: dict) -> dict:
    """ Turn answer_a, answer_b, ... to: "answers": "TN"/{"A": "...", "B": "..."} """
    if not question_data["answer_a"]: # Tak/Nie
        question_data["answers"] = "TN"
    else: # ABC
        question_data["answers"] = {
            "A": question_data["answer_a"],
            "B": question_data["answer_b"],
            "C": question_data["answer_c"],
        }
        
    del question_data["answer_a"]
    del question_data["answer_b"]
    del question_data["answer_c"]

    return question_data


def fetch_question(index: int) -> dict:
    query = supabase.table("Questions").select("*").eq("index", index)
    response = execute_query(query)
    question_row = response.model_dump()["data"][0]
    return __parse_answers(question_row)


def set_practice_index(client_id: str, index: int) -> None:
    execute_query(
        supabase.table("Clients").update({"practice_index": index}).eq("client_id", client_id)
    )

def mark_as_hard_question(client_data: dict, question_index: int) -> list[int]:
    current_hard = client_data["practice_hard_questions"]
    client_id = client_data["client_id"]
    if question_index in current_hard:
        return current_hard
    
    new_hard_list = current_hard + [question_index]
    execute_query(
        supabase.table("Clients").update({"practice_hard_questions": new_hard_list}).eq("client_id", client_id)
    )
    
    return new_hard_list
    
def unmark_as_hard_question(client_data: dict, question_index: int) -> list[int]:
    current_hard = client_data["practice_hard_questions"]
    client_id = client_data["client_id"]
    if question_index not in current_hard:
        return current_hard
    
    current_hard.remove(question_index)
    execute_query(
        supabase.table("Clients").update({"practice_hard_questions": current_hard}).eq("client_id", client_id)
    )
    
    return current_hard

def create_anonymous_client() -> str:
    client_id = str(uuid.uuid4())
    execute_query(supabase.table("Clients").insert({
        "client_id": client_id,
        "is_anon": True,
        "practice_seed": random.randint(1, 2_147_483_647) # int4 max
    }))

    return client_id


def get_client(client_id: str) -> dict | None:
    clients_data = execute_query(supabase.table("Clients").select("*").eq("client_id", client_id)).model_dump()["data"]
    if not clients_data:
        return
    return clients_data[0]

