from pydantic import BaseModel
from hashlib import sha1
import bcrypt
import random
import uuid

from modules import observability
from modules import database


class AccountRegisterModel(BaseModel):
    client_id: str
    username: str
    password: str

class AccountLoginModel(BaseModel):
    username: str
    password: str


def hash_ip(raw_ip: str) -> str:
    return sha1(raw_ip.encode()).hexdigest()

def create_anonymous_client() -> str:
    client_id = str(uuid.uuid4())
    database.execute_query(database.supabase.table("Clients").insert({
        "client_id": client_id,
        "is_anon": True,
        "practice_seed": random.randint(1, 2_147_483_647) # int4 max
    }))

    return client_id

def get_client_by_id(client_id: str) -> dict | None:
    clients_data = database.execute_query(database.supabase.table("Clients").select("*").eq("client_id", client_id)).model_dump()["data"]
    if not clients_data:
        return
    return clients_data[0]

def get_client_by_name(username: str) -> dict | None:
    return database.execute_query(database.supabase.table("Clients").select("*").eq("name", username).single()).model_dump()["data"]

def register_account(client_id: str, username: str, password: str, iphash: str) -> bool:
    anon_client_entry = get_client_by_id(client_id)
    if anon_client_entry is None:
        observability.client_logger.error(f"failed to register account client_id={client_id} (not found)")
        return False
    
    if not anon_client_entry["is_anon"]:
        observability.client_logger.error(f"failed to register account client_id={client_id} (account not anon?)")
        return False
    
    encrypted_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    database.execute_query(
        database.supabase.table("Clients").update({
            "is_anon": False,
            "name": username,
            "password": encrypted_password,
            "logged_ips": [iphash]
        }).eq("client_id", client_id)
    )
    
    observability.client_logger.info(f"successfully registered account client_id={client_id} with username={username} from iphash={iphash}")
    return True

def login_account(username: str, password: str, iphash: str) -> bool:
    account = get_client_by_name(username)
    if account is None:
        observability.client_logger.error(f"failed to login into account username={username} (not found)")
        return False
    
    if not bcrypt.checkpw(password.encode(), account['password']):
        observability.client_logger.error(f"failed to login into account username={username} (invalid password)")
        return False

    if iphash not in account['logged_ips']:
        database.execute_query(
            database.supabase.table("Clients").update({
                "logged_ips": account['logged_ips'] + [iphash]
            }).eq("client_id", account['client_id'])
        )
        observability.client_logger.info(f"added iphash={iphash} to logged_ips of client_id={account['client_id']}")
        
    observability.client_logger.info(f"successfully logged in into account client_id={account['client_id']} from iphash={iphash}")
    return True

def logout(client_id: str, iphash: str) -> None:
    account = get_client_by_id(client_id)
    if account is None:
        return observability.client_logger.error(f"failed to logout iphash={iphash} from account client_id={client_id} (not found)")
        
    if iphash not in account['logged_ips']:
        return observability.client_logger.error(f"failed to logout iphash={iphash} from account client_id={client_id} (iphash not logged?)")
        
    account['logged_ips'].remove(iphash)
    database.execute_query(
        database.supabase.table("Clients").update({
            "logged_ips": account['logged_ips']
        }).eq("client_id", account['client_id'])
    )
    
    observability.client_logger.info(f"logged out iphash={iphash} from account client_id={client_id}")