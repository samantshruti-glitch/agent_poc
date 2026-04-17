import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from tools import mock_tools

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
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Higher free-tier quota than gemini-2.5-flash-lite
            temperature=0,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

def create_agent_graph():
    llm = get_llm()
    # create_react_agent from langgraph.prebuilt handles message history
    # correctly for all providers including Gemini, ensuring AIMessages
    # with tool_calls are never stripped from the conversation history.
    graph = create_react_agent(
        model=llm,
        tools=mock_tools,
        prompt=SYSTEM_PROMPT,
    )
    return graph
