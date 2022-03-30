import asyncio
from common.comm_func import entrace
import os


def main(test_cases):
    """
    事件循环主函数，负责所有接口请求的执行
    :param test_cases:
    :return:
    """
    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(10)
    # 需要处理的任务
    task = loop.create_task(entrace(test_cases, loop, semaphore))
    # 将协程注册到事件循环，并启动事件循环
    try:
        # loop.run_until_complete(asyncio.gather(*tasks))
        loop.run_until_complete(task)
    finally:
        loop.close()

    return task.result()


if __name__ == '__main__':
    # 获取当前文件路径
    current_path = os.path.abspath(__file__)
    # 获取当前文件的父目录
    project_dir = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
    test_case_dir = os.path.join(project_dir, "testcase")
    test_case_files = os.listdir(test_case_dir)
    test_cases = [test_case_dir + os.sep + test_case_name for test_case_name in test_case_files]
    main(test_cases)
