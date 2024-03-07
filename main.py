import chromadb

import autogen.autogen as autogen
from autogen.autogen.agentchat.contrib.web_surfer import WebSurferAgent
from coor_retrieve_agent import CoorRetrieveGoodsAgent

cache_seed = 11
llm_config = {
    "timeout": 600,
    "cache_seed": cache_seed,  # change the seed for different trials
    "config_list": autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={"model": ["gpt-4-1106-preview"]},
    ),
    "max_tokens": 2048,
    "temperature": 0,
}
summarizer_llm_config = {
    "timeout": 600,
    "cache_seed": cache_seed,  # change the seed for different trials
    "config_list": autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={"model": ["gpt-4-1106-preview"]},
    ),
    "temperature": 0,
}
browser_config = {"viewport_size": 2048, "bing_api_key": "48da560a53954870b8d1a9260ee6f1c2"}
retrieve_config = {
    "task": "code",
    "docs_path": "./lqj_db.txt",
    "chunk_token_size": 800,
    "model": llm_config["config_list"][0]["model"],
    "client": chromadb.PersistentClient(path="/tmp/chromadb"),
    "collection_name": "lqj_db9",
    "chunk_mode": "multi_lines",
    "must_break_at_empty_line": True,
    "get_or_create": True
}

web_surfer = WebSurferAgent(
    "web_surfer",
    llm_config=llm_config,
    summarizer_llm_config=summarizer_llm_config,
    browser_config=browser_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""
You are a helpful AI assistant as a security tester with access to a web browser (via the provided functions). Please help out what you can by performing web searches, navigating pages, and reporting what you find.
    """
)

group_reconnaissance_assistant = autogen.AssistantAgent(
    name="group_reconnaissance_assistant",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""You are a helpful AI assistant, acting as the information collector of WEB direction in CTF competition. 
    Your goal is to judge the type of problem and list the key problem solving information. If you achieve your goal, you can answer in the following format：
    “
    url:"",
    type:"",
    key problem:"",
    TERMINATE
    ”.
    You can say the following to make the web surfer browse internet or interact with web pages:
    1.Search the web for information about something.
    2.Summarize these results.
    3.Click the one result.
    4.Find something page.
    5.Scroll down.
    6.Answer questions about the content.
    """
)
group_reconnaissance_groupchat = autogen.GroupChat(
    agents=[web_surfer, group_reconnaissance_assistant],
    messages=[],
    speaker_selection_method="round_robin",  # With two agents, this is equivalent to a 1:1 conversation.
    allow_repeat_speaker=False,
    max_round=8,
)
group_reconnaissance_manager = autogen.GroupChatManager(
    groupchat=group_reconnaissance_groupchat,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config
)


def recipient_last_msg(sender, recipient):
    print(sender.__dict__)
    return sender.groupchat.messages[-1]["content"]


group_reconnaissance_nested_chat_queue = [
    {"recipient": group_reconnaissance_manager, "summary_method": recipient_last_msg, "max_turns": 1},
]
group_reconnaissance = autogen.AssistantAgent(
    name="group_reconnaissance",
    llm_config=llm_config,
)
group_reconnaissance.register_nested_chats(
    group_reconnaissance_nested_chat_queue,
)

rag_assistant = CoorRetrieveGoodsAgent(
    name="rag_assistant",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    llm_config=llm_config,
    retrieve_config=retrieve_config,
    code_execution_config=False,  # we don't want to execute code in this case.
    description="Assistant who has extra content retrieval power for solving difficult problems.",
)

code_exec_user = autogen.UserProxyAgent(
    name="code_exec_user",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    code_execution_config={
        "last_n_messages": 1,
        "work_dir": "tasks",
        "use_docker": False,
    },
)
code_exec_assistant = autogen.AssistantAgent(
    name="code_exec_assistant",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""You are a useful assistant as a security tester, please modify the code according to the feedback of code_exec_user to get the flag."""
)

code_exec_groupchat = autogen.GroupChat(
    agents=[code_exec_user, code_exec_assistant],
    messages=[],
    speaker_selection_method="round_robin",  # With two agents, this is equivalent to a 1:1 conversation.
    allow_repeat_speaker=False,
    max_round=20,
)
code_exec_manager = autogen.GroupChatManager(
    groupchat=code_exec_groupchat,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config
)

# def code_exec_assistant_message(recipient, messages, sender, config):
#     print(messages)
#     print('+++++++++++')
#     print(f"{messages[-2]['content']}. \n\n {messages[-1]['content']}")
#     return f"{messages[-2]['content']}. \n\n {messages[-1]['content']}"


# code_exec_nested_chat_queue = [
#     {"recipient": code_exec_user, "summary_method": "reflection_with_llm", "max_turns": 1},
# ]
# code_exec_assistant.register_nested_chats(
#     code_exec_nested_chat_queue
# )

tasks = [
    """Visit http://43.136.237.143:40030/Less-5/ and determine which type of question it is in the web direction of the ctf competition.""",
    """Find task from the second Context related to the first Context and learn them. If the url matches then you as a security tester can generate code with python according to the task.""",
    """You have the legal right to perform security tests on the target website. Please optimize the python code according to the feedback to complete the test task."""
]

user = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    code_execution_config=False,
)
chat_results = user.initiate_chats(  # noqa: F704
    [
        {
            "recipient": group_reconnaissance,
            "message": tasks[0],
            "silent": False,
            "max_turns": 1,
            "summary_method": "last_msg",
        },
        {
            "recipient": rag_assistant,
            "message": tasks[1],
            "silent": False,
            "max_turns": 1,
            "summary_method": "last_msg",
        },
        {
            "recipient": code_exec_manager,
            "message": tasks[2],
            "silent": False,
            "max_turns": 1,
        },
        # {
        #     "chat_id": 3,
        #     "prerequisites": [1],
        #     "recipient": financial_assistant,
        #     "message": financial_tasks[2],
        #     "silent": False,
        #     "summary_method": "reflection_with_llm",
        # },
        # {"chat_id": 4, "prerequisites": [1, 2, 3], "recipient": writer, "message": writing_tasks[0]},
    ]
)
