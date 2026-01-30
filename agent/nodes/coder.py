import re
from langchain_core.messages import SystemMessage, HumanMessage  # <--- IMPORT HUMANMESSAGE
from agent.states import AgentState
from agent.model import get_model
from agent.tools import list_files, write_file

def coder_node(state: AgentState):
    print("--- 🧑‍💻 CODER: Writing Code ---")
    
    # 1. Gather Context
    current_files = list_files()
    files_str = "\n".join(current_files) if current_files else "(No files yet)"
    
    # 2. Determine Mode: "New Feature" vs "Bug Fix"
    feedback = state.get("debug_feedback", None)
    
    if feedback:
        print(f"   > Mode: FIXING (Feedback: {feedback[:50]}...)")
        instruction = f"""
        CRITICAL: The previous code had issues. 
        DEBUGGER FEEDBACK: {feedback}
        
        Fix the code based on this feedback.
        """
    else:
        print(f"   > Mode: IMPLEMENTING (Architect's Plan)")
        instruction = f"""
        Execute the next step in the Architect's Plan:
        {state.get('plan')}
        """

    # 3. Call the Model
    llm = get_model()
    
    # --- SPLIT PROMPT TO FIX 400 ERROR ---
    # Part A: Identity & Format (System)
    system_message = """You are the Coder. 
    Your job is to write code AND write tests to prove it works.
    
    IMPORTANT:
    1. Always write the main logic (e.g. calculator.py).
    2. Always write a test script (e.g. test_calculator.py) using 'unittest' or basic assertions.
    3. The Debugger will run this test script to verify your work.
    
    OUTPUT FORMAT:
    <write_file path="filename.py">
    ... code here ...
    </write_file>
    """
    
    # Part B: Context & Task (User)
    user_message = f"""
    CURRENT FILES:
    {files_str}
    
    INSTRUCTIONS:
    {instruction}
    """
    
    # Invoke with BOTH messages
    response = llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content=user_message)
    ])
    content = response.content
    
    # 4. Execute Writes
    matches = re.findall(r'<write_file path=["\'](.*?)["\']>\s*\n?(.*?)\n?\s*</write_file>', content, re.DOTALL)
    
    touched_files = []
    if matches:
        for path, code in matches:
            clean_code = code.strip()
            write_file(path, clean_code)
            touched_files.append(path)
            print(f"   > Wrote {path}")
    else:
        print("   > ⚠️ No file tags found in output.")

    # 5. Pass baton to Debugger
    return {
        "dev_iterations": state.get("dev_iterations", 0) + 1,
        "debug_history": state.get("debug_history", []) + [{"role": "coder", "touched": touched_files}]
    }