import typer


app = typer.Typer()
@app.command()
def main(query: list[str] = typer.Argument(None)):
    print("You asked:", " ".join(query or []))
if __name__ == "__main__":
    app()
