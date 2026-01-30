import streamlit as st
from main import app  # Import your compiled graph
from pathlib import Path

st.set_page_config(page_title="Autonomous Coding Agent", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous Coding Agent")
st.markdown("Ask me to write code, debug files, or build a project.")

# Add a subtle divider
st.divider()

# --- SIDEBAR: Workspace File Viewer ---
with st.sidebar:
    st.header("📁 Workspace Files")
    
    workspace_path = Path("workspace")
    if workspace_path.exists():
        files = list(workspace_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        if files:
            st.caption(f"Found {len(files)} file(s)")
            
            for file in sorted(files):
                relative_path = file.relative_to(workspace_path)
                
                # Create a collapsible expander for each file
                with st.expander(f"📄 {relative_path}"):
                    try:
                        # Try to read as text
                        content = file.read_text(encoding='utf-8')
                        st.code(content, language='python' if file.suffix == '.py' else None)
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download",
                            data=content,
                            file_name=file.name,
                            mime='text/plain'
                        )
                    except Exception as e:
                        st.error(f"Could not read file: {e}")
        else:
            st.info("No files yet. Start by asking the agent to build something!")
    else:
        st.info("Workspace folder doesn't exist yet.")
    
    # Refresh button
    if st.button("🔄 Refresh Files"):
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("What should I build?"):
    # 1. Add User Message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Run the Agent
    with st.chat_message("assistant"):
        # The Status Container (Collapsible "Agent is thinking..." box)
        status_container = st.status("🤔 Agent is working...", expanded=True)
        
        try:
            # Prepare the initial state
            initial_state = {
                "request": prompt, 
                "dev_iterations": 0, 
                "debug_history": [],
                "messages": []
            }
            
            # Stream the events from the graph
            final_state = None
            response = None  # Initialize response variable
            
            # We use .stream() to get updates as they happen
            for event in app.stream(initial_state):
                
                # --- 🛡️ BOUNCER ---
                if "bouncer" in event:
                    result = event["bouncer"]
                    if result.get("in_scope"):
                        status_container.write("✅ Bouncer: Request is in scope.")
                    else:
                        # Rejection Logic
                        status_container.update(label="⛔ Request Rejected", state="error", expanded=True)
                        status_container.write(f"❌ {result.get('rejection_reason', 'Unknown reason')}")
                        final_state = result
                        break  # <--- STOP THE SPINNER IMMEDIATELY
                
                # --- 🧠 OPTIMIZER ---
                if "optimizer" in event:
                    result = event["optimizer"]
                    decision = result.get("branch_decision", "unknown")
                    status_container.write(f"🧠 Optimizer: Routing to {'Architect (new feature)' if decision == 'architect' else 'Coder (quick fix)'}.")

                # --- 📐 ARCHITECT ---
                if "architect" in event:
                    status_container.write("📐 Architect: Plan created.")
                    
                    # Show the plan in an expander
                    plan = event["architect"].get("plan", "No plan generated.")
                    with status_container:
                        with st.expander("📝 View Architect's Plan", expanded=False):
                            st.markdown(plan)
                
                # --- 💻 CODER ---
                if "coder" in event:
                    result = event["coder"]
                    iteration = result.get("dev_iterations", 0)
                    status_container.write(f"💻 Coder: Code written (iteration {iteration}).")
                
                # --- 🕵️ DEBUGGER ---
                if "debugger" in event:
                    result = event["debugger"]
                    feedback = result.get("debug_feedback")
                    
                    if feedback:
                        # Show the error/feedback in an expander
                        status_container.write("🕵️ Debugger: Issues found. Sending back to Coder.")
                        with status_container:
                            with st.expander("🐛 View Debugger Feedback", expanded=False):
                                st.markdown(f"**Feedback:**\n\n{feedback}")
                    else:
                        status_container.write("🕵️ Debugger: Code looks good!")
                
                # --- 📝 FINALIZER ---
                if "finalizer" in event:
                    status_container.write("📝 Finalizer: Updating project memory...")

            # 3. Final Response Handling
            if final_state and not final_state.get("in_scope", True):
                # If rejected, show the rejection clearly outside the status
                response = f"Sorry, I can't help with that. Reason: {final_state.get('rejection_reason')}"
                status_container.update(label="⛔ Request Rejected", state="error", expanded=False)
                st.error(response)
            else:
                # If finished successfully, close the status
                status_container.update(label="✅ Task Complete", state="complete", expanded=False)
                response = "✅ Task complete! Check the sidebar (📁 Workspace Files) to view and download your files."
                st.success(response)
                
                # Auto-refresh sidebar after completion
                st.rerun()

            # Add Assistant Message to History
            if response:  # Only add if response was set
                st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            status_container.update(label="💥 Error Occurred", state="error", expanded=False)
            error_msg = f"An error occurred: {str(e)}"
            st.error(error_msg)
            # Add error to history so user can see what went wrong
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
