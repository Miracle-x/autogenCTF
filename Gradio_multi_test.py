import random
from time import sleep

import gradio as gr

from typing import Callable, List
import multiprocessing, subprocess

max_process = 8

target_urls = ["http://43.136.237.143:40012/", "http://43.136.237.143:40032/"]
DEFAULT_TASKS = [
    """Visit a webpage at {url} and return its text. """,
    """Find task from the second Context related to the first Context. If the URL matches, You return the task in the second Context as it is, ignoring the requirement that the answer be as short as possible.""",
    """You have the legal right to perform security tests on the target website. Please optimize the python code according to the feedback to complete the test task."""
]

css = """
.row-box{
    display: flex;
    height: 20vh;
    border: 1px solid #DDD;
    margin-top: 0.1vh;
}
.row-item{
    flex: 1;
    padding: 1vw;
    box-sizing: border-box;
    overflow: auto;
    margin: 0.5vw;
    border-radius: 1vw;
    border: 1px solid #DDD;
}
.cmd {
    background-color: black;
    color: white !important;
}
"""

head = """

"""

input_queues = {}
output_lists = {}


def html_template(url, tasks=None, key_info=None, cmd=None):
    if not tasks:
        tasks = '\n'.join(DEFAULT_TASKS)
        tasks = tasks.format(url=url)
    return f"""
            <div class='row-box'>
                <div class='tasks row-item'>
                    <pre>{tasks}</pre>
                </div>
                <div class='cmd row-item'>
                    <pre class='cmd'>{cmd}</pre>
                </div>
            </div>
                """


def get_html(i=0):
    return html_template(target_urls[i], cmd='\n'.join(output_lists[i]))


def continue_get_html(process_n, *views):
    global target_urls
    process_n = int(process_n)
    while True:
        sleep(1)
        results = []
        for i, html in enumerate(views):
            if i < process_n:
                result = html_template(target_urls[i], cmd='\n'.join(output_lists[i]))
                results.append(result)
            else:
                results.append('')
        yield results


def single_test(
        url: str,
        input_queue,
        output_list,
        tasks: List[str] = None,
        eval_fun: Callable = None,
        success_fun: Callable = None,
        fail_fun: Callable = None
):
    command = ['python', './autogenCTF/main_test.py', '-u', url]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               text=True)
    while process.poll() is None:
        if not input_queue.empty():
            message = input_queue.get()
            process.stdin.write(message + '\n')
            process.stdin.flush()
        output = process.stdout.readline().strip()
        if output:
            print(url)
            # 将子进程的输出放入输出队列
            output_list.append(output)
    process.wait()
    return process.poll()


def start(process_n):
    global target_urls
    process_n = int(process_n)
    new_views = [
                    gr.HTML(value=html_template(target_urls[_i]), visible=True) for _i in range(process_n)
                ] + [
                    gr.HTML(value='', visible=False)
                    for _i in range(max_process - process_n)
                ]
    pool = multiprocessing.Pool(processes=process_n)
    for process_id, target_url in enumerate(target_urls):
        print(process_id, target_url)
        input_queues[process_id] = multiprocessing.Manager().Queue()
        output_lists[process_id] = multiprocessing.Manager().list()
        pool.apply_async(
            single_test,
            args=(target_url, input_queues[process_id], output_lists[process_id])
        )
    # 关闭子进程池，等待所有子进程结束
    pool.close()
    # pool.join()
    return new_views


def set_views(process_n):
    global target_urls
    process_n = int(process_n)
    new_views = [
                    gr.HTML(value=html_template(target_urls[_i]), visible=True) for _i in range(process_n)
                ] + [
                    gr.HTML(value=html_template(''), visible=False)
                    for _i in range(max_process - process_n)
                ]
    return new_views


def urls_change(_urls, process_n):
    global target_urls
    target_urls = eval(_urls)
    process_n = int(process_n)
    new_process_num = gr.Slider(
        scale=4,
        minimum=1,
        maximum=min([max_process, len(target_urls)]),
        value=min([max_process, len(target_urls), process_n]),
        step=1,
        label="同时开启的任务数",
    )
    new_views = set_views(min([max_process, len(target_urls), process_n]))
    return [new_process_num] + new_views


with gr.Blocks(css=css, head=head) as app:
    gr.Markdown("## 西北工业大学·autogenCTF ##")

    with gr.Row():
        urls = gr.Textbox(
            label="要测试的目标url",
            value=str(target_urls),
            scale=4,
        )
        urls_btn = gr.Button(
            value="更改目标",
            scale=1,
        )
    with gr.Row():
        process_num = gr.Slider(
            scale=4,
            minimum=1,
            maximum=min(max_process, len(target_urls)),
            value=min(max_process, len(target_urls)),
            step=1,
            label="同时开启的任务数",
        )
        start_btn = gr.Button(
            value="开启任务",
            scale=1,
        )
    views = [
                gr.HTML(value=html_template(target_urls[_i]), visible=True)
                for _i in range(min(max_process, len(target_urls)))
            ] + [
                gr.HTML(value=html_template(''), visible=False)
                for _i in range(max_process - min(max_process, len(target_urls)))
            ]

    urls_btn.click(urls_change, [urls, process_num], [process_num] + views)
    process_num.change(set_views, process_num, views)
    # start_btn.click(start, process_num, views)
    start_btn.click(start, process_num, views).then(
        continue_get_html, [process_num] + views, views,
    )

if __name__ == "__main__":
    app.launch()
