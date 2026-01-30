import ast
from langchain_core.messages import SystemMessage, HumanMessage  # <--- IMPORT HUMANMESSAGE
from agent.states import AgentState
from agent.model import get_model
from agent.tools import list_files, read_file, run_command

def debugger_node(state: AgentState):
    print("--- 🕵️ DEBUGGER: Testing Code ---")
    current_files = list_files()
    
    # 1. PRE-CHECK: Syntax (Fast Fail)
    syntax_errors = []
    for file in current_files:
        if file.endswith(".py"):
            try:
                content = read_file(file)
                ast.parse(content)
            except SyntaxError as e:
                syntax_errors.append(f"{file}: {str(e)}")

    if syntax_errors:
        error_msg = "Syntax Errors Found (Auto-Reject):\n" + "\n".join(syntax_errors)
        print(f"   > ❌ {error_msg}")
        return {
            "dev_loop_complete": False,
            "debug_feedback": error_msg,
            "debug_history": state.get("debug_history", []) + [{"role": "debugger", "status": "syntax_error"}]
        }

    # 2. RUN TESTS (The Simulation)
    test_files = [f for f in current_files if "test" in f.lower() or "t_" in f.lower()]
    execution_logs = ""
    
    if test_files:
        print(f"   > Found tests: {test_files}")
        for tf in test_files:
            print(f"   > Running {tf}...")
            # Run the test file using the tool
            result = run_command(f"python {tf}")
            execution_logs += f"\n--- EXECUTION OF {tf} ---\n{result}\n"
    else:
        execution_logs = "No test files found. Code was not executed."

    # 3. ANALYZE RESULTS (LLM)
    llm = get_model()
    
    code_dump = ""
    for file in current_files:
        code_dump += f"\n--- {file} ---\n{read_file(file)}\n"
        
    # --- SPLIT PROMPT TO FIX 400 ERROR ---
    system_message = """You are the QA Debugger.
    INSTRUCTIONS:
    1. Look at the EXECUTION RESULTS. Did the tests pass (Exit code 0)?
    2. If tests failed, tell the Coder EXACTLY what the error message was.
    3. If no tests exist, fail the code and tell the Coder to write a test file.
    4. If tests passed and code looks good, output <APPROVED />.
    """
    
    user_message = f"""
    ARCHITECT'S PLAN: {state.get('plan')}
    
    CODE:
    {code_dump}
    
    EXECUTION RESULTS (REAL WORLD TEST):
    {execution_logs}
    """
    
    response = llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content=user_message)
    ])
    content = response.content
    
    # 4. DECISION LOGIC
    if "<APPROVED />" in content:
        print("   > ✅ Code Approved")
        return {
            "dev_loop_complete": True, 
            "debug_feedback": None,
            "debug_history": state.get("debug_history", []) + [{"role": "debugger", "status": "approved"}]
        }
    else:
        print("   > ⚠️ Test Failed or Issues Found")
        return {
            "dev_loop_complete": False, 
            "debug_feedback": content,
            "debug_history": state.get("debug_history", []) + [{"role": "debugger", "status": "rejected"}]
        }