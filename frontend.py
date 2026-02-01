import streamlit as st
from ai_researcher import INITIAL_PROMPT, graph, config
from pathlib import Path
import logging
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic app config
st.set_page_config(page_title="Research AI Agent", page_icon="📄")
st.title("📄 Research AI Agent")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    logger.info("Initialized chat history")

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

# Display existing chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat interface
user_input = st.chat_input("What research topic would you like to explore?")

if user_input:
    # Log and display user input
    logger.info(f"User input: {user_input}")
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Prepare input for the agent
    chat_input = {
        "messages": [
            {"role": "system", "content": INITIAL_PROMPT}
        ] + st.session_state.chat_history
    }
    logger.info("Starting agent processing...")

    # Stream agent response
    full_response = ""
    response_placeholder = st.chat_message("assistant").empty()
    
    try:
        # Use stream_mode="updates" to get node updates
        for chunk in graph.stream(chat_input, config, stream_mode="updates"):
            logger.info(f"Received chunk with keys: {chunk.keys()}")
            
            # Check for agent node updates
            if "agent" in chunk:
                agent_output = chunk["agent"]
                if "messages" in agent_output:
                    messages = agent_output["messages"]
                    for message in messages:
                        # Handle tool calls (log only)
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tool_call in message.tool_calls:
                                logger.info(f"Tool call: {tool_call['name']}")
                                response_placeholder.info(f"🔧 Calling tool: {tool_call['name']}...")
                        
                        # Handle assistant response
                        if isinstance(message, AIMessage) and message.content:
                            if isinstance(message.content, str):
                                text_content = message.content
                            elif isinstance(message.content, list):
                                # Handle case where content is a list of content blocks
                                text_content = "".join(
                                    block.get("text", "") if isinstance(block, dict) else str(block)
                                    for block in message.content
                                )
                            else:
                                text_content = str(message.content)
                            
                            if text_content.strip():
                                full_response = text_content
                                response_placeholder.markdown(full_response)
            
            # Check for tools node updates (optional logging)
            if "tools" in chunk:
                logger.info("Tool execution completed")

    except Exception as e:
        logger.error(f"Error during agent processing: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

    # Add final response to history
    if full_response:
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
    else:
        st.warning("No response generated. Please try again.")
