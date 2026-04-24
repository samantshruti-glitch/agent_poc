import gradio as gr
from agent import create_agent_graph
from langchain_core.messages import HumanMessage
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# ── Step definitions ────────────────────────────────────────────────────────

STEPS = [
    "Read JIRA Ticket",
    "Region ID Mapping",
    "Map Compilation",
    "Check EMR Status",
    "Update JIRA (EMR Details)",
    "Download Certificates",
    "Run Validations",
    "Update Confluence",
    "Check Approval Status",
    "Prod Publish",
    "Increment Version",
    "Update JIRA (Final)",
    "Send Email"
]

TOOL_TO_STEP = {
    "read_jira_ticket": 0,
    "trigger_region_id_mapping": 1,
    "trigger_map_compilation": 2,
    "check_emr_job_status": 3,
    "update_jira_ticket": 4,
    "download_map_certificates": 5,
    "run_validations": 6,
    "update_confluence_page": 7,
    "check_confluence_status": 8,
    "trigger_prod_publish_emr": 9,
    "run_increment_version_job": 10,
    "send_certificates_email": 12
}

# ── LangGraph state ─────────────────────────────────────────────────────────

graph_instance = None
init_error = ""

async def get_graph():
    global graph_instance, init_error
    if graph_instance is None and not init_error:
        try:
            graph_instance = await create_agent_graph()
        except Exception as e:
            init_error = str(e)
    return graph_instance

# ── Sidebar HTML ─────────────────────────────────────────────────────────────

def get_sidebar_html(step_status):
    html = "<div style='font-family: sans-serif;'>"
    for i, step in enumerate(STEPS):
        is_done = step_status[i] == "completed"
        is_rejected = step_status[i] == "rejected"
        if is_done:
            icon, color, bg = "✅", "#2ecc71", "rgba(46, 204, 113, 0.1)"
        elif is_rejected:
            icon, color, bg = "❌", "#e74c3c", "rgba(231, 76, 60, 0.1)"
        else:
            icon, color, bg = "⏳", "#95a5a6", "rgba(149, 165, 166, 0.05)"
        html += f"""
        <div style='padding: 10px; border-radius: 8px; margin-bottom: 8px;
                    background: {bg}; border-left: 4px solid {color};'>
            <span style='font-size: 1.1em;'>{icon}</span>
            <span style='margin-left: 8px; color: {color}; font-weight: 500;'>{i+1}. {step}</span>
        </div>"""
    html += "</div>"
    return html

# ── Message helpers (Gradio 6 format) ───────────────────────────────────────

def user_msg(content):
    return {"role": "user", "content": content}

def assistant_msg(content):
    return {"role": "assistant", "content": content}

# ── Core chat handler ────────────────────────────────────────────────────────

