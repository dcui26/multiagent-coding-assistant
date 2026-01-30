import streamlit as st
from main import app  # Import your compiled graph

st.set_page_config(page_title="Autonomous Coding Agent", page_icon="🤖")

st.title("🤖 Autonomous Coding Agent")
st.markdown("Ask me to write code, debug files, or build a project.")

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
                "in_scope": True
            }
            
            # Stream the events from the graph
            final_state = None
            
            # We use .stream() to get updates as they happen
            for event in app.stream(initial_state):
                
                # --- 🛡️ BOUNCER ---
                if "bouncer" in event:
                    result = event["bouncer"]
                    if result["in_scope"]:
                        status_container.write("✅ Bouncer: Request is in scope.")
                    else:
                        # Rejection Logic
                        status_container.update(label="⛔ Request Rejected", state="error", expanded=True)
                        status_container.write(f"❌ {result.get('rejection_reason', 'Unknown reason')}")
                        final_state = result
                        break  # <--- STOP THE SPINNER IMMEDIATELY

                # --- 📐 ARCHITECT ---
                if "architect" in event:
                    status_container.write("📐 Architect: Plan created.")
                    
                    # RESTORED: Show the plan in an expander
                    plan = event["architect"].get("plan", "No plan generated.")
                    with status_container:
                        with st.expander("📝 View Architect's Plan", expanded=False):
                            st.markdown(plan)
                
                # --- 💻 CODER ---
                if "coder" in event:
                    status_container.write("💻 Coder: Code written.")
                
                # --- 🕵️ DEBUGGER ---
                if "debugger" in event:
                    result = event["debugger"]
                    feedback = result.get("debug_feedback")
                    
                    if feedback:
                        # RESTORED: Show the error/feedback in an expander
                        status_container.write("🕵️ Debugger: Issues found. Sending back to Coder.")
                        with status_container:
                            with st.expander("🐛 View Debugger Feedback", expanded=False):
                                st.markdown(f"**Feedback:**\n\n{feedback}")
                    else:
                        status_container.write("🕵️ Debugger: Code looks good!")

            # 3. Final Response Handling
            if final_state and not final_state.get("in_scope", True):
                # If rejected, show the rejection clearly outside the status
                response = f"Sorry, I can't help with that. Reason: {final_state.get('rejection_reason')}"
                st.error(response)
            else:
                # If finished successfully, close the status
                status_container.update(label="✅ Task Complete", state="complete", expanded=False)
                response = "I have finished the task. Check your `workspace/` folder!"
                st.success(response)

            # Add Assistant Message to History
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            status_container.update(label="💥 Error Occurred", state="error")
            st.error(f"An error occurred: {e}")