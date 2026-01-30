import json
from langchain_core.messages import SystemMessage, HumanMessage
from agent.states import AgentState
from agent.model import get_model
from agent.tools import load_mind_files

def optimize_prompt_node(state: AgentState):
    """
    1. Loads project context (Mind).
    2. Analyzes user request.
    3. Decides: Do we need a new plan (Architect) or just code (Dev Loop)?
    """
    print("--- 🧠 OPTIMIZING PROMPT & LOADING CONTEXT ---")
    
    # 1. Load the "Mind" (Manifest + Memory)
    manifest, memory = load_mind_files()
    
    # Convert JSONs to string for the LLM to read
    context_str = f"""
    PROJECT MANIFEST (Rules & Stack):
    {json.dumps(manifest, indent=2)}

    PROJECT MEMORY (Current State):
    {json.dumps(memory, indent=2)}
    """
    
    # 2. Ask the LLM to route the request
    llm = get_model()
    
    system_prompt = """You are a Project Manager for a software project.
    Your job is to route the user's request based on the current project state.
    
    OPTIONS:
    1. "architect" -> If the user asks for a NEW feature, a structural change, or if the project is brand new/empty.
    2. "dev_loop" -> If the user asks to fix a bug, continue an existing task, or small code tweaks.
    
    OUTPUT FORMAT:
    Return ONLY the raw string "architect" or "dev_loop". Do not add punctuation.
    """
    
    user_message = f"User Request: {state['request']}\n\nCurrent Context:\n{context_str}"
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])
    
    decision = response.content.strip().lower()
    
    # Fallback safety
    if decision not in ["architect", "dev_loop"]:
        decision = "architect" # Default to planning if unsure

    print(f"Decision: {decision.upper()}")

    # 3. Return updated state
    return {
        "branch_decision": decision,
        "context": context_str, # Pass the full context forward
        # Initialize dev loop counters here so they are ready if needed
        "dev_iterations": 0,
        "dev_loop_complete": False
    }