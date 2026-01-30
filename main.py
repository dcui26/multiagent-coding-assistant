import os
from dotenv import load_dotenv

# Load environment before importing nodes
load_dotenv()

from langgraph.graph import StateGraph, END
from agent.states import AgentState
from agent.nodes import (
    validate_scope,
    optimize_prompt_node,
    generate_spec,
    coder_node,
    debugger_node,
    finalizer_node
)

# --- 1. DEFINE ROUTING LOGIC ---

def route_bouncer(state: AgentState):
    """Decides if we proceed or stop based on Bouncer."""
    if state.get("in_scope"):
        # If user asked for a reset/new project, branch_decision might be set
        if state.get("branch_decision") == "architect":
            return "architect"
        return "optimizer"
    return END

def route_optimizer(state: AgentState):
    """Decides if we need a plan (Architect) or just code (Coder)."""
    decision = state.get("branch_decision", "architect")
    if decision == "dev_loop":
        return "coder"
    return "architect"

def route_debugger(state: AgentState):
    """Decides if we are done or need to fix bugs."""
    if state.get("dev_loop_complete"):
        return "finalizer"
    return "coder"  # Loop back to fix issues

# --- 2. BUILD THE GRAPH ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("bouncer", validate_scope)
workflow.add_node("optimizer", optimize_prompt_node)
workflow.add_node("architect", generate_spec)
workflow.add_node("coder", coder_node)
workflow.add_node("debugger", debugger_node)
workflow.add_node("finalizer", finalizer_node)

# Add Edges (The Flow)
workflow.set_entry_point("bouncer")

# Bouncer -> Optimizer (or Architect if reset) OR End
workflow.add_conditional_edges(
    "bouncer",
    route_bouncer,
    {
        "optimizer": "optimizer",
        "architect": "architect",
        END: END
    }
)

# Optimizer -> Architect OR Coder
workflow.add_conditional_edges(
    "optimizer",
    route_optimizer,
    {
        "architect": "architect",
        "coder": "coder"
    }
)

# Architect -> Coder (Always)
workflow.add_edge("architect", "coder")

# Coder -> Debugger (Always)
workflow.add_edge("coder", "debugger")

# Debugger -> Finalizer OR Coder (Loop)
workflow.add_conditional_edges(
    "debugger",
    route_debugger,
    {
        "finalizer": "finalizer",
        "coder": "coder"
    }
)

# Finalizer -> End
workflow.add_edge("finalizer", END)

# --- 3. COMPILE & RUN ---

app = workflow.compile()

if __name__ == "__main__":
    print("🤖 CODING AGENT INITIALIZED")
    
    # Simple loop to keep the agent running for multiple requests
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        initial_state = {
            "request": user_input,
            "dev_iterations": 0,
            "debug_history": [],
            "messages": []
        }
        
        # Run the graph
        for event in app.stream(initial_state):
            # stream() yields dictionaries with node names as keys
            for node_name, state_update in event.items():
                # We already print inside the nodes, so we can stay silent here
                # or print a separator
                pass