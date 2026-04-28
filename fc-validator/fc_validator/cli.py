import typer
from pathlib import Path
from typing_extensions import Annotated

from fc_validator.c_parser import get_c_model
from fc_validator.fortran_parser import extract_fortran_model
from fc_validator.compare import validate_all
from fc_validator.report import generate_terminal_report, generate_json_report

app = typer.Typer(
    name="fc-validator",
    help="A tool for validating Fortran BIND(C) and C header interfaces."
)

@app.command()
def main(
    fortran_file: Annotated[Path, typer.Argument(exists=True, readable=True, help="Path to the Fortran .f90 file.")],
    c_header: Annotated[Path, typer.Argument(exists=True, readable=True, help="Path to the C .h header file.")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output report in JSON format.")] = False,
):
    """Validate Fortran BIND(C) interfaces against C header declarations."""

    # Ensure a build directory exists for intermediate files like C AST
    build_dir = Path(".") / "build_temp"
    build_dir.mkdir(exist_ok=True)

    try:
        # 1. Extract Fortran model
        typer.echo(f"Parsing Fortran file: {fortran_file}")
        f_model = extract_fortran_model(fortran_file)

        # 2. Extract C model
        typer.echo(f"Parsing C header: {c_header}")
        c_model = get_c_model(c_header, build_dir)

        # 3. Compare models
        typer.echo("Comparing Fortran and C interfaces...")
        report = validate_all(f_model, c_model)

        # 4. Generate report
        if json_output:
            typer.echo(generate_json_report(report))
        else:
            generate_terminal_report(report)

    except Exception as e:
        typer.echo(f"[ERROR] An unexpected error occurred: {e}", err=True)
        raise typer.Exit(code=1)

    finally:
        # Clean up temporary build directory
        import shutil
        if build_dir.exists():
            shutil.rmtree(build_dir)

if __name__ == "__main__":
    app()
