from supabase import acreate_client, AsyncClient, create_client, Client
import postgrest
import asyncio
import os

from modules import observability


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: AsyncClient | None = None
_sync_supabase: Client = create_client(url, key)

async def get_supabase():  
    global supabase
    if supabase is None:
        supabase = await acreate_client(url, key)  
    return supabase

asyncio.get_event_loop().run_until_complete(get_supabase())


async def execute_query(query: postgrest.AsyncRequestBuilder) -> postgrest.APIResponse:
    try:
        return await query.execute()
    except postgrest.APIError as query_error:
        observability.db_logger.error(f"Request error: {query_error} ({query_error._raw_error})")
    except Exception as error:
        observability.db_logger.error(f"Unkown db query error: {error}")


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


async def fetch_question(index: int) -> dict:
    query = supabase.table("Questions").select("*").eq("index", index)
    response = await execute_query(query)
    question_row = response.model_dump()["data"][0]
    return __parse_answers(question_row)


async def set_practice_index(client_id: str, index: int) -> None:
    await execute_query(
        supabase.table("Clients").update({"practice_index": index}).eq("client_id", client_id)
    )

async def mark_as_hard_question(client_data: dict, question_index: int) -> list[int]:
    current_hard = client_data["practice_hard_questions"]
    client_id = client_data["client_id"]
    if question_index in current_hard:
        return current_hard
    
    new_hard_list = current_hard + [question_index]
    await execute_query(
        supabase.table("Clients").update({"practice_hard_questions": new_hard_list}).eq("client_id", client_id)
    )
    
    return new_hard_list
    
async def unmark_as_hard_question(client_data: dict, question_index: int) -> list[int]:
    current_hard = client_data["practice_hard_questions"]
    client_id = client_data["client_id"]
    if question_index not in current_hard:
        return current_hard
    
    current_hard.remove(question_index)
    await execute_query(
        supabase.table("Clients").update({"practice_hard_questions": current_hard}).eq("client_id", client_id)
    )
    
    return current_hard

async def generate_exam_line() -> list[dict]:
    """  
    20 questions from "PODSTAWOWY" set:
        - 10x 3p.
        - 6x 2p.
        - 4x 1p.
        
    12 questions from "SPECJALISTYCZNY" set:
        - 6x 3p.
        - 4x 2p.
        - 2x 1p.
    """
    
    queries = [
        supabase.table("exam_podstawowy_3p").select("*").limit(10),
        supabase.table("exam_podstawowy_2p").select("*").limit(6),
        supabase.table("exam_podstawowy_1p").select("*").limit(4),
        
        supabase.table("exam_specjalistyczny_3p").select("*").limit(6),
        supabase.table("exam_specjalistyczny_2p").select("*").limit(4),
        supabase.table("exam_specjalistyczny_1p").select("*").limit(2),
    ]
    
    questions_line = []

    for query in queries:
        query = await execute_query(query)
        results = query.model_dump()["data"]
        for result in results:
            questions_line.append(__parse_answers(result))        
        
    
    return questions_line

