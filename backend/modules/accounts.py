from hashlib import sha1

from modules import observability
from modules import database


def hash_ip(raw_ip: str) -> str:
    return sha1(raw_ip.encode()).hexdigest()


def register_account(client_id: str, username: str, password: str, iphash: str) -> bool:
    anon_client_entry = database.get_client(client_id)
    if anon_client_entry is None:
        observability.client_logger.error(f"failed to register account client_id={client_id} (not found)")
        return False
    
    if not anon_client_entry["is_anon"]:
        observability.client_logger.error(f"failed to register account client_id={client_id} (account not anon?)")
        return False
    
    pass

