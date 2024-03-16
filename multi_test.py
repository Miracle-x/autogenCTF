from time import sleep
from typing import Callable, List
import multiprocessing, subprocess

# 创建输入队列和输出队列的字典
input_queues = {}
output_queues = {}


def single_test(
        process_id: int,
        url: str,
        input_queue,
        output_queue,
        tasks: List[str] = None,
        eval_fun: Callable = None,
        success_fun: Callable = None,
        fail_fun: Callable = None
):
    command = ['python', './autogenCTF/main_test.py', '-u', url]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    while process.poll() is None:
        if not input_queue.empty():
            message = input_queue.get()
            process.stdin.write(message + '\n')
            process.stdin.flush()
        output = process.stdout.readline().strip()
        if output:
            # 将子进程的输出放入输出队列
            output_queue.put(output)
    process.wait()
    return process.poll()

    # exit()
    # res, params = eval_fun(res)
    # if (res):
    #     success_fun(params)
    # else:
    #     fail_fun(params)


def parent_process(input_queues, output_queues):
    while True:
        # 检查子进程是否有输出要传递给父进程
        for process_id, output_queue in output_queues.items():
            if not output_queue.empty():
                output = output_queue.get()
                # 父进程处理子进程的输出
                print(f"Output from Child Process {process_id}: {output}")
        # 检查父进程是否有新消息要发送给子进程
        for process_id, input_queue in input_queues.items():
            if not input_queue.empty():
                message = input_queue.get()
                print(message)
                if message == 'exit':
                    break

                # 向特定进程的子进程发送消息
                input_queue.task_done()


if __name__ == '__main__':
    target_url = ['http://43.136.237.143:40032/', 'http://43.136.237.143:40012/']
    # 创建进程池
    pool = multiprocessing.Pool(processes=2)
    for process_id, target_url in enumerate(target_url):
        input_queues[process_id] = multiprocessing.Manager().Queue()
        output_queues[process_id] = multiprocessing.Manager().Queue()
        pool.apply_async(
            single_test,
            args=(process_id, target_url, input_queues[process_id], output_queues[process_id])
        )
    # 启动父进程
    parent_process(input_queues, output_queues)
    # 关闭子进程池，等待所有子进程结束
    pool.close()
    pool.join()
