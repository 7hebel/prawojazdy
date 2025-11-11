from modules import observability

import requests
import os


def test_env_vars() -> bool:
    required_env_vars = (
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "TOTAL_QUESTIONS",
        "LGTM_LOKI_API",
        "LGTM_OTEL_API",
    )
    
    for required_env_var in required_env_vars:
        if required_env_var not in os.environ:
            observability.test_logger.critical(f"Missing required env_var={required_env_var}")
            return False
        
    return True

def test_lgtm_stack() -> bool:
    endpoints = {
        "Loki": "http://localhost:3100/ready",
        "Grafana": "http://localhost:3000/api/health",
        "Prometheus": "http://localhost:9090/"
    }

    for name, url in endpoints.items():
        try:
            r = requests.get(url, timeout=2)
            if r.status_code != 200:
                observability.test_logger.critical(f"LGTM service={name} at url={url} did not respond correctly with status_code={r.status_code}")
                return False
                
        except Exception as e:
            observability.test_logger.critical(f"LGTM service={name} at url={url} failed to respond. {e}")
            return False
        
    return True
        
def test_is_api_and_app_up() -> bool:
    endpoints = {
        "API": "http://localhost:8000/",
        "app": "http://localhost:5173/",
    }

    for name, url in endpoints.items():
        try:
            r = requests.get(url, timeout=2)
            if r.status_code != 200:
                observability.test_logger.critical(f"Local service={name} at url={url} did not respond correctly with satus_code={r.status_code}")
                return False
                
        except Exception as e:
            observability.test_logger.critical(f"Local service={name} at url={url} failed to respond. {e}")
            return False
        
    return True
   