async def process_chat(message, history, step_status, thread_id):
    """Send a new message and stream results. Yields (history, step_status, thread_id, approve_row_vis, rejected_row_vis)."""
    # Ignore empty / whitespace-only submissions
    if not message or not message.strip():
        hint = assistant_msg(
            "💬 It looks like you didn't type anything.\n\n"
            "Here are some things you can do:\n"
            "- Type **'Start map release'** to begin the 13-step SOP.\n"
            "- Use the **✅ Approve / ❌ Reject** buttons when a step is waiting for your decision.\n"
            "- Click **🔄 Restart** in the sidebar to reset the process."
        )
        yield history + [hint], step_status, thread_id, gr.update(), gr.update()
        return

    graph = await get_graph()
    if not graph:
        yield (
            history + [user_msg(message), assistant_msg(f"❌ Initialisation error: {init_error}")],
            step_status, thread_id,
            gr.update(visible=False), gr.update(visible=False)
        )
        return

    config = {"configurable": {"thread_id": thread_id}}
    state  = await graph.aget_state(config)

    # If graph is paused (pending tool call), resume with None.
    # Never inject a HumanMessage here — it breaks the message chain.
    stream_input = None if state.next else {"messages": [HumanMessage(content=message)]}

    new_history = history + [user_msg(message), assistant_msg("")]
    output_text = ""

    try:
        async for event in graph.astream(stream_input, config=config):
            for key, value in event.items():
                if key == "agent":
                    msg = value["messages"][0]
                    content = msg.content if isinstance(msg.content, str) else ""
                    if msg.tool_calls:
                        content += "\n\n🛠️ **Preparing tool calls:**\n"
                        for tc in msg.tool_calls:
                            content += f"- `{tc['name']}`\n"
                    output_text += content

                elif key == "tools":
                    for tmsg in value["messages"]:
                        output_text += f"\n✅ **Tool `{tmsg.name}` executed.**"
                        idx = TOOL_TO_STEP.get(tmsg.name)
                        if idx is not None:
                            if tmsg.name == "update_jira_ticket" and step_status[4] == "completed":
                                idx = 11
                            step_status = list(step_status)
                            step_status[idx] = "completed"

            new_history[-1] = assistant_msg(output_text)
            yield new_history, step_status, thread_id, gr.update(visible=False), gr.update(visible=False)

    except Exception as e:
        output_text += f"\n\n❌ Error: {str(e)}"
        new_history[-1] = assistant_msg(output_text)
        yield new_history, step_status, thread_id, gr.update(visible=False), gr.update(visible=False)
        return

    # After streaming, decide which panel to show
    new_state = await graph.aget_state(config)
    if new_state.next:
        output_text += "\n\n⚠️ **Awaiting human approval before the next tool call.**"
        new_history[-1] = assistant_msg(output_text)
        yield new_history, step_status, thread_id, gr.update(visible=True), gr.update(visible=False)
    else:
        yield new_history, step_status, thread_id, gr.update(visible=False), gr.update(visible=False)

# ── Approval handlers ────────────────────────────────────────────────────────

async def handle_approve(history, step_status, thread_id):
    """User approved — resume the graph (execute the pending tool)."""
    async for result in process_chat("yes", history, step_status, thread_id):
        yield result


async def handle_reject(history, step_status, thread_id):
    """User rejected the step — mark it and show the 'rejected' options panel."""
    notice = assistant_msg(
        "❌ **Step rejected.** The tool will NOT be executed.\n\n"
        "Choose how to continue:\n"
        "- **Proceed Anyway** — override the rejection and execute the tool.\n"
        "- **Abort Process** — stop the entire release process."
    )
    new_history = history + [notice]
    # Hide approve row, show rejected row
    yield new_history, step_status, thread_id, gr.update(visible=False), gr.update(visible=True)


async def handle_proceed_anyway(history, step_status, thread_id):
    """User decided to proceed despite the rejection — resume the graph."""
    async for result in process_chat("yes", history, step_status, thread_id):
        yield result


async def handle_abort(history, step_status, thread_id):
    """User decided to abort — clear chat, reset sidebar, create fresh thread."""
    new_thread_id = str(uuid.uuid4())
    new_status    = ["pending"] * len(STEPS)
    fresh_history = [
        assistant_msg(
            "🛑 **Process aborted.**\n\n"
            "All progress has been cleared and the agent state has been reset.\n\n"
            "Type **'Start map release'** whenever you are ready to begin again."
        )
    ]
    return fresh_history, new_status, new_thread_id, gr.update(visible=False), gr.update(visible=False)

# ── Restart (from sidebar / menu) ────────────────────────────────────────────

async def handle_restart(history, step_status, thread_id):
    """Full restart — clear chat, reset sidebar, create fresh thread."""
    new_thread_id = str(uuid.uuid4())
    new_status    = ["pending"] * len(STEPS)
    fresh_history = [
        assistant_msg(
            "🔄 **Process restarted from the beginning.**\n\n"
            "All previous progress has been cleared.\n\n"
            "Type **'Start map release'** to begin the 13-step SOP."
        )
    ]
    return fresh_history, new_status, new_thread_id, gr.update(visible=False), gr.update(visible=False)

