from playwright.sync_api import sync_playwright
import requests
import sys
import os

import dotenv
dotenv.load_dotenv(".env")

from modules import observability

try:
    from modules import database
    from modules import accounts
except Exception as e:
    observability.test_logger.critical(f"Failed to establish connection with database: {e}")
    exit()


def test_env_vars() -> bool:
    required_env_vars = (
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "TOTAL_QUESTIONS",
        "LGTM_LOKI_API",
        "LGTM_OTEL_API",
        "TEST_CLIENT_ID"
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
   
def test_custom_test_client() -> bool:
    test_client_id = os.getenv("TEST_CLIENT_ID")
    
    try:
        client_data = accounts.get_client_by_id(test_client_id)
    except Exception as e:
        observability.test_logger.critical(f"Failed to fetch test-client-id={test_client_id} data from database. {e}")
        return False
    
    if client_data["name"] != "TestClient":
        observability.test_logger.warning(f"Invalid test client's name={client_data['name']}. Expected name: 'TestClient'. Test won't be continued as there is a chance that it is a real client. test-client-id={test_client_id}")
        return False
    
    if client_data["practice_seed"] != 3:
        observability.test_logger.warning(f"Invalid practice_seed={client_data['practice_seed']} set expected=3. Setting correct...")
        database.execute_query(
            database.supabase.table("Clients").update({"practice_seed": 3}).eq("client_id", test_client_id)
        )
        
    database.execute_query(
        database.supabase.table("Clients").update({"practice_index": 0, "practice_hard_questions": []}).eq("client_id", test_client_id)
    )
    observability.test_logger.info(f"Set test client's practice_index to default (0)...")

    client_data = accounts.get_client_by_id(test_client_id)
    if client_data["practice_index"] != 0:
        observability.test_logger.critical(f"Validating recent practice_index = 0 change failed. Found practice_index={client_data['practice_index']}")
        return False
    
    return True  

def test_ui() -> bool:
    TEST_CLIENT_ID = os.getenv('TEST_CLIENT_ID')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script(f"localStorage.setItem('CLIENT_ID', '{TEST_CLIENT_ID}');")
        page.goto("http://localhost:5173/quiz", wait_until="domcontentloaded")

        # Verify saved CLIENT_ID from localStorage
        saved_client_id = page.evaluate("localStorage.getItem('CLIENT_ID')")
        if saved_client_id != TEST_CLIENT_ID:
            observability.test_logger.critical(f"Playwright: page opened, client_id set in localstorage but the values dont match! written={TEST_CLIENT_ID} saved={saved_client_id}")
            return False

        # Verify properly connected WebSocket connection
        with page.expect_websocket(timeout=10000) as ws:
            if ws.value.is_closed():
                observability.test_logger.critical("Playwright: page opened, but no WS connection is established (closed).")
                return False
            
        # Check if base HTML structure is loaded.
        main_view_locator = page.wait_for_selector("main#quiz-view", timeout=3000)
        if main_view_locator is None:
            observability.test_logger.critical("Playwright: the <main id='quiz-view'> element has not been loaded after 3 seconds since WS connection established...")
            return False

        # The correct configuration should make server send questions in the following order: 357, 239, 23, 644
        # This order is based on the 'practice_seed' column in DB for client entry with TEST_CLIENT_ID. In this case it should be: 3 
        # The 'practice_seed' value is ensured in the `test_custom_test_client()` test step, also the 'practice_index' is set there to 0 (so it points 357 - the first question).
        # If the questions come from the server in a different order, it might be casued by the different amount of total questions (not 2017). This value is set in .env file.
        # The seed-based pseudo-random generator has been implemented to be thread-safe so there is no chance that a different thread interferes with our shuffling...
        FIRST_QUESTION_INDEX = "357"
        SECOND_QUESTION_INDEX = "239"
        THRID_QUESTION_INDEX = "23"
        FOURTH_QUESTION_INDEX = "644"

        # Check if correct question has been loaded.
        loaded_question_index = main_view_locator.get_attribute("question_index")
        if loaded_question_index != FIRST_QUESTION_INDEX:
            observability.test_logger.critical(f"Playwright: client received incorrect question! Expected question: {FIRST_QUESTION_INDEX}, got: {loaded_question_index}. This may happen when: incorrect practice_seed is set (not '3') or the total amount of questions has changed")
            return False
        
        # Check if pressing 'NEXT' button without selecting a answer plays a error-animation (eq. does not continue...).
        continue_btn = page.locator("#continue-btn")
        continue_btn.click()

        page.wait_for_timeout(100)
        if "error-animation" not in continue_btn.get_attribute("class").split():
            observability.test_logger.critical(f"Playwright: clicked `next` button without selecting a answer but the button did not contain a `error-animation` class after 100ms...")
            return False

        
        def _select_answer_and_check_next_question(answer_value: str, is_long_wait: bool, next_question_index: str | None) -> bool:
            # Select and confirm answer.
            page.click(f"#possible-answer-{answer_value}", timeout=0)
            continue_btn.click()
            
            # Wait for next question to load. If answering incorrect answer, there is additional 3 seconds wait time...
            page.wait_for_timeout(3000 if not is_long_wait else (3000 + 3000))
            
            # Check if the next question index matches desired one.
            if next_question_index is not None:
                current_question_index = page.locator("main#quiz-view").get_attribute("question_index")
                if current_question_index != next_question_index:
                    observability.test_logger.critical(f"Playwright: The displayed question has not changed from {current_question_index} to desired {next_question_index}")
                    return False
                
                # Check if question and all answers are visible on site.
                question_data = database.fetch_question(int(next_question_index))
                if not page.get_by_text(question_data["question"]).is_visible():
                    observability.test_logger.critical(f"Playwright: Question content is not visible on the site after loading next question: {next_question_index}")
                    return False
                
                answers_content = []
                if question_data["correct_answer"] in "TN":
                    answers_content.append("Tak")
                    answers_content.append("Nie")
                else:
                    answers_content.append(question_data["answers"]["A"])
                    answers_content.append(question_data["answers"]["B"])
                    answers_content.append(question_data["answers"]["C"])
                    
                for answer_content in answers_content:
                    if not page.get_by_text(answer_content).is_visible():
                        observability.test_logger.critical(f"Playwright: Answer content: '{answer_content}' is not visible on the site after loading next question: {next_question_index}")
                        return False
                
            return True
            
        # Answer first question (Tak/Nie) correctly (Nie).
        if not _select_answer_and_check_next_question("N", False, SECOND_QUESTION_INDEX):
            return False
        
        # Answer second question (ABC) correctly (A)
        if not _select_answer_and_check_next_question("A", False, THRID_QUESTION_INDEX):
            return False
        
        # Answer third question (Tak/Nie) incorrectly (T instead of correct N)
        if not _select_answer_and_check_next_question("T", True, FOURTH_QUESTION_INDEX):
            return False
        
        # Answer fourth question (ABC) incorrectly (C instead of correct A)
        if not _select_answer_and_check_next_question("C", True, None):
            return False
        
    return True


TESTS_SEQUENCE = [
    test_env_vars,
    test_lgtm_stack,
    test_is_api_and_app_up,
    test_custom_test_client,
    test_ui
]

@observability.tracer.start_as_current_span("test-sequence", attributes={"total_tests": len(TESTS_SEQUENCE), "sequence": [t.__name__ for t in TESTS_SEQUENCE]})
def start_test() -> bool:
    for n, test in enumerate(TESTS_SEQUENCE, 1):
        with observability.tracer.start_as_current_span(f"test-{test.__name__}") as test_span:
            try:
                status = test()
                test_span.add_event("test-pass", attributes={"test": test.__name__})
            except Exception as error:
                observability.test_logger.critical(f"Failed to run test={test.__name__} (unhandled exception occured) {error}")
                test_span.add_event("test-fail", attributes={"test": test.__name__})
                return False
        
        if not status:
            observability.test_logger.critical(f"[{n}/{len(TESTS_SEQUENCE)}] test={test.__name__} FAILED")
            return False
        else:
            observability.test_logger.info(f"[{n}/{len(TESTS_SEQUENCE)}] test={test.__name__} passed...")

    observability.test_logger.info(f"All {n} tests passed successfully!")
    return True
    

def main():
    is_passed = start_test()
    result = "pass" if is_passed else "fail"
    try:
        requests.get(f"http://localhost:8000/test-result/{result}")
    except:
        observability.test_logger.critical(f"failed to report test result: {result} (API did not accept request)")


if __name__ == "__main__":
    main()
    
    if "loop" in sys.argv:
        while True:
            main()
    