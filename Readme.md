# 📄 AI Research Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Latest-purple.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent AI-powered research assistant that searches academic papers, analyzes them, and generates new research papers with LaTeX/PDF output.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Deployment](#-deployment) • [API Reference](#-api-reference)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Paper Search** | Search arXiv for the latest academic papers across physics, math, CS, and more |
| 📖 **PDF Analysis** | Extract and analyze content from research papers automatically |
| ✍️ **Paper Writing** | Generate new research papers based on analyzed content |
| 📄 **PDF Generation** | Automatically compile LaTeX documents to downloadable PDFs |
| 💬 **Chat Interface** | Modern, responsive web interface with real-time streaming |
| 🔄 **Live Updates** | See AI responses and tool calls in real-time via Server-Sent Events |
| 📥 **Easy Downloads** | One-click PDF downloads directly in your browser |

---

## 🖥️ Demo

```
┌─────────────────────────────────────────────────────────────────┐
│  📄 Research AI Agent                                 [Clear]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Welcome to Research AI Agent!                                  │
│  I can help you explore research topics, find papers on arXiv,  │
│  analyze them, and write new research papers with LaTeX.        │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  👤 Search for papers on transformer architectures              │
│                                                                 │
│  🤖 🔧 Calling tool: arxiv_search...                            │
│                                                                 │
│     I found 5 recent papers on transformer architectures:       │
│                                                                 │
│     1. **Attention Is All You Need** - Vaswani et al.          │
│        Summary: The dominant sequence transduction models...    │
│        📎 PDF: https://arxiv.org/pdf/1706.03762.pdf            │
│                                                                 │
│     2. **BERT: Pre-training of Deep Bidirectional...**         │
│        ...                                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [What research topic would you like to explore?          ] [➤] │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11+** installed
- ✅ **Tectonic** LaTeX compiler ([installation guide](#installing-tectonic))
- ✅ **Groq API key** (free at [console.groq.com](https://console.groq.com))

### Step 1: Clone & Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Tectonic

Tectonic is a modern LaTeX engine that compiles your papers to PDF.

```bash
# macOS (using Homebrew)
brew install tectonic

# Ubuntu/Debian
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh

# Windows (using Scoop)
scoop install tectonic

# Verify installation
tectonic --version
```

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
nano .env  # or use any text editor
```

Your `.env` file should look like:

```env
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Step 4: Run the Application

```bash
# Start the server
python app.py --port 8000

# You should see:
# * Running on http://127.0.0.1:8000
```

### Step 5: Open in Browser

Navigate to **http://localhost:8000** and start researching! 🎉

---

## 📁 Project Structure

```
ai-research-agent/
│
├── 📄 app.py                 # Flask web server & API endpoints
├── 🤖 ai_researcher.py       # LangGraph agent with tools
├── 🔍 arxiv_tool.py          # arXiv paper search tool
├── 📖 read_pdf.py            # PDF text extraction tool
├── ✍️  write_pdf.py           # LaTeX to PDF compilation tool
│
├── 📋 requirements.txt       # Python dependencies
├── 🔐 .env.example           # Environment variables template
├── 🐳 Dockerfile             # Docker container configuration
├── 🐙 docker-compose.yml     # Docker orchestration
│
├── 📂 templates/
│   └── index.html            # Chat interface HTML
│
├── 📂 static/
│   ├── css/
│   │   └── style.css         # UI styles (dark theme)
│   └── js/
│       └── app.js            # Frontend JavaScript
│
├── 📂 nginx/
│   └── nginx.conf            # Production Nginx config
│
└── 📂 output/                # Generated PDFs (auto-created)
```

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              HTML / CSS / JavaScript                   │  │
│  │                 (Chat Interface)                       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP / SSE
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     FLASK BACKEND                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   /chat     │  │ /chat/stream│  │    /download/       │  │
│  │   (POST)    │  │   (SSE)     │  │    (GET)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   LANGGRAPH AGENT                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   State Machine                        │  │
│  │                                                        │  │
│  │   START ──▶ AGENT ──▶ TOOLS ──▶ AGENT ──▶ END        │  │
│  │              │                    ▲                    │  │
│  │              └────────────────────┘                    │  │
│  │                  (loop until done)                     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │ arxiv_search│  │  read_pdf   │  │ write_pdf   │
   │             │  │             │  │             │
   │ Search for  │  │ Extract     │  │ Generate    │
   │ papers      │  │ PDF text    │  │ PDF files   │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  arXiv API  │  │   PyPDF2    │  │  Tectonic   │
   └─────────────┘  └─────────────┘  └─────────────┘
```

### Agent Workflow

```
User Message
     │
     ▼
┌─────────────────┐
│   LLM (Groq)    │
│                 │
│ Decides action: │
│ • Respond       │
│ • Use tool      │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Respond   Use Tool
    │         │
    │    ┌────┴────────────────┐
    │    ▼         ▼           ▼
    │ arxiv    read_pdf    write_pdf
    │ search                   │
    │    │         │           │
    │    └────┬────┘           │
    │         ▼                ▼
    │   Tool Result       PDF File
    │         │                │
    │         ▼                │
    │    Back to LLM ◀─────────┘
    │         │
    ▼         ▼
┌─────────────────┐
│  Send Response  │
│   to User       │
└─────────────────┘
```

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Groq](https://groq.com/) - Fast LLM inference
- [arXiv](https://arxiv.org/) - Open access research papers
- [Tectonic](https://tectonic-typesetting.github.io/) - Modern LaTeX engine
- [Flask](https://flask.palletsprojects.com/) - Web framework

---
