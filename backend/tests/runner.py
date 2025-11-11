from playwright.async_api import async_playwright
from collections.abc import Callable
import requests
import asyncio
import time
import os

from modules import observability


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
        
    @observability.tracer.start_as_current_span("testing-pre-tests-sequence")
    def __run_pretests(self) -> bool:
        for n, test in enumerate(self.pre_tests, 1):
            with observability.tracer.start_as_current_span("pre-test", attributes={"pre-test-name": test.__name__}) as pretest_span:
                try:
                    status = test()

                except Exception as error:
                    observability.test_logger.critical(f"Failed to execute pre-test: {test.__name__}: {error}")
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
    async def __run_webtests(self) -> bool:
        config = self.config_generator() 
        observability.test_logger.debug(f"Generated configuration for tests sequence config={config}")
        
        async with async_playwright() as playwright:
            engine = playwright.chromium
            browser = await engine.launch()
            page = await browser.new_page()
            
            for n, test in enumerate(self.web_tests, 1):
                with observability.tracer.start_as_current_span("web-test", attributes={"web-test-name": test.__name__}) as webtest_span:
                    status = await test(page, config)

                    if status:
                        observability.test_logger.info(f"[{n}/{len(self.web_tests)}] web-test={test.__name__} passed...")
                        webtest_span.add_event("pass")
    
                    else:                    
                        observability.test_logger.error(f"[{n}/{len(self.web_tests)}] web-test={test.__name__} FAILED")
                        webtest_span.add_event("fail")
                        return False
                        
            observability.test_logger.info(f"All {len(self.web_tests)} web-tests passed successfully!")
            return True
                      
    async def run(self) -> None:
        pretests_status = self.__run_pretests()
        if not pretests_status:
            return self.__report_result(False)
        
        if self.n_workers > 1:
            workers = [asyncio.create_task(self.__run_worker()) for _ in range(self.n_workers)]
            await asyncio.gather(*workers)
        else:
            await self.__run_worker()
            
    async def __run_single_webtest_sequence(self) -> None:
        test_start_time = time.time()
        webtests_status = await self.__run_webtests()
        test_total_time = time.time() - test_start_time
        
        self.__report_result(webtests_status, test_total_time)
        
        if not webtests_status and self.on_fail == "exit":
            exit()
        
    async def __run_worker(self) -> None:
        await self.__run_single_webtest_sequence()

        if not self.loop:
            return
            
        while True:
            await self.__run_single_webtest_sequence()
            
    def __report_result(self, result: bool, total_time: float = 0) -> None:
        result = "pass" if result else "fail"
        try:
            requests.get(f"http://localhost:8000/test-result/{result}/{total_time}/{self.n_workers}")
        except:
            observability.test_logger.critical(f"failed to report test result: {result} (API did not accept request)")
            exit()
            
        