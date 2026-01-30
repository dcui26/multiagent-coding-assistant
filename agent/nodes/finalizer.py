import json
import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from agent.states import AgentState
from agent.model import get_model
from agent.tools import load_mind_files, update_memory, list_files

def finalizer_node(state: AgentState):
    print("--- 📝 FINALIZER: Updating Memory ---")
    
    # 1. Load Data
    _, current_memory = load_mind_files() # We only need the dynamic memory part
    current_files = list_files()
    
    # Get the "Battle Scars" (History of what went wrong/right)
    # We summarize the debug history to extract lessons
    debug_history = state.get("debug_history", [])
    history_summary = "\n".join(
        [f"- {entry['role'].upper()}: {entry.get('result', '')}" 
         for entry in debug_history if 'result' in entry]
    )

    # 2. The Memory Update Prompt
    llm = get_model()
    
    system_prompt = f"""You are the Project Historian.
    Your job is to update the project's 'memory.json' based on the work just completed.
    
    OLD MEMORY:
    {json.dumps(current_memory, indent=2)}
    
    WORK DONE:
    - User Request: "{state['request']}"
    - Final File List: {current_files}
    - Debug History (Critiques & Fixes):
    {history_summary}
    
    INSTRUCTIONS:
    1. 'completed_tasks': Add the user request here.
    2. 'known_files': Update this list based on the Final File List. Remove deleted files.
    3. 'error_log': If the Debug History shows repeated errors, add a note here so we avoid them later.
    4. 'pending_tasks': If the Architect left a plan with multiple steps and we only did one, add the rest here.
    
    OUTPUT:
    Return ONLY the valid, updated JSON string.
    """
    
    user_prompt = "Please update the memory based on the completed work described above."
    
    # ⚠️ CRITICAL FIX: Added HumanMessage
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    # 3. Parse and Save
    try:
        # Clean the output (remove markdown fences if present)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        new_memory = json.loads(content)
        
        # Add timestamp metadata manually to ensure accuracy
        new_memory["last_updated"] = datetime.datetime.now().isoformat()
        
        # Write to disk
        update_memory(new_memory)
        print("   > Memory Saved to mind/memory.json")
        
        final_msg = f"Task Complete. Memory updated. (Files: {len(current_files)})"
        
    except json.JSONDecodeError as e:
        print(f"   > ❌ Error parsing memory update from LLM: {e}")
        final_msg = "Task Complete, but failed to update memory JSON."
        new_memory = {}

    # 4. Final Output
    return {
        "final_summary": final_msg,
        "memory_update": new_memory
    }