from supabase import create_client, Client
import postgrest
import random
import uuid
import os

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
TOTAL_QUESTIONS = 2016


def execute_query(query: postgrest.SyncRequestBuilder) -> postgrest.APIResponse:
    try:
        return query.execute()
    except postgrest.APIError as query_error:
        # logger.error(f"DB query error: \n{query.params} \n{query_error._raw_error}")
        print("db error: " + query_error._raw_error)


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


def fetch_random_question() -> dict:
    q_rand_index = random.randint(1, TOTAL_QUESTIONS)
    
    query = supabase.table("Questions").select("*").eq("index", q_rand_index)
    response = execute_query(query)
    question_row = response.model_dump()["data"][0]
    return __parse_answers(question_row)


def create_anonymous_client() -> str:
    client_id = uuid.uuid4().hex
    supabase.table("Clients").insert({
        "client_id": client_id,
        "is_anon": True,
        "practice_seed": random.randint(1, 2_147_483_647) # int4 max
    })

    return client_id

def get_client(client_id: str) -> dict:
    return supabase.table("Clients").select("*").eq("client_id", client_id)

