import chromadb
import autogen.autogen as autogen
from autogen.autogen.agentchat.contrib.web_surfer import WebSurferAgent
from coor_retrieve_agent import CoorRetrieveGoodsAgent

task = """This is a ctf competition，please test http://43.136.237.143:40030/Less-5/ and get the flag. """
cache_seed = 8
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
browser_config = {"viewport_size": 65536, "bing_api_key": "48da560a53954870b8d1a9260ee6f1c2"}
retrieve_config = {
    "task": "code",
    "docs_path": "./test1.pdf",
    "chunk_token_size": 1024,
    "model": llm_config["config_list"][0]["model"],
    "client": chromadb.PersistentClient(path="/tmp/chromadb"),
    "collection_name": "test1",
    "get_or_create": True,
    # "n_results": 1
}

web_surfer = WebSurferAgent(
    "web_surfer",
    llm_config=llm_config,
    summarizer_llm_config=summarizer_llm_config,
    browser_config=browser_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""
You are a helpful AI assistant with access to a web browser (via the provided functions). Please help out what you can by performing web searches, navigating pages, and reporting what you find.
    """
)

group_reconnaissance_assistant = autogen.AssistantAgent(
    name="group_reconnaissance_assistant",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""You are a helpful AI assistant, acting as the information collector of WEB direction in CTF competition. 
    Your goal is to judge the type of problem and list the key problem solving information. If you achieve your goal, you can answer in the following format：
    “
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
    name="group_reconnaissance_manager",
    groupchat=group_reconnaissance_groupchat,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config,
    description="""If there is no relevant information about the task, you should be chosen to speak in response to the information about the task."""
)
# group_reconnaissance_nested_chat_queue = [
#     {"recipient": group_reconnaissance_manager, "summary_method": "reflection_with_llm", "max_turns": 1},
# ]
# group_reconnaissance = autogen.AssistantAgent(
#     name="group_reconnaissance",
#     llm_config=llm_config,
# )
# group_reconnaissance.register_nested_chats(
#     group_reconnaissance_nested_chat_queue,
# )

# learn_group = autogen.GroupChat(
#     agents=[],
#     messages=[],
#     speaker_selection_method="round_robin",  # With two agents, this is equivalent to a 1:1 conversation.
#     allow_repeat_speaker=False,
#     max_round=8,
# )
# learn_group_manager = autogen.GroupChatManager(
#     groupchat=learn_group,
#     llm_config=llm_config
# )

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
    system_message="""You are a useful assistant as a security tester, please modify the code according to the feedback of code_exec_user to completion plan."""
)

code_exec_groupchat = autogen.GroupChat(
    agents=[code_exec_assistant, code_exec_user, ],
    messages=[],
    speaker_selection_method="round_robin",  # With two agents, this is equivalent to a 1:1 conversation.
    allow_repeat_speaker=False,
    max_round=20,
)
code_exec_manager = autogen.GroupChatManager(
    name="code_exec_manager",
    groupchat=code_exec_groupchat,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config,
    description="""Execute the planner's plan."""
)

# exec_group = autogen.GroupChat(
#     agents=[],
#     messages=[],
#     speaker_selection_method="round_robin",  # With two agents, this is equivalent to a 1:1 conversation.
#     allow_repeat_speaker=False,
#     max_round=8,
# )
# exec_group_manager = autogen.GroupChatManager(
#     name="exec_group_manager",
#     groupchat=exec_group,
#     llm_config=llm_config,
#     description="""Execute the planner's plan."""
# )

planner = autogen.AssistantAgent(
    name="planner",
    llm_config=llm_config,
    system_message=f"""You're a thoughtful, logical web test planner. You can improve your plans at any time. 
    "{task}" is your task to keep in mind, and all your plans are for this task. 
    Your answer should be: a list of plans for the next plan. Follow the following format：
    
     {{Plan List：[plan1,plan2...],
     Next Plan: plan2,}}
     
     Among them, plans such as plan1 and plan2 need to be generated by your own thinking.""",
    description="""Develop and improve test plans based on task and other people's answers."""
)

task_group = autogen.GroupChat(
    agents=[group_reconnaissance_manager, planner, code_exec_manager, ],
    messages=[],
    speaker_selection_method="auto",  # With two agents, this is equivalent to a 1:1 conversation.
    allow_repeat_speaker=False,
    max_round=8,
)

task_group_manager = autogen.GroupChatManager(
    groupchat=task_group,
    llm_config=llm_config
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    system_message=task,
    code_execution_config=False,
    human_input_mode="NEVER",
    llm_config=False,
    description="""Never select me as a speaker."""
)

user_proxy.initiate_chat(
    task_group_manager,
    message=task,
    clear_history=True
)
