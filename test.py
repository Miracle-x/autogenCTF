import autogen.autogen as autogen
from autogen.autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.autogen.agentchat.contrib.web_surfer import WebSurferAgent
from coor_retrieve_agent import CoorRetrieveGoodsAgent

cache_seed = 5
llm_config = {
    "timeout": 600,
    "cache_seed": cache_seed,  # change the seed for different trials
    "config_list": autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={"model": ["gpt-3.5-turbo"]},
    ),
    "temperature": 0,
}
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config=llm_config
)
# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # set to True or image name like "python:3" to use docker
    },
)
# the assistant receives a message from the user_proxy, which contains the task description
user_proxy.initiate_chat(
    assistant,
    message="""What date is today? Compare the year-to-date gain for META and TESLA.""",
)