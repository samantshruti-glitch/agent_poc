from fastmcp import FastMCP
import asyncio
import logging

# Suppress schema warnings in the console
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("fastmcp").setLevel(logging.ERROR)

mcp = FastMCP("MapReleaseServer")

@mcp.tool()
async def read_jira_ticket(ticket_id: str) -> dict:
    """Reads release information from a JIRA ticket."""
    await asyncio.sleep(1)
    return {
        "ticket_id": ticket_id,
        "release_version": "v1.2.3",
        "market_information": "North America",
        "map_compiler_version": "v4.5",
        "source_input_version": "v2023.10"
    }

@mcp.tool()
async def trigger_region_id_mapping(release_version: str, market_information: str) -> dict:
    """Triggers the region ID mapping pipeline via Swagger."""
    await asyncio.sleep(1)
    return {"status": "success", "pipeline_id": "pipe-8899"}

@mcp.tool()
async def trigger_map_compilation(release_version: str, compiler_version: str, source_version: str) -> dict:
    """Triggers the map compilation job via Swagger through GitLab pipeline."""
    await asyncio.sleep(1)
    return {"status": "triggered", "emr_job_id": "j-2XXYYZZ"}

@mcp.tool()
async def check_emr_job_status(emr_job_id: str) -> dict:
    """Logs into AWS and checks the EMR compilation job status."""
    await asyncio.sleep(2)
    return {"emr_job_id": emr_job_id, "status": "SUCCESS"}

@mcp.tool()
async def update_jira_ticket(ticket_id: str, message: str) -> str:
    """Updates the JIRA ticket with job details or status."""
    await asyncio.sleep(1)
    return f"Ticket {ticket_id} updated successfully with message: '{message}'"

@mcp.tool()
async def download_map_certificates(release_version: str) -> str:
    """Executes a script to download map certificates."""
    await asyncio.sleep(1)
    return f"Certificates downloaded successfully for {release_version}."

@mcp.tool()
async def run_validations(release_version: str) -> dict:
    """Executes script to run validations on the map release."""
    await asyncio.sleep(1)
    return {"status": "passed", "details": "All validations passed."}

@mcp.tool()
async def update_confluence_page(release_version: str, status: str) -> str:
    """Updates confluence release page with release status."""
    await asyncio.sleep(1)
    return f"Confluence page for {release_version} updated to: {status}"

@mcp.tool()
async def check_confluence_status(release_version: str) -> str:
    """Checks the Confluence page to see if the release is approved."""
    await asyncio.sleep(1)
    return "approved"

@mcp.tool()
async def trigger_prod_publish_emr(release_version: str) -> dict:
    """Triggers a prod publish EMR job."""
    await asyncio.sleep(1)
    return {"status": "triggered", "emr_job_id": "j-PROD123"}

@mcp.tool()
async def run_increment_version_job(current_version: str) -> str:
    """Runs increment version job."""
    await asyncio.sleep(1)
    return "v1.2.4"

@mcp.tool()
async def send_certificates_email(release_version: str) -> str:
    """Calls script to send downloaded certificates via email."""
    await asyncio.sleep(1)
    return "Email sent successfully to stakeholders."

if __name__ == "__main__":
    mcp.run(show_banner=False)
