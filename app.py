from flask import Flask, render_template, request, jsonify, send_file, Response
from ai_researcher import INITIAL_PROMPT, graph, config
from pathlib import Path
import logging
import json
import os
from langchain_core.messages import AIMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store chat history in memory (for production, use a database or session)
chat_sessions = {}

def get_chat_history(session_id):
    """Get or create chat history for a session."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI response."""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        logger.info(f"User input: {user_message}")
        
        # Get chat history for this session
        chat_history = get_chat_history(session_id)
        chat_history.append({"role": "user", "content": user_message})
        
        # Prepare input for the agent
        chat_input = {
            "messages": [
                {"role": "system", "content": INITIAL_PROMPT}
            ] + chat_history
        }
        
        logger.info("Starting agent processing...")
        
        # Process with the agent
        full_response = ""
        tool_calls_made = []
        pdf_path = None
        
        for chunk in graph.stream(chat_input, config, stream_mode="updates"):
            logger.info(f"Received chunk with keys: {chunk.keys()}")
            
            # Check for agent node updates
            if "agent" in chunk:
                agent_output = chunk["agent"]
                if "messages" in agent_output:
                    messages = agent_output["messages"]
                    for message in messages:
                        # Handle tool calls
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tool_call in message.tool_calls:
                                logger.info(f"Tool call: {tool_call['name']}")
                                tool_calls_made.append(tool_call['name'])
                        
                        # Handle assistant response
                        if isinstance(message, AIMessage) and message.content:
                            if isinstance(message.content, str):
                                text_content = message.content
                            elif isinstance(message.content, list):
                                text_content = "".join(
                                    block.get("text", "") if isinstance(block, dict) else str(block)
                                    for block in message.content
                                )
                            else:
                                text_content = str(message.content)
                            
                            if text_content.strip():
                                full_response = text_content
            
            # Check for tools node updates
            if "tools" in chunk:
                tools_output = chunk["tools"]
                if "messages" in tools_output:
                    for msg in tools_output["messages"]:
                        # Check if a PDF was generated
                        if hasattr(msg, "content") and msg.content:
                            content = msg.content
                            if isinstance(content, str) and content.endswith('.pdf'):
                                pdf_path = content
                                logger.info(f"PDF generated: {pdf_path}")
        
        # Add response to history
        if full_response:
            chat_history.append({"role": "assistant", "content": full_response})
        
        response_data = {
            'response': full_response,
            'tool_calls': tool_calls_made,
        }
        
        # If a PDF was generated, include the download path
        if pdf_path and os.path.exists(pdf_path):
            response_data['pdf_available'] = True
            response_data['pdf_filename'] = os.path.basename(pdf_path)
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error during agent processing: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Handle chat messages with streaming response."""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        logger.info(f"User input: {user_message}")
        
        # Get chat history for this session
        chat_history = get_chat_history(session_id)
        chat_history.append({"role": "user", "content": user_message})
        
        # Prepare input for the agent
        chat_input = {
            "messages": [
                {"role": "system", "content": INITIAL_PROMPT}
            ] + chat_history
        }
        
        def generate():
            full_response = ""
            pdf_path = None
            
            try:
                for chunk in graph.stream(chat_input, config, stream_mode="updates"):
                    # Check for agent node updates
                    if "agent" in chunk:
                        agent_output = chunk["agent"]
                        if "messages" in agent_output:
                            messages = agent_output["messages"]
                            for message in messages:
                                # Handle tool calls
                                if hasattr(message, "tool_calls") and message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_call['name']})}\n\n"
                                
                                # Handle assistant response
                                if isinstance(message, AIMessage) and message.content:
                                    if isinstance(message.content, str):
                                        text_content = message.content
                                    elif isinstance(message.content, list):
                                        text_content = "".join(
                                            block.get("text", "") if isinstance(block, dict) else str(block)
                                            for block in message.content
                                        )
                                    else:
                                        text_content = str(message.content)
                                    
                                    if text_content.strip():
                                        full_response = text_content
                                        yield f"data: {json.dumps({'type': 'content', 'content': text_content})}\n\n"
                    
                    # Check for tools node updates
                    if "tools" in chunk:
                        tools_output = chunk["tools"]
                        if "messages" in tools_output:
                            for msg in tools_output["messages"]:
                                if hasattr(msg, "content") and msg.content:
                                    content = msg.content
                                    if isinstance(content, str) and content.endswith('.pdf'):
                                        pdf_path = content
                                        yield f"data: {json.dumps({'type': 'pdf', 'filename': os.path.basename(pdf_path)})}\n\n"
                
                # Add response to history
                if full_response:
                    chat_history.append({"role": "assistant", "content": full_response})
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f"Error during streaming: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"Error during agent processing: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_pdf(filename):
    """Download a generated PDF file."""
    try:
        # Look for the PDF in the output directory
        pdf_path = Path("output") / filename
        
        if not pdf_path.exists():
            # Try absolute path
            pdf_path = Path(filename)
        
        if not pdf_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"Downloading PDF: {pdf_path}")
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history for a session."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in chat_sessions:
            chat_sessions[session_id] = []
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    Path("output").mkdir(exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8000)