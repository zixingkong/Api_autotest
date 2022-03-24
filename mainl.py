

def main(test_cases):
    """
    事件循环主函数，负责所有接口请求的执行
    :param test_cases:
    :return:
    """
    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(bxmat.semaphore)
    # 需要处理的任务
    # tasks = [asyncio.ensure_future(one(case_name=test_case, semaphore=semaphore)) for test_case in test_cases]
    task = loop.create_task(entrace(test_cases, loop, semaphore))
    # 将协程注册到事件循环，并启动事件循环
    try:
        # loop.run_until_complete(asyncio.gather(*tasks))
        loop.run_until_complete(task)
    finally:
        loop.close()

    return task.result()