# ── Sidebar updater ───────────────────────────────────────────────────────────

def update_sidebar(status):
    return get_sidebar_html(status)

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
.gradio-container { max-width: 100% !important; font-family: 'Inter', sans-serif; }
#chatbot { border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
#approval_box {
    margin-top: 12px; padding: 16px; border-radius: 12px;
    background: rgba(52, 152, 219, 0.06);
    border: 1px solid rgba(52, 152, 219, 0.3);
}
#rejected_box {
    margin-top: 12px; padding: 16px; border-radius: 12px;
    background: rgba(231, 76, 60, 0.06);
    border: 1px solid rgba(231, 76, 60, 0.35);
}
"""

# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Map Release Agent") as demo:
    thread_id   = gr.State(str(uuid.uuid4()))
    step_status = gr.State(["pending"] * len(STEPS))

    gr.Markdown("# 🗺️ Map Release Process Automation")
    gr.Markdown("Agentic 13-step map release SOP powered by MCP & LangGraph with human-in-the-loop approvals.")

    with gr.Row():
        # ── Sidebar ──────────────────────────────────────────────────────────
        with gr.Column(scale=1, variant="panel"):
            gr.Markdown("## 📋 Progress")
            sidebar = gr.HTML(get_sidebar_html(["pending"] * len(STEPS)))
            with gr.Row():
                restart_sidebar_btn = gr.Button("🔄 Restart", variant="secondary", size="sm")

        # ── Chat panel ────────────────────────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=520, elem_id="chatbot", show_label=False)

            with gr.Row():
                msg    = gr.Textbox(placeholder="Type 'Start map release' to begin...", scale=4, show_label=False)
                submit = gr.Button("Send 🚀", variant="primary", scale=1)

            # ── Approval panel (shown while graph is interrupted) ─────────────
            with gr.Row(visible=False, elem_id="approval_box") as approval_row:
                with gr.Column():
                    gr.Markdown("### 🚦 Human Approval Required")
                    gr.Markdown("The agent wants to execute the tool shown above. Do you approve?")
                    with gr.Row():
                        approve_btn = gr.Button("✅ Approve", variant="primary")
                        reject_btn  = gr.Button("❌ Reject",  variant="stop")

            # ── Rejection follow-up panel ────────────────────────────────────
            with gr.Row(visible=False, elem_id="rejected_box") as rejected_row:
                with gr.Column():
                    gr.Markdown("### ⚠️ Step Was Rejected")
                    gr.Markdown("The tool has NOT been executed. How would you like to continue?")
                    with gr.Row():
                        proceed_anyway_btn = gr.Button("▶️ Proceed Anyway", variant="secondary")
                        abort_btn          = gr.Button("🛑 Abort Process",  variant="stop")

    # ── Shared outputs list ──────────────────────────────────────────────────
    outputs = [chatbot, step_status, thread_id, approval_row, rejected_row]

    def clear_msg():
        return ""

    # Chat submit
    msg.submit(process_chat, [msg, chatbot, step_status, thread_id], outputs).then(clear_msg, None, [msg])
    submit.click(process_chat, [msg, chatbot, step_status, thread_id], outputs).then(clear_msg, None, [msg])

    # Approval buttons
    approve_btn.click(handle_approve,        [chatbot, step_status, thread_id], outputs)
    reject_btn.click( handle_reject,         [chatbot, step_status, thread_id], outputs)

    # Post-rejection buttons
    proceed_anyway_btn.click(handle_proceed_anyway, [chatbot, step_status, thread_id], outputs)
    abort_btn.click(         handle_abort,           [chatbot, step_status, thread_id], outputs)

    # Restart from sidebar
    restart_sidebar_btn.click(handle_restart, [chatbot, step_status, thread_id], outputs)

    # Keep sidebar in sync
    step_status.change(update_sidebar, step_status, sidebar)


if __name__ == "__main__":
    demo.launch(css=CSS)
