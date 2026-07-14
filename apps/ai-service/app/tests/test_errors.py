import unittest
import asyncio
from app.orchestrator.errors import (
    WorkflowTimeoutError,
    AgentExecutionError,
    retry_on_failure
)

class TestErrors(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_exception_properties(self):
        err = AgentExecutionError("agent failed")
        self.assertEqual(err.message, "agent failed")
        self.assertEqual(err.error_code, "AGENT_EXECUTION_ERROR")
        
        timeout_err = WorkflowTimeoutError("timeout occurred")
        self.assertEqual(timeout_err.error_code, "TIMEOUT_ERROR")

    def test_retry_on_failure_success(self):
        calls = 0
        
        @retry_on_failure(retries=3, base_delay=0.01, backoff_factor=1.1)
        async def flaky_function():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("Temporary failure")
            return "success"
            
        async def run_test():
            res = await flaky_function()
            self.assertEqual(res, "success")
            self.assertEqual(calls, 3)
            
        self.loop.run_until_complete(run_test())

    def test_retry_on_failure_exhaustion(self):
        calls = 0
        
        @retry_on_failure(retries=2, base_delay=0.01, backoff_factor=1.1)
        async def failing_function():
            nonlocal calls
            calls += 1
            raise RuntimeError("Permanent failure")
            
        async def run_test():
            with self.assertRaises(RuntimeError):
                await failing_function()
            self.assertEqual(calls, 3) # 1 initial + 2 retries
            
        self.loop.run_until_complete(run_test())

if __name__ == "__main__":
    unittest.main()
