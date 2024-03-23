import autogen
from autogen.agentchat.contrib.web_surfer import WebSurferAgent

from autogenCTF.attack.attack_agent import AttackAgent
from autogenCTF.reconnaissance.reconnaissance_agent import ReconnaissanceAgent
from autogenCTF.tools.code_exec_agent import CodeExecAgent
from tool_sqlmap import SqlmapAgent

# 配置文件
config_list = [
    {
        "model": "gpt-4",
        "api_key": "sk-itUIKUlHKRBYopUzD2Df6fC6Db4d4f7f9163F89c6b8455E3",
        "base_url": "https://api.kwwai.top/v1"
    },
]
llm_config = {
    # "request_timeout": 600,
    "seed": 46,
    "config_list": config_list,
    "temperature": 0
}


user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

# 第一阶段代理设置
reconnaissance_agent = ReconnaissanceAgent(
    name="reconnaissance_agent",
    llm_config=llm_config,
    # return_mode="SIMPLE_CODE"
)

# # 第一阶段任务
# user_proxy.send(
#     message="Reconnaissance http://43.136.237.143:40033/",
#     recipient=reconnaissance_agent,
#     request_reply=True
# )

# 第二阶段代理设置
code_exec_agent = CodeExecAgent(
    name="code_exec_agent",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)
code_exec_sqlmap = SqlmapAgent(
    name="code_exec_sqlmap",
    llm_config=llm_config
)
browser_config = {"viewport_size": 2048, "bing_api_key": "48da560a53954870b8d1a9260ee6f1c2"}
web_surfer = WebSurferAgent(
    "web_surfer",
    llm_config=llm_config,
    summarizer_llm_config=llm_config,
    browser_config=browser_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""
    You are a helpful AI assistant as a web security tester with access to a web browser (via the provided functions). Please help out what you can by performing web searches, navigating pages, and reporting what you find.
    """
)

attack_assistant = AttackAgent(
    name="plan_assistant",
    llm_config=llm_config,
    agents=[code_exec_agent, reconnaissance_agent, code_exec_sqlmap]
)

# 开始聊天
user_proxy.initiate_chat(
    recipient=attack_assistant,
    message="""get the flag

### 题目链接

[http://43.136.237.143:40033](http://43.136.237.143:40033/)

**下面文件夹是提供给参赛选手的代码**

https://github.com/fbsamples/fbctf-2019-challenges/tree/main/web/products-manager/dist

描述：

This challenge is a database storage where users can create and view products (protected by secrets). There are already 5 products in the database, one of them has the flag in its description.""",
    clear_history=False,
    request_reply=True
)
