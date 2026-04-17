import gradio as gr
from agent import create_agent_graph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import json
import os
from dotenv import load_dotenv

load_dotenv()

# We need an API key to actually run the compiled graph. For POC purposes, we can 
# check if API key exists.
missing_key = False
provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
    missing_key = True
elif provider == "openai" and not os.getenv("OPENAI_API_KEY"):
    missing_key = True
elif provider == "gemini" and not os.getenv("GOOGLE_API_KEY"):
    missing_key = True

try:
    graph = create_agent_graph()
except Exception as e:
    graph = None
    init_error = str(e)

def process_chat(message, history):
    if missing_key:
        yield "Error: API Key is missing in .env file. Please add it and restart the app."
        return
        
    if not graph:
        yield f"Error initializing agent: {init_error}"
        return

    # Convert Gradio history to Langchain Messages
    # Safely coerce content to str in case Gradio passes lists (multimodal)
    lc_messages = []
    for turn in history:
        user_msg = turn[0] if isinstance(turn, (list, tuple)) else turn.get("role", "")
        ai_msg = turn[1] if isinstance(turn, (list, tuple)) else turn.get("content", "")
        lc_messages.append(HumanMessage(content=str(user_msg) if user_msg else ""))
        lc_messages.append(AIMessage(content=str(ai_msg) if ai_msg else ""))

    lc_messages.append(HumanMessage(content=message))
    
    # Stream output from LangGraph (create_react_agent uses 'agent' and 'tools' node keys)
    output_text = ""
    try:
        for event in graph.stream({"messages": lc_messages}):
            for key, value in event.items():
                if key == "agent":
                    msg = value["messages"][0]
                    # Safely convert content to string
                    content = ""
                    if isinstance(msg.content, list):
                        content = " ".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in msg.content
                        )
                    elif msg.content:
                        content = str(msg.content)
                    if content.strip():
                        output_text += content + "\n\n"
                    if msg.tool_calls:
                        output_text += "🛠️ **Tool Calls:**\n"
                        for tc in msg.tool_calls:
                            output_text += f"- `{tc['name']}` with args: `{json.dumps(tc['args'])}`\n"
                        output_text += "\n"
                elif key == "tools":
                    output_text += "✅ **Tool Results:**\n"
                    for msg in value["messages"]:
                        content = str(msg.content)
                        if len(content) > 200:
                            content = content[:200] + "..."
                        output_text += f"- `{msg.name}`: `{content}`\n"
                    output_text += "\n---\n"
            yield output_text
    except Exception as e:
        yield output_text + f"\n\nError during execution: {str(e)}"

# Gradio Interface
with gr.Blocks(title="Map Release Process Agent POC") as demo:
    gr.Markdown("# 🗺️ Map Release Process Automation Agent")
    gr.Markdown("This agent uses LangGraph and an LLM to follow a strict 12-step SOP to automate the map release process using mock tools.")
    
    if missing_key:
        gr.Markdown(f"### ⚠️ Missing API Key\nPlease add your API key for **{provider}** to the `.env` file before running.")
    
    chatbot = gr.ChatInterface(
        fn=process_chat,
        description="Type something like: 'Start the map release process for ticket MAP-404'. The agent will guide you through the process.",
        examples=["Start the map release process for ticket MAP-404", "What steps have you completed?"]
    )

if __name__ == "__main__":
    demo.launch()
