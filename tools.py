from langchain_core.tools import tool
import time

@tool
def read_jira_ticket(ticket_id: str) -> dict:
    """Reads release information from a JIRA ticket."""
    time.sleep(1)
    return {
        "ticket_id": ticket_id,
        "release_version": "v1.2.3",
        "market_information": "North America",
        "map_compiler_version": "v4.5",
        "source_input_version": "v2023.10"
    }

@tool
def trigger_region_id_mapping(release_version: str, market_information: str) -> dict:
    """Triggers the region ID mapping pipeline via Swagger."""
    time.sleep(1)
    return {"status": "success", "pipeline_id": "pipe-8899"}

@tool
def trigger_map_compilation(release_version: str, compiler_version: str, source_version: str) -> dict:
    """Triggers the map compilation job via Swagger through GitLab pipeline."""
    time.sleep(1)
    return {"status": "triggered", "emr_job_id": "j-2XXYYZZ"}

@tool
def check_emr_job_status(emr_job_id: str) -> dict:
    """Logs into AWS and checks the EMR compilation job status."""
    time.sleep(2)
    return {"emr_job_id": emr_job_id, "status": "SUCCESS"}

@tool
def update_jira_ticket(ticket_id: str, message: str) -> str:
    """Updates the JIRA ticket with job details or status."""
    time.sleep(1)
    return f"Ticket {ticket_id} updated successfully with message: '{message}'"

@tool
def download_map_certificates(release_version: str) -> str:
    """Executes a script to download map certificates."""
    time.sleep(1)
    return f"Certificates downloaded successfully for {release_version}."

@tool
def run_validations(release_version: str) -> dict:
    """Executes script to run validations on the map release."""
    time.sleep(1)
    return {"status": "passed", "details": "All validations passed."}

@tool
def update_confluence_page(release_version: str, status: str) -> str:
    """Updates confluence release page with release status."""
    time.sleep(1)
    return f"Confluence page for {release_version} updated to: {status}"

@tool
def check_confluence_status(release_version: str) -> str:
    """Checks the Confluence page to see if the release is approved."""
    time.sleep(1)
    return "approved"

@tool
def trigger_prod_publish_emr(release_version: str) -> dict:
    """Triggers a prod publish EMR job."""
    time.sleep(1)
    return {"status": "triggered", "emr_job_id": "j-PROD123"}

@tool
def run_increment_version_job(current_version: str) -> str:
    """Runs increment version job."""
    time.sleep(1)
    return "v1.2.4"

@tool
def send_certificates_email(release_version: str) -> str:
    """Calls script to send downloaded certificates via email."""
    time.sleep(1)
    return "Email sent successfully to stakeholders."

# List of all tools for the agent to use
mock_tools = [
    read_jira_ticket,
    trigger_region_id_mapping,
    trigger_map_compilation,
    check_emr_job_status,
    update_jira_ticket,
    download_map_certificates,
    run_validations,
    update_confluence_page,
    check_confluence_status,
    trigger_prod_publish_emr,
    run_increment_version_job,
    send_certificates_email
]
