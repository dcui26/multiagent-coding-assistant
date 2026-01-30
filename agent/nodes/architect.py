from langchain_core.messages import SystemMessage, HumanMessage
from agent.states import AgentState
from agent.model import get_model
from agent.tools import list_files

def generate_spec(state: AgentState):
    print("--- 🏗️ ARCHITECT: Generating Technical Spec ---")
    
    # 1. Gather Context
    # We need to see the current file structure to plan correctly
    current_files = list_files()
    files_str = "\n".join(current_files) if current_files else "(No files yet)"
    
    # 2. Prepare the Brain
    llm = get_model()
    
    system_prompt = f"""You are a Software Architect.
    Your goal is to design a robust, step-by-step implementation plan for the user's request.
    
    CURRENT FILE STRUCTURE:
    {files_str}
    
    INSTRUCTIONS:
    1. Analyze the Context (Manifest/Memory) and User Request.
    2. Break the work down into atomic, logical steps.
    3. Specify exactly which files need to be created or modified.
    4. Consider dependencies (e.g., "Install package X before importing it").
    
    OUTPUT FORMAT:
    Return a clear Markdown-formatted plan.
    Example:
    ## Plan
    1. Create `src/utils.py` with helper functions.
    2. Modify `main.py` to import utils.
    3. Install `pandas`.
    """
    
    # 3. Call the Model
    # We pass the full context (manifest/memory) that the Optimizer loaded
    user_msg = f"User Request: {state['request']}\n\nProject Context:\n{state['context']}"
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg)
    ])
    
    # 4. Save to State
    # The Dev Loop will read this 'plan' to know what to do.
    return {
        "plan": response.content,
        "dev_iterations": 0,    # Reset loop counter
        "dev_loop_complete": False
    }