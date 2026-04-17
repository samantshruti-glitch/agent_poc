from agent import get_llm
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
llm = get_llm()
from tools import mock_tools
llm_with_tools = llm.bind_tools(mock_tools)

msgs = [
    HumanMessage(content='Start'),
    AIMessage(content='', tool_calls=[{'name': 'test', 'args': {}, 'id': 'call_1'}]),
    ToolMessage(content='result', tool_call_id='call_1')
]
print('Trying AIMessage with empty content')
try:
    llm_with_tools.invoke(msgs)
    print('Success')
except Exception as e:
    print(e)

msgs = [
    HumanMessage(content='Start'),
    AIMessage(content=' ', tool_calls=[{'name': 'test', 'args': {}, 'id': 'call_1'}]),
    ToolMessage(content='result', tool_call_id='call_1')
]
print('Trying AIMessage with space content')
try:
    llm_with_tools.invoke(msgs)
    print('Success')
except Exception as e:
    print(e)
