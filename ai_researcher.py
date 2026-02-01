from typing_extensions import TypedDict
from typing import Annotated,Literal
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages] 
    
    
    
from arxiv_tool import *
from read_pdf import *
from write_pdf import *
from langgraph.prebuilt import ToolNode

tools=[read_pdf,render_latex_pdf,arxiv_search]
tool_node=ToolNode(tools)

import os 
from langchain_groq.chat_models import ChatGroq

models=ChatGroq(model="openai/gpt-oss-120b",api_key=os.getenv("GROQ_API_KEY")).bind_tools(tools)


from langgraph.graph import END,START,StateGraph



def call_model(state:State):
    messages=state["messages"]
    response=models.invoke(messages)
    return {"messages":[response]}

def should_continue(state: State) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END



workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")




from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
config = {"configurable": {"thread_id": 222222}, "recursion_limit": 25}  # Limit to 25 iterations

graph = workflow.compile(checkpointer=checkpointer)



# Step5: TESTING
INITIAL_PROMPT = """
You are an expert researcher in the fields of physics, mathematics,
computer science, quantitative biology, quantitative finance, statistics,
electrical engineering and systems science, and economics.

You are going to analyze recent research papers in one of these fields in
order to identify promising new research directions and then write a new
research paper. For research information or getting papers, ALWAYS use arxiv.org.
You will use the tools provided to search for papers, read them, and write a new
paper based on the ideas you find.

IMPORTANT: You have access to ONLY these three tools:
1. arxiv_search(topic: str) - Search for papers on arXiv. Use simple keywords without quotes or special characters.
2. read_pdf(url: str) - Read and extract text from a PDF given its URL.
3. render_latex_pdf(latex_content: str) - Render LaTeX content to a PDF file. YOU MUST USE THIS TOOL to generate PDFs.

Do NOT attempt to use any other tools. Only use the three tools listed above.

WORKFLOW:
1. First, ask me what topic I want to research.
2. Call arxiv_search ONCE with simple keywords (e.g., "machine learning" or "neural networks").
3. Present the papers found to me (DO NOT search again unless I ask for different results).
4. Wait for me to choose a paper.
5. Read the chosen paper using read_pdf.
6. Discuss the paper with me and suggest research ideas.
7. When I ask you to write a paper, use render_latex_pdf to generate the PDF.

IMPORTANT RULES:
- Call arxiv_search only ONCE per topic. Do not repeat searches.
- After searching, STOP and present results to the user.
- Do not keep searching in a loop - one search is enough.
- Wait for user input before taking the next action.

CRITICAL INSTRUCTIONS FOR WRITING PAPERS:
- When asked to write a paper, you MUST use the render_latex_pdf tool to generate the PDF.
- DO NOT output LaTeX code as plain text in the chat.
- Instead, call the render_latex_pdf tool with the complete LaTeX document as the argument.

LATEX TEMPLATE - USE THIS EXACT STRUCTURE:
```
\\documentclass[12pt]{article}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{hyperref}
\\usepackage[margin=1in]{geometry}

\\title{Your Paper Title}
\\author{AI Research Assistant}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
Your abstract here.
\\end{abstract}

\\section{Introduction}
Your introduction here.

\\section{Methods}
Your methods here. You can use equations like:
\\begin{equation}
E = mc^2
\\end{equation}

\\section{Results}
Your results here.

\\section{Conclusion}
Your conclusion here.

\\begin{thebibliography}{9}
\\bibitem{ref1} Author, "Title", Journal, Year. \\url{https://arxiv.org/pdf/...}
\\end{thebibliography}

\\end{document}
```

IMPORTANT LATEX RULES:
- Always include \\usepackage{amsmath} and \\usepackage{amssymb} for math
- Always include \\usepackage{hyperref} for URLs
- Use \\url{} for links, NOT \\href{}
- Do NOT use custom or obscure packages
- Do NOT use \\R, \\N, \\Z - use \\mathbb{R}, \\mathbb{N}, \\mathbb{Z} instead
- Do NOT use undefined commands
- Make sure all braces {} are properly matched

If the tool returns an error, read the error message carefully and fix the LaTeX, then try again.

Remember: 
- Search arxiv ONCE, then STOP and present results
- ALWAYS use render_latex_pdf tool to generate PDFs
- Never show LaTeX code as plain text"""




def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        print(f"Message received: {message.content[:200]}...")
        message.pretty_print()