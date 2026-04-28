import json
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

def get_styled_status(status):
    if status == "compatible":
        return Text("✔ Compatible", style="green")
    elif status == "warning":
        return Text("⚠ Warning", style="yellow")
    else:
        return Text("✘ Incompatible", style="red")

def generate_terminal_report(report_data):
    console.print("[bold blue]Fortran–C Cross-Language Interface Validation Report[/bold blue]")
    console.print("[dim]Notes: C extraction is compiler-driven (Clang AST), Fortran extraction uses a restricted fallback parser.[/dim]\n")

    console.print("[bold underline]Procedure Comparison:[/bold underline]")
    for proc in report_data["procedures"]:
        console.print(f"\n[bold]{proc['symbol']}[/bold]")
        console.print(f"  Status: {get_styled_status(proc['status'])}")
        console.print(f"  Severity: [bold {proc['severity']}]{proc['severity'].upper()}[/bold]")
        console.print(f"  Risk Score: [bold]{proc['risk_score']}[/bold]")

        if proc["summary"]:
            for s in proc["summary"]:
                console.print(f"  - [{s['level'].upper()}]: {s['issue']}", style=s['level'])
        else:
            console.print("  - [green]No top-level issues.[/green]")

        if proc["per_param"]:
            table = Table(title="Parameters")
            table.add_column("Idx", style="cyan", justify="right")
            table.add_column("Fortran (Name, Type, Mode)", style="magenta")
            table.add_column("C (Name, Raw Type, Ptr Depth)", style="yellow")
            table.add_column("Issues", style="red")

            for pp in proc["per_param"]:
                fortran_info = f"name={pp['fortran']['name'] if pp['fortran'] else 'N/A'}, type={pp['fortran']['base_type'] if pp['fortran'] else 'N/A'}, mode={pp['fortran']['passing_mode'] if pp['fortran'] else 'N/A'}"
                c_info = f"name={pp['c']['name'] if pp['c'] else 'N/A'}, raw={pp['c']['raw'] if pp['c'] else 'N/A'}, ptr_depth={pp['c']['pointer_depth'] if pp['c'] else 'N/A'}"
                issues_text = Text()
                if pp["issues"]:
                    for issue in pp["issues"]:
                        issues_text.append(f"[{issue['level'].upper()}]: {issue['issue']}\n", style=issue['level'])
                else:
                    issues_text.append("[OK] Compatible", style="green")
                table.add_row(str(pp['index']), fortran_info, c_info, issues_text)
            console.print(table)
        console.print("-" * 80)

    console.print("[bold underline]Record (Struct) Comparison:[/bold underline]")
    for rec in report_data["records"]:
        console.print(f"\n[bold]Record: {rec['record']}[/bold]")
        console.print(f"  Status: {get_styled_status(rec['status'])}")
        console.print(f"  Severity: [bold {rec['severity']}]{rec['severity'].upper()}[/bold]")
        console.print(f"  Risk Score: [bold]{rec['risk_score']}[/bold]")

        if rec["summary"]:
            for s in rec["summary"]:
                console.print(f"  - [{s['level'].upper()}]: {s['issue']}", style=s['level'])
        else:
            console.print("  - [green]No top-level issues.[/green]")

        if rec["per_field"]:
            table = Table(title="Fields")
            table.add_column("Idx", style="cyan", justify="right")
            table.add_column("Fortran (Name, Type)", style="magenta")
            table.add_column("C (Name, Raw Type)", style="yellow")
            table.add_column("Issues", style="red")

            for pf in rec["per_field"]:
                fortran_info = f"{pf['fortran']['name']} : {pf['fortran']['base_type']}"
                c_info = f"{pf['c']['name']} : {pf['c']['raw']}"
                issues_text = Text()
                if pf["issues"]:
                    for issue in pf["issues"]:
                        issues_text.append(f"[{issue['level'].upper()}]: {issue['issue']}\n", style=issue['level'])
                else:
                    issues_text.append("[OK] Compatible", style="green")
                table.add_row(str(pf['index']), fortran_info, c_info, issues_text)
            console.print(table)
        console.print("-" * 80)

def generate_json_report(report_data):
    return json.dumps(report_data, indent=2)
