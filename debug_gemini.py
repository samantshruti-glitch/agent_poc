"""Intercept the exact messages being sent to Gemini on every agent call."""
import os
from dotenv import load_dotenv
load_dotenv()

# Patch ChatGoogleGenerativeAI._generate before importing agent
from langchain_google_genai import ChatGoogleGenerativeAI

original_generate = ChatGoogleGenerativeAI._generate

call_num = [0]

def patched_generate(self, messages, *args, **kwargs):
    call_num[0] += 1
    print(f"\n=== LLM CALL #{call_num[0]} ===")
    print(f"Number of messages: {len(messages)}")
    for i, m in enumerate(messages):
        content_repr = repr(str(m.content)[:100])
        tc = getattr(m, 'tool_calls', [])
        print(f"  [{i}] {type(m).__name__}: content={content_repr}, tool_calls={len(tc)}")
    try:
        return original_generate(self, messages, *args, **kwargs)
    except Exception as e:
        print(f"  !! FAILED on call #{call_num[0]}: {e}")
        raise

ChatGoogleGenerativeAI._generate = patched_generate

from agent import create_agent_graph
from langchain_core.messages import HumanMessage

graph = create_agent_graph()

print("Running graph...")
try:
    result = graph.invoke(
        {"messages": [HumanMessage(content="Start the map release process for ticket MAP-404")]},
    )
    print("\nDONE. Final message:", result["messages"][-1].content[:300])
except Exception as e:
    print("\nFinal ERROR:", e)
