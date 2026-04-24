import os
import sys
import logging
import warnings

# Aggressively suppress technical warnings
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("langchain_mcp_adapters").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*additionalProperties.*")

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are a Map Release Automation Agent. Your job is to strictly follow this 12-step process to automate a map release. Execute EXACTLY ONE tool at a time, wait for its result, then proceed to the next step:

1. Read release information from a JIRA ticket (use read_jira_ticket).
2. Trigger the region ID mapping pipeline (use trigger_region_id_mapping).
3. Trigger the map compilation job (use trigger_map_compilation).
4. Check the EMR compilation job status until SUCCESS (use check_emr_job_status).
5. Update the same JIRA ticket with the EMR job details (use update_jira_ticket).
6. Execute the script to download map certificates (use download_map_certificates).
7. Execute the script to run validations (use run_validations).
8. Update the Confluence release page with the release status (use update_confluence_page).
9. Check if the Confluence page status is 'approved' (use check_confluence_status).
10. If approved, trigger a prod publish EMR job (use trigger_prod_publish_emr).
11. Run the increment version job (use run_increment_version_job).
12. Update the JIRA ticket with the final status (use update_jira_ticket).
13. Call the script to send downloaded certificates via email (use send_certificates_email).

IMPORTANT: Execute ONE tool at a time. Wait for each result before calling the next tool.
Report your progress to the user as you complete each step."""

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        return ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
    elif provider == "openai":
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif provider == "gemini":
        # Try models in order of likelihood to have quota/availability for this user
        # gemini-3-flash-preview is the most likely based on user context
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            max_retries=3
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

async def create_agent_graph():
    llm = get_llm()
    
    # Configure MCP client to connect to the local mock Atlassian MCP server
    mcp_servers = {
        "atlassian_mcp": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["mcp_server.py"],
        }
    }
    
    # Initialize the MultiServerMCPClient
    client = MultiServerMCPClient(mcp_servers)
    
    # Fetch tools from the connected MCP server dynamically
    tools = await client.get_tools()
    
    # Use a MemorySaver as a checkpointer to support interrupts and human-in-the-loop
    checkpointer = MemorySaver()
    
    # create_react_agent from langgraph.prebuilt handles message history
    # correctly for all providers including Gemini, ensuring AIMessages
    # with tool_calls are never stripped from the conversation history.
    # We add interrupt_before=["tools"] to pause before any tool execution.
    graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        interrupt_before=["tools"]
    )
    return graph
