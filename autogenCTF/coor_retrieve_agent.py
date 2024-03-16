from autogen import AssistantAgent, Agent
from typing import Dict, Optional, Union, List, Tuple, Any

from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.contrib.text_analyzer_agent import TextAnalyzerAgent


class CoorRetrieveGoodsAgent(AssistantAgent):
    def __init__(
            self,
            name: str,
            llm_config: Optional[Union[Dict, bool]],
            retrieve_config: Optional[Union[Dict, bool]],
            **kwargs
    ):
        super().__init__(
            name,
            llm_config=llm_config,
            **kwargs
        )

        self.analyzer = TextAnalyzerAgent(llm_config=llm_config)
        self.register_reply(Agent, CoorRetrieveGoodsAgent._generate_retrieve_goods_reply)
        self.retrieve_config = retrieve_config
        self.ragproxyagent = RetrieveUserProxyAgent(
            name="inner_rag_proxy_user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            retrieve_config=self.retrieve_config,
            code_execution_config=False,
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        )
        self.assistant = RetrieveAssistantAgent(
            name="inner_rag_proxy_assistant",
            system_message="You are a helpful assistant as a security tester. If you answer the question, add the 'TERMINATE' after the answer.",
            # is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
            llm_config=self.llm_config,
        )

    def _generate_retrieve_goods_reply(
            self,
            messages: Optional[List[Dict]] = None,
            sender: Optional[Agent] = None,
            config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        if config is None:
            config = self
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]
        url = self.analyzer.analyze_text(message.get('content'), "Extract the test_target_url without quotation mark").replace('TERMINATE', '').strip()
        print('aaaaaaaaaaa'+url+'aaaaaaaaa')
        self.ragproxyagent.initiate_chat(
            self.assistant,
            problem=message['content'],
            n_results=1,
            search_string=url
        )

        if self.assistant.last_message()["content"] == "TERMINATE":
            return True, "没有找到相关信息。"
        else:
            return True, self.assistant.last_message()["content"]
