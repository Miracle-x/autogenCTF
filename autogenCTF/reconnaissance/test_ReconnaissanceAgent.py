import autogen
from autogenCTF.reconnaissance.reconnaissance_agent import ReconnaissanceAgent

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
    "seed": 45,
    "config_list": config_list,
    "temperature": 0
}

# 代理设置
assistant = ReconnaissanceAgent(
    name="assistant",
    llm_config=llm_config,
    # return_mode="SIMPLE_CODE"
)

user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

user_proxy.send(
    message="Reconnaissance http://43.136.237.143:40033/",
    recipient=assistant,
    request_reply=True
)
