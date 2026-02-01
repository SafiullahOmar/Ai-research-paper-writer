// Generate a unique session ID
const sessionId = 'session_' + Math.random().toString(36).substring(2, 15);

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');

// Templates
const loadingTemplate = document.getElementById('loading-template');
const toolTemplate = document.getElementById('tool-template');
const pdfTemplate = document.getElementById('pdf-template');

// Configure marked for markdown rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false
});

// Remove welcome message when first message is sent
function removeWelcomeMessage() {
    const welcomeMsg = chatContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
}

// Add a message to the chat
function addMessage(role, content, additionalContent = null) {
    removeWelcomeMessage();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Render markdown for assistant messages
    if (role === 'assistant') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    // Add any additional content (like PDF download buttons)
    if (additionalContent) {
        contentDiv.appendChild(additionalContent);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
    
    return messageDiv;
}

// Add loading indicator
function addLoadingIndicator() {
    const loading = loadingTemplate.content.cloneNode(true);
    const loadingDiv = loading.querySelector('.message');
    loadingDiv.id = 'loading-indicator';
    chatContainer.appendChild(loading);
    scrollToBottom();
    return loadingDiv;
}

// Remove loading indicator
function removeLoadingIndicator() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        loading.remove();
    }
}

// Add tool call indicator
function addToolIndicator(toolName) {
    const toolIndicator = toolTemplate.content.cloneNode(true);
    toolIndicator.querySelector('.tool-name').textContent = `Calling ${toolName}...`;
    
    // Add to loading indicator if exists, otherwise to chat
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        const content = loading.querySelector('.message-content');
        content.insertBefore(toolIndicator, content.firstChild);
    }
    
    scrollToBottom();
}

// Create PDF download button
function createPdfDownloadButton(filename) {
    const pdfDiv = pdfTemplate.content.cloneNode(true);
    const downloadBtn = pdfDiv.querySelector('.download-btn');
    downloadBtn.href = `/download/${filename}`;
    downloadBtn.querySelector('.pdf-name').textContent = `Download ${filename}`;
    return pdfDiv;
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Disable/enable input
function setInputEnabled(enabled) {
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    
    if (enabled) {
        userInput.focus();
    }
}

// Send message using Server-Sent Events (streaming)
async function sendMessageStream(message) {
    removeWelcomeMessage();
    
    // Add user message
    addMessage('user', message);
    
    // Add loading indicator
    addLoadingIndicator();
    
    // Disable input while processing
    setInputEnabled(false);
    
    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let currentContent = '';
        let pdfFilename = null;
        let messageDiv = null;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        switch (data.type) {
                            case 'tool_call':
                                addToolIndicator(data.name);
                                break;
                                
                            case 'content':
                                currentContent = data.content;
                                
                                // Remove loading indicator and create/update message
                                removeLoadingIndicator();
                                
                                if (!messageDiv) {
                                    messageDiv = addMessage('assistant', currentContent);
                                } else {
                                    const contentDiv = messageDiv.querySelector('.message-content');
                                    contentDiv.innerHTML = marked.parse(currentContent);
                                }
                                break;
                                
                            case 'pdf':
                                pdfFilename = data.filename;
                                break;
                                
                            case 'error':
                                removeLoadingIndicator();
                                addMessage('assistant', `Error: ${data.message}`);
                                break;
                                
                            case 'done':
                                // Add PDF download button if available
                                if (pdfFilename && messageDiv) {
                                    const contentDiv = messageDiv.querySelector('.message-content');
                                    const pdfBtn = createPdfDownloadButton(pdfFilename);
                                    contentDiv.appendChild(pdfBtn);
                                }
                                break;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        removeLoadingIndicator();
        addMessage('assistant', `Sorry, an error occurred: ${error.message}`);
    } finally {
        setInputEnabled(true);
    }
}

// Send message (non-streaming fallback)
async function sendMessage(message) {
    removeWelcomeMessage();
    
    // Add user message
    addMessage('user', message);
    
    // Add loading indicator
    addLoadingIndicator();
    
    // Disable input while processing
    setInputEnabled(false);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoadingIndicator();
        
        if (data.error) {
            addMessage('assistant', `Error: ${data.error}`);
            return;
        }
        
        // Create PDF download button if available
        let pdfButton = null;
        if (data.pdf_available) {
            pdfButton = createPdfDownloadButton(data.pdf_filename);
        }
        
        // Add assistant response
        addMessage('assistant', data.response, pdfButton);
        
    } catch (error) {
        console.error('Error:', error);
        removeLoadingIndicator();
        addMessage('assistant', `Sorry, an error occurred: ${error.message}`);
    } finally {
        setInputEnabled(true);
    }
}

// Clear chat history
async function clearChat() {
    try {
        await fetch('/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        // Clear chat UI
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to Research AI Agent!</h2>
                <p>I can help you explore research topics, find papers on arXiv, analyze them, and even write new research papers with LaTeX.</p>
                <p>What research topic would you like to explore?</p>
            </div>
        `;
        
    } catch (error) {
        console.error('Error clearing chat:', error);
    }
}

// Event listeners
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    userInput.value = '';
    
    // Use streaming version
    sendMessageStream(message);
});

clearBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
        clearChat();
    }
});

// Focus input on page load
userInput.focus();