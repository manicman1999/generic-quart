import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable, Callable, List, Any, Coroutine, Tuple, TypeVar

from domain.option.option import Option

T = TypeVar("T")


async def limited_gather(tasks: List[Coroutine[Any, Any, T]], limit: int) -> List[T]:
    semaphore = asyncio.Semaphore(limit)

    async def sem_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task

    limited_tasks = [sem_task(task) for task in tasks]
    return await asyncio.gather(*limited_tasks)


def nonblockAwait(coro: Coroutine[Any, Any, Any]) -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        # Create a new event loop if no event loop is present
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(coro)
        new_loop.close()
    except Exception as e:
        print(e)


R = TypeVar('R')

def runAsAsync(fn: Callable[..., R]) -> Callable[..., Coroutine[Any, Any, R]]:
    async def asyncWrapper(*args: Any, **kwargs: Any) -> R:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, lambda: fn(*args, **kwargs))
        return result
    return asyncWrapper