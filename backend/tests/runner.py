from playwright.async_api import async_playwright
from collections.abc import Callable
import requests
import asyncio
import logging
import time
import os

from modules import observability
from tests import interface


class TestsRunner:
    """
    `pre_tests` set is executed once - to ensure environment is correctly configured (test DB, API, etc...)  
    `web_tests` is a set of sequential tests ran in the exact order. Each test is provided with the state of the browser left by previous test.
    `config_generator` is a function returning a dictionary with configuration for the entire `web_tests` sequence. 
    """
    
    def __init__(self, pre_tests: list[Callable], web_tests: list[Callable], config_generator: Callable):
        self.pre_tests = pre_tests
        self.web_tests = web_tests
        self.config_generator = config_generator
        
        self.n_workers = int(os.getenv("n_workers")) or 1
        self.on_fail = os.getenv("on_fail") or "exit"
        if self.on_fail not in ("exit", "continue"):
            observability.test_logger.warning(f"invalid TestRunner configuration: on_fail={self.on_fail} is not one of: exit/continue (using: exit)")
        self.loop = os.getenv("loop") == "true"
        self.verbose = os.getenv("verbose") == "true"

        interface.clear_screen()
        interface.print_config({
            "Workers": self.n_workers,
            "On fail": self.on_fail,
            "Loop": self.loop,
            "Verbose": self.verbose
        })
        
        if not self.verbose:
            for handler in observability.test_logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.WARNING)
        
    @observability.tracer.start_as_current_span("testing-pre-tests-sequence")
    def __run_pretests(self) -> bool:
        for n, test in enumerate(self.pre_tests, 1):
            with observability.tracer.start_as_current_span("pre-test", attributes={"pre-test-name": test.__name__}) as pretest_span:
                try:
                    test_start_time = time.time()
                    status = test()
                    test_total_time = time.time() - test_start_time
                    interface.context_test_step_result(n, len(self.pre_tests), test.__name__, status, test_total_time)

                except Exception as error:
                    observability.test_logger.critical(f"Failed to execute pre-test: {test.__name__}: {error}")
                    interface.context_test_step_result(n, len(self.pre_tests), test.__name__, False)
                    status = False
                
                if status:
                    observability.test_logger.info(f"[{n}/{len(self.pre_tests)}] pre-test={test.__name__} passed...")
                    pretest_span.add_event("pass")

                else:                    
                    observability.test_logger.info(f"[{n}/{len(self.pre_tests)}] pre-test={test.__name__} FAILED")
                    pretest_span.add_event("fail")
                    return False

        observability.test_logger.info(f"All {n} pre-tests passed successfully! Can continue to web-tests...")
        return True
    
    @observability.tracer.start_as_current_span("testing-web-tests-sequence")
    async def __run_webtests(self, no_step_logs: bool = False) -> bool:
        test_start_time = time.time()
        
        config = self.config_generator()
        if not no_step_logs:
            interface.context_key_value_point("Dynamic config", config)
            interface.context_separator()
        
        observability.test_logger.debug(f"Generated configuration for tests sequence config={config}")
        
        async with async_playwright() as playwright:
            engine = playwright.chromium
            browser = await engine.launch()
            page = await browser.new_page()
            
            for n, test in enumerate(self.web_tests, 1):
                with observability.tracer.start_as_current_span("web-test", attributes={"web-test-name": test.__name__}) as webtest_span:
                    test_step_start_time = time.time()
                    status = await test(page, config)
                    test_step_total_time = time.time() - test_step_start_time 

                    if not no_step_logs:
                        interface.context_test_step_result(n, len(self.web_tests), test.__name__, status, test_step_total_time)

                    if status:
                        observability.test_logger.info(f"[{n}/{len(self.web_tests)}] web-test={test.__name__} passed...")
                        webtest_span.add_event("pass")
    
                    else:                    
                        observability.test_logger.error(f"[{n}/{len(self.web_tests)}] web-test={test.__name__} FAILED")
                        webtest_span.add_event("fail")
                        return False
                        
            observability.test_logger.info(f"All {len(self.web_tests)} web-tests passed successfully!")
            
            test_total_time = time.time() - test_start_time
            if self.n_workers > 1:
                interface.context_message_success(f"🌟 Pass: {round(test_total_time, 2)}s")
            else:
                interface.context_separator()
                interface.context_message_success("🌟 web-tests passed")
                interface.context_finish(test_total_time)
            
            return True
                      
    async def run(self) -> None:
        interface.context_header("🔎 Running environment checks")
        interface.context_key_value_point("Pre-tests", len(self.pre_tests))
        interface.context_separator()
        pretests_start = time.time()
        pretests_status = self.__run_pretests()
        pretest_total_time = time.time() - pretests_start

        interface.context_separator()
        if not pretests_status:
            interface.context_message_error("❌ Cannot proceed, checks failed")
            interface.context_finish(pretest_total_time)
            return self.__report_result(False)
        else:
            interface.context_message_success("🌟 Checks succeeded")
            interface.context_finish(pretest_total_time)
        
        if self.n_workers > 1:
            interface.context_header("🧪 Test sequence")
            interface.context_key_value_point("Web-tests", len(self.web_tests))
            interface.context_key_value_point("Workers", self.n_workers)
            interface.context_separator()
            
            workers = [asyncio.create_task(self.__run_worker(silent=True)) for _ in range(self.n_workers)]
            await asyncio.gather(*workers)
        else:
            await self.__run_worker()
            
    async def __run_single_webtest_sequence(self, silent: bool) -> None:
        test_start_time = time.time()
        webtests_status = await self.__run_webtests(no_step_logs=silent)
        test_total_time = time.time() - test_start_time

        self.__report_result(webtests_status, test_total_time)
        
        if not webtests_status and self.on_fail == "exit":
            exit()
        
    async def __run_worker(self, silent: bool = False) -> None:
        while True:
            if self.n_workers == 1:
                interface.context_header("🧪 Test sequence")
                interface.context_key_value_point("Web-tests", len(self.web_tests))
            
            await self.__run_single_webtest_sequence(silent)

            if not self.loop:
                return
            
    def __report_result(self, result: bool, total_time: float = 0) -> None:
        result = "pass" if result else "fail"
        try:
            requests.get(f"http://localhost:8000/test-result/{result}/{total_time}/{self.n_workers}")
        except:
            observability.test_logger.critical(f"failed to report test result: {result} (API did not accept request)")
            exit()
            
        