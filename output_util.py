from rich.table import Table
from rich.console import Console

console = Console()

def format_sats_to_btc(sats: int) -> float:
    """Converts a value in satoshis to BTC."""
    return round(sats / 100000000, 8)

def display_analysis(analysis_results: dict):
    """
    Displays the analysis results in a structured format using Rich.
    """
    if not analysis_results:
        console.print("[bold red]Analysis failed. Check your PSBT input.[/bold red]")
        return
        
    console.print("[bold green]PSBT Analysis Summary[/bold green]")

    table = Table(show_header=True, header_style="bold white")
    table.add_column("Metric", style="dim", width=20)
    table.add_column("Value")
    
    table.add_row("PSBT Version", str(analysis_results["version"]))
    table.add_row("Total Inputs", f"{format_sats_to_btc(analysis_results['total_input_value']):.8f} BTC")
    table.add_row("Total Outputs", f"{format_sats_to_btc(analysis_results['total_output_value']):.8f} BTC")
    table.add_row("Inferred Fee", f"{format_sats_to_btc(analysis_results['inferred_fee']):.8f} BTC")
    table.add_row("Inferred Fee Rate", f"{analysis_results['inferred_fee_rate']:.2f} sats/vB")
    
    console.print(table)
    
    console.print("\n[bold yellow]Fee Reasonableness[/bold yellow]")
    console.print(analysis_results["fee_reasonableness"]["suggestion"])

    console.print("\n[bold yellow]Script Type Summary[/bold yellow]")
    console.print(analysis_results["script_summary"])

    if analysis_results["change_output"]:
        console.print("\n[bold yellow]Change Output Detection[/bold yellow]")
        change_table = Table(show_header=True, header_style="bold white")
        change_table.add_column("Metric")
        change_table.add_column("Value")
        change_table.add_row("Value", f"{format_sats_to_btc(analysis_results['change_output']['amount']):.8f} BTC")
        change_table.add_row("Script Type", analysis_results['change_output']['script_type'])
        change_table.add_row("Address", analysis_results['change_output'].get('address', 'N/A'))
        change_table.add_row("Reason", analysis_results['change_output'].get('reason', 'N/A'))
        console.print(change_table)
    else:
        console.print("No change output detected using a simple heuristic.")

def display_coin_simulation(coin_simulation: dict):
    """
    Displays the coin simulation results in a structured format using Rich.
    """
    for strategy,data in coin_simulation.items():
        table = Table(show_header=True, header_style="bold white")
        console.print("\n[bold yellow]{strategy}[/bold yellow]".format(strategy = strategy))
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value")
        
        if not data:
            return

        table.add_row("Selected amounts", str(data["selected"]))
        table.add_row("Total inputs amounts", f"{format_sats_to_btc(data['total_input']):.8f} BTC")
        table.add_row("Inferred fee", f"{format_sats_to_btc(data['fee']):.8f} BTC")
        table.add_row("Inferred transaction size", f"{(data['vsize']):.0f} vBytes")
        table.add_row("Inferred fee rate", f"{data['effective_rate']:.2f} sats/vB")
        console.print(table)



