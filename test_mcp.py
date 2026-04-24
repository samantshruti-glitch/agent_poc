import asyncio
from agent import create_agent_graph
from langchain_core.messages import HumanMessage

async def main():
    print("Initializing agent...")
    graph = await create_agent_graph()
    config = {"configurable": {"thread_id": "test-thread"}}
    
    print("\n--- Phase 1: Start Task ---")
    messages = [HumanMessage(content="Start the map release process for ticket MAP-404.")]
    
    # Run until interrupt
    async for event in graph.astream({"messages": messages}, config=config):
        print(f"Event: {list(event.keys())}")
        if "agent" in event:
            msg = event["agent"]["messages"][0]
            if msg.tool_calls:
                print(f"Agent wants to call tools: {[tc['name'] for tc in msg.tool_calls]}")

    state = await graph.aget_state(config)
    print(f"Next step: {state.next}")
    
    if state.next:
        print("\n--- Phase 2: Approve ---")
        # Resume with None
        async for event in graph.astream(None, config=config):
            print(f"Event: {list(event.keys())}")
            if "tools" in event:
                for msg in event["tools"]["messages"]:
                    print(f"Tool Result ({msg.name}): {msg.content[:50]}...")
            if "agent" in event:
                msg = event["agent"]["messages"][0]
                if msg.content:
                    print(f"Agent Response: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
