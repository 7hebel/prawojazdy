from playwright.async_api import Page

from modules import observability
from modules import database

import random
import string
import os

def random_string(length: int) -> str:
    chars = string.ascii_letters + string.digits + "_"
    assert length < len(chars) - 1
    
    random_str = list(chars)
    random.shuffle(random_str)
    return (''.join(random_str))[:length]


def config_generator() -> dict:
    return {
        "username": "test-" + random_string(24),
        "password": random_string(8)
    }
    

async def launch_page(page: Page, config: dict) -> bool:
    await page.goto("http://localhost:5173", wait_until="domcontentloaded")
    page.set_default_timeout(5000)
    return True

async def check_ws_connection(page: Page, config: dict) -> bool:
    async with page.expect_websocket() as ws:
        webscoket = await ws.value
        if webscoket.is_closed():
            observability.test_logger.critical("page opened, but no WS connection is established (closed).")
            return False

        observability.test_logger.debug(f"Connected to the server WebSocket (as anon)")
        return True

async def verify_html_base_render(page: Page, config: dict) -> bool:
    main_view_locator = await page.wait_for_selector("main#quiz-view")
    if main_view_locator is None:
        observability.test_logger.critical("the <main id='quiz-view'> element has not been loaded after 3 seconds since WS connection established...")
        return False

    observability.test_logger.debug(f"The base HTML structure has been loaded")
    return True

async def open_account_management_panel(page: Page, config: dict) -> bool:
    account_panel_opener = await page.wait_for_selector("#account-panel")
    if account_panel_opener is None:
        observability.test_logger.critical("no #account-panel element found...")
        return False
    
    await account_panel_opener.click()
    observability.test_logger.debug(f"Opened account management panel...")
    return True

async def write_account_username(page: Page, config: dict) -> bool:
    username_input = await page.wait_for_selector("#account-username")
    username_accept = await page.wait_for_selector("#accept-username")
    
    if username_input is None:
        observability.test_logger.critical("no #account-username input found...")
        return False

    if username_accept is None:
        observability.test_logger.critical("no #accept-username button found...")
        return False
    
    await username_input.fill(config.get('username'))
    await username_accept.click()

    observability.test_logger.debug(f"Entered and accepted account username={config.get('username')}")
    return True

async def write_register_passwords(page: Page, config: dict) -> bool:
    register_password_input = await page.wait_for_selector("#register-password")
    register_password_repeat_input = await page.wait_for_selector("#register-password-repeat")

    if register_password_input is None or register_password_repeat_input is None:
        observability.test_logger.critical("no #register-password or #register-password-repeat input found, cannot register...")
        return False
    
    await register_password_input.fill(config.get('password'))
    await register_password_repeat_input.fill(config.get('password'))

    observability.test_logger.debug(f"Entered password={config.get('password')} for both register password inputs.")
    return True

async def register_account(page: Page, config: dict) -> bool:
    register_button = await page.wait_for_selector("#register-button")
    if register_button is None:
        observability.test_logger.critical("no #register-button button found, cannot register...")
        return False
    
    async with page.expect_response(lambda r: "/account/register" in r.url) as request:
        await register_button.click()

        response = await request.value
        if not response.ok:
            observability.test_logger.critical(f"Recevied incorrect response: {response.status} from request: {response.url}")
            return False

        observability.test_logger.debug(f"Accepted entered register data")
        return True
    
async def set_practice_seed(page: Page, config: dict) -> bool:
    db = await database.get_supabase()
    await db.table("Clients").update({"practice_seed": 3}).eq("name", config.get('username')).execute()

    observability.test_logger.debug(f"Set practice_seed=3 for user.")
    return True

async def logout_client(page: Page, config: dict) -> bool:
    logout_button = await page.wait_for_selector("#logout-button")
    if logout_button is None:
        observability.test_logger.critical("no #logout_button button found, cannot log out...")
        return False
    
    async with page.expect_response(lambda r: "/account/logout" in r.url) as request:
        await logout_button.click()
    
        response = await request.value
        if not response.ok:
            observability.test_logger.critical(f"Recevied incorrect response: {response.status} from request: {response.url}")
            return False

        observability.test_logger.debug(f"Logged out")
        return True
    
async def check_incorrect_password(page: Page, config: dict) -> bool:
    login_password_input = await page.wait_for_selector("#login-password")
    login_button = await page.wait_for_selector("#login-button")
    
    if login_password_input is None:
        observability.test_logger.critical("no #account-username input found, cannot login...")
        return False
    
    if login_button is None:
        observability.test_logger.critical("no #login-button button found, cannot login...")
        return False

    await login_password_input.fill("INCORRECT" + config.get('password'))
    observability.test_logger.debug(f"Entered incorrect password, trying to fail login")
    
    async with page.expect_response(lambda r: "/account/login" in r.url) as request:
        await login_button.click()

        response = await request.value
        if response.ok:
            observability.test_logger.critical(f"The server accepted login with incorrect password: {response.status} from request: {response.url}")
            return False

        observability.test_logger.debug(f"Received failed response for request with incorrect password")
        
        if not await login_button.is_visible():
            observability.test_logger.critical("after testing INCORRECT password the #login-button is no longer visible.")
            return False

        return True

