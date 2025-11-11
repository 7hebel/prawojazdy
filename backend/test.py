import dotenv
import asyncio
import os

# Load configs.
dotenv.load_dotenv(".env")
dotenv.load_dotenv("tests.env")

from tests.runner import TestsRunner
from tests import pre_tests
from tests import web_tests


PRE_TESTS = [
    pre_tests.test_env_vars,
    pre_tests.test_lgtm_stack,
    pre_tests.test_is_api_and_app_up,
]

WEB_TESTS = [
    web_tests.launch_page,
    web_tests.check_ws_connection,
    web_tests.verify_html_base_render,
    web_tests.open_account_management_panel,
    web_tests.write_account_username,
    web_tests.write_register_passwords,
    web_tests.register_account,
    web_tests.set_practice_seed,
    web_tests.open_account_management_panel,
    web_tests.logout_client,
    web_tests.open_account_management_panel,
    web_tests.write_account_username,
    web_tests.check_incorrect_password,
    web_tests.login_client,
    web_tests.check_first_loaded_question,
    web_tests.try_continue_without_answer,
    web_tests.check_first_loaded_question,
    web_tests.select_answer_and_verify_next_question_builder(
        answer="N",
        is_correct=False,
        next_question_index=os.getenv("q_index_2")
    ),
    web_tests.select_answer_and_verify_next_question_builder(
        answer="A",
        is_correct=False,
        next_question_index=os.getenv("q_index_3")
    ),
    web_tests.select_answer_and_verify_next_question_builder(
        answer="T",
        is_correct=True,
        next_question_index=os.getenv("q_index_4")
    ),
    web_tests.select_answer_and_verify_next_question_builder(
        answer="C",
        is_correct=True,
        next_question_index=None
    ),
]

runner = TestsRunner(
    pre_tests=PRE_TESTS,
    web_tests=WEB_TESTS,
    config_generator=web_tests.config_generator
)

asyncio.run(runner.run())
