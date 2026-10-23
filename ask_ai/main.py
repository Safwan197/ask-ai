import subprocess
import sys
from pathlib import Path
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .llm import LLMError, ask_llm, clean_command
from .prompts import COMMAND_PROMPT, EXPLAIN_PROMPT
from .safety import is_dangerous

# Load keys from the current folder, then from a global file in the home folder.
load_dotenv()
load_dotenv(Path.home() / ".ask-ai.env")


app = typer.Typer(add_completion=False, help="Turn plain English into shell commands.")
console = Console()
MAX_ERROR_CHARS = 6000  # keep AI requests small and fas

def show_command(cmd: str, title: str = "Suggested command", style: str = 
"cyan"):
    console.print(
        Panel(Syntax(cmd, "bash", theme="monokai", word_wrap=True), 
title=title, border_style=style)
    )
    
    
    
def confirm_and_run(cmd: str):
    if is_dangerous(cmd):
        show_command(cmd, "⚠ POTENTIALLY DANGEROUS", "red")
        answer = typer.prompt("This could damage your system. Type 'yes' to run", default="no")
        if answer.strip().lower() != "yes":
            console.print("[yellow]Cancelled. Nothing was run.[/yellow]")
            raise typer.Exit()
    else:
        show_command(cmd)
        if not typer.confirm("Run this command?", default=True):  # shows [Y/n]
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        console.print(f"[red]Command exited with code {result.returncode}[/red]")
    raise typer.Exit(result.returncode)




def do_command(request: str):
    with console.status("[bold green]Thinking..."):
        cmd = clean_command(ask_llm(COMMAND_PROMPT, request))
    if not cmd:
        console.print("[red]The AI returned an empty answer. Try rephrasing.[/red]")
        raise typer.Exit(1)
    confirm_and_run(cmd)
def do_explain():
    if sys.stdin.isatty():
        console.print("[red]Nothing piped in.[/red] Example: [cyan]npm run build 2>&1 | ask explain[/cyan]")
        raise typer.Exit(1)
    error_text = sys.stdin.read().strip()
    if not error_text:
        console.print("[yellow]Input was empty, nothing to explain.[/yellow]")
        raise typer.Exit(0)
    error_text = error_text[-MAX_ERROR_CHARS:]  # the end of a log usually holds the real error
    with console.status("[bold green]Analyzing error..."):
        reply = ask_llm(EXPLAIN_PROMPT, error_text)
    diagnosis, fix = reply, ""
    if "FIX:" in reply:
        diagnosis, fix = reply.split("FIX:", 1)
    diagnosis = diagnosis.replace("DIAGNOSIS:", "").strip()
    console.print(Panel(diagnosis, title="Diagnosis", border_style="yellow"))
    fix = clean_command(fix)
    if fix:
        # stdin was used by the pipe, so we do not auto-run here. Show the fix only.
        show_command(fix, "Recovery command", "green")
        console.print("[dim]Copy and run it yourself after reading it.[/dim]")
        
        
        
@app.command()
def main(query: list[str] = typer.Argument(None, help='Your request, or the word "explain" with piped input')):
    try:
        if query and query[0].lower() == "explain":
            do_explain()
        elif query:
            do_command(" ".join(query))
        else:
            console.print("[yellow]Tell me what you want.[/yellow] Example: [cyan]ask list large files[/cyan]")
            raise typer.Exit(1)
    except LLMError as e:
        console.print(Panel(str(e), title="AI request failed", 
        border_style="red"))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()       