async def login_client(page: Page, config: dict) -> bool:
    login_password_input = await page.wait_for_selector("#login-password")
    login_button = await page.wait_for_selector("#login-button")
    
    await login_password_input.fill(config.get('password'))
    
    async with page.expect_response(lambda r: "/account/login" in r.url) as request:
        await login_button.click()
        observability.test_logger.debug(f"Entered and accepted valid login password, logging in...")
    
        response = await request.value
        if not response.ok:
            observability.test_logger.critical(f"The server rejected login request with correct username={config.get('username')} and password={config.get('password')}  from request: {response.url}")
            return False
    
        return True

async def check_first_loaded_question(page: Page, config: dict) -> bool:
    FIRST_QUESTION_INDEX = os.getenv("q_index_1")
    
    main_view_locator = await page.wait_for_selector("main#quiz-view")
    loaded_question_index = await main_view_locator.get_attribute("question_index")

    try:
        await page.wait_for_function(
            """
            (i) => {
                const el = document.querySelector("main#quiz-view");
                return el && el.getAttribute("question_index") === i;
            }
            """,
            arg=FIRST_QUESTION_INDEX
        )
        observability.test_logger.debug(f"The first question has been correctly loaded (index={FIRST_QUESTION_INDEX})")
        return True
    
    except:
        observability.test_logger.critical(f"client received incorrect question! Expected question: {FIRST_QUESTION_INDEX}, got: {loaded_question_index}. This may happen when: incorrect practice_seed is set (not '3') or the total amount of questions has changed")
        return False
    
    
async def try_continue_without_answer(page: Page, config: dict) -> bool:
    continue_btn = await page.wait_for_selector("#continue-btn")
    await continue_btn.click()

    try:
        await page.wait_for_function(
            """
            () => {
                const el = document.querySelector("#continue-btn");
                return el && el.classList.contains("error-animation");
            }
            """
        )
        observability.test_logger.debug(f"The `continue` button has been clicked without selecting answer and is playing animation")
        observability.test_logger.debug(f"ensuring the displayed question is still the first question...")
        return True
    
    except:
        observability.test_logger.critical(f"clicked `continue` button without selecting a answer but the button did not contain a `error-animation` class")
        return False
        

def select_answer_and_verify_next_question_builder(answer: str, is_correct: bool, next_question_index: str | None):
    async def select_answer_and_verify_next_question(page: Page, config: dict) -> bool:
        continue_btn = await page.wait_for_selector("#continue-btn")
        
        await page.click(f"#possible-answer-{answer}")
        await continue_btn.click()
        
        # If answering incorrect answer, there is additional 3 seconds wait time...
        if not is_correct:
            await page.wait_for_timeout(3000)
            
        # Check if the next question index matches desired one.
        if next_question_index is None:
            return True
        
        try:
            await page.wait_for_function(
                """
                (e) => {
                    const el = document.querySelector("main#quiz-view");
                    return el && el.getAttribute("question_index") == e;
                }
                """,
                arg=next_question_index,
                timeout=10_000
            )
            observability.test_logger.debug(f"The displayed question has successfully changed to desired: {next_question_index} after answer")
        except:
            observability.test_logger.critical(f"The displayed question has not changed to desired {next_question_index}")
            return False
        
        # Check if question and all answers are visible on site.
        question_data = await database.fetch_question(int(next_question_index))
        if not await (page.get_by_text(question_data["question"])).is_visible():
            observability.test_logger.critical(f"Question content is not visible on the site after loading next question: {next_question_index}")
            return False
        observability.test_logger.debug(f"The question content is visible on the site.")
        
        answers_content = []
        if question_data["correct_answer"] in "TN":
            answers_content.append("Tak")
            answers_content.append("Nie")
        else:
            answers_content.append(question_data["answers"]["A"])
            answers_content.append(question_data["answers"]["B"])
            answers_content.append(question_data["answers"]["C"])
            
        for answer_content in answers_content:
            if not await (page.get_by_text(answer_content)).is_visible():
                observability.test_logger.critical(f"Answer content: '{answer_content}' is not visible on the site after loading next question: {next_question_index}")
                return False
            
        observability.test_logger.debug(f"All of the answers are visible on the screen.")
        return True

    return select_answer_and_verify_next_question

    