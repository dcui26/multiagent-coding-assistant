from typing import TypedDict, Annotated, Optional
from langgraph.graph import add_messages

class AgentState(TypedDict):
    # User Input
    request: str
    
    # Bouncer outputs
    in_scope: bool
    rejection_reason: Optional[str]
    
    # Prompt Optimizer outputs
    branch_decision: str  # "architect" | "dev_loop"
    context: str  # FULL manifest + memory injected here
    
    # Architect outputs
    plan: Optional[str]  # <--- CHANGED FROM technical_spec TO plan
    
    # Dev Loop outputs
    dev_loop_complete: bool
    dev_iterations: int
    debug_feedback: Optional[str]
    debug_history: list[dict]
    
    # Finalizer outputs
    memory_update: dict 
    final_summary: str
    
    # Metadata
    messages: Annotated[list, add_messages]