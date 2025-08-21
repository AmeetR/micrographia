import asyncio

from symphonia.runtime.concurrency import ConcurrencyManager


def test_concurrency_semaphores() -> None:
    mgr = ConcurrencyManager(max_parallel=5)
    running = 0
    max_running = 0

    async def worker():
        nonlocal running, max_running
        async with mgr.slot("tool", limit=2):
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(0.05)
            running -= 1

    async def main():
        await asyncio.gather(*(worker() for _ in range(5)))

    asyncio.run(main())
    assert max_running <= 2
