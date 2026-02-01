from langchain_core.tools import tool
from datetime import datetime
from pathlib import Path
import subprocess
import shutil
import re


def sanitize_latex(latex_content: str) -> str:
    """Clean up common LaTeX issues that LLMs produce."""
    
    # Remove any markdown code block markers
    latex_content = re.sub(r'^```latex\s*', '', latex_content)
    latex_content = re.sub(r'^```\s*', '', latex_content)
    latex_content = re.sub(r'\s*```$', '', latex_content)
    
    # Fix common LLM mistakes
    
    # Fix \begin{split} without amsmath (add amsmath if not present)
    if r'\begin{split}' in latex_content or r'\begin{align}' in latex_content:
        if r'\usepackage{amsmath}' not in latex_content:
            # Add amsmath after documentclass
            latex_content = re.sub(
                r'(\\documentclass[^\n]*\n)',
                r'\1\\usepackage{amsmath}\n',
                latex_content
            )
    
    # Fix \mathbb without amssymb
    if r'\mathbb' in latex_content:
        if r'\usepackage{amssymb}' not in latex_content:
            latex_content = re.sub(
                r'(\\documentclass[^\n]*\n)',
                r'\1\\usepackage{amssymb}\n',
                latex_content
            )
    
    # Fix common undefined control sequences
    # \R, \N, \Z etc. should be \mathbb{R}, \mathbb{N}, \mathbb{Z}
    latex_content = re.sub(r'\\R(?![a-zA-Z])', r'\\mathbb{R}', latex_content)
    latex_content = re.sub(r'\\N(?![a-zA-Z])', r'\\mathbb{N}', latex_content)
    latex_content = re.sub(r'\\Z(?![a-zA-Z])', r'\\mathbb{Z}', latex_content)
    latex_content = re.sub(r'\\Q(?![a-zA-Z])', r'\\mathbb{Q}', latex_content)
    latex_content = re.sub(r'\\C(?![a-zA-Z])', r'\\mathbb{C}', latex_content)
    
    # Fix \text{} without amsmath
    if r'\text{' in latex_content:
        if r'\usepackage{amsmath}' not in latex_content:
            latex_content = re.sub(
                r'(\\documentclass[^\n]*\n)',
                r'\1\\usepackage{amsmath}\n',
                latex_content
            )
    
    # Add graphicx if \includegraphics is used
    if r'\includegraphics' in latex_content:
        if r'\usepackage{graphicx}' not in latex_content:
            latex_content = re.sub(
                r'(\\documentclass[^\n]*\n)',
                r'\1\\usepackage{graphicx}\n',
                latex_content
            )
    
    # Add hyperref for \href and \url
    if r'\href' in latex_content or r'\url' in latex_content:
        if r'\usepackage{hyperref}' not in latex_content:
            latex_content = re.sub(
                r'(\\documentclass[^\n]*\n)',
                r'\1\\usepackage{hyperref}\n',
                latex_content
            )
    
    # Fix double usepackage declarations
    lines = latex_content.split('\n')
    seen_packages = set()
    cleaned_lines = []
    for line in lines:
        match = re.match(r'\\usepackage(\[.*?\])?\{([^}]+)\}', line.strip())
        if match:
            package = match.group(2)
            if package in seen_packages:
                continue  # Skip duplicate
            seen_packages.add(package)
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


@tool
def render_latex_pdf(latex_content: str) -> str:
    """Render a LaTeX document to PDF.

    Args:
        latex_content: The LaTeX document content as a string. Must be a complete 
                      LaTeX document starting with \\documentclass and ending with \\end{document}.
                      Use standard packages like amsmath, amssymb, graphicx, hyperref.
                      Avoid custom or unusual packages.

    Returns:
        Path to the generated PDF document, or an error message if compilation fails.
    """
    if shutil.which("tectonic") is None:
        return "Error: tectonic is not installed. Please install it with: brew install tectonic"

    try:
        # Sanitize the LaTeX content
        latex_content = sanitize_latex(latex_content)
        
        # Create directory
        output_dir = Path("output").absolute()
        output_dir.mkdir(exist_ok=True)
        
        # Setup filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tex_filename = f"paper_{timestamp}.tex"
        pdf_filename = f"paper_{timestamp}.pdf"
        
        # Write LaTeX file
        tex_file = output_dir / tex_filename
        tex_file.write_text(latex_content)
        print(f"LaTeX file written to: {tex_file}")

        # Run tectonic and capture output
        result = subprocess.run(
            ["tectonic", tex_filename, "--outdir", str(output_dir)],
            cwd=output_dir,
            capture_output=True,
            text=True,
        )

        # Log stdout and stderr for debugging
        if result.stdout:
            print(f"Tectonic stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Tectonic stderr:\n{result.stderr}")

        # Check if tectonic command failed
        if result.returncode != 0:
            # Extract the error line number and message
            error_match = re.search(r'error: [^:]+:(\d+): (.+)', result.stderr)
            if error_match:
                line_num = int(error_match.group(1))
                error_msg = error_match.group(2)
                
                # Get the problematic line from the LaTeX content
                lines = latex_content.split('\n')
                problematic_line = lines[line_num - 1] if line_num <= len(lines) else "Unknown"
                
                return (f"LaTeX compilation failed at line {line_num}: {error_msg}\n"
                        f"Problematic line: {problematic_line}\n"
                        f"Please fix the LaTeX error and try again. "
                        f"Common issues: undefined commands, missing packages, or syntax errors.")
            else:
                return (f"LaTeX compilation failed: {result.stderr}\n"
                        f"Please fix the LaTeX errors and try again.")

        final_pdf = output_dir / pdf_filename
        if not final_pdf.exists():
            # Check for any PDF files that might have been generated with different name
            pdf_files = list(output_dir.glob("*.pdf"))
            if pdf_files:
                final_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
            else:
                return "PDF file was not generated. Please check the LaTeX content for errors."

        print(f"Successfully generated PDF at {final_pdf}")
        return str(final_pdf)

    except Exception as e:
        print(f"Error rendering LaTeX: {str(e)}")
        return f"Error rendering LaTeX: {str(e)}. Please try again with valid LaTeX content."