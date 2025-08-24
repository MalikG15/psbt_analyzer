import argparse
import base64
from rich.console import Console
from bitcointx.core.psbt import PartiallySignedTransaction

# Initialize Rich console for pretty output
console = Console()

def parse_psbt_input(psbt_base64: str):
    try:
        psbt_obj = PartiallySignedTransaction.from_base64(b64_data = psbt_base64)
        print(psbt_obj)
    except Exception as e:
        console.print(f"[bold red]Error parsing PSBT with python-bitcointx:[/bold red] {e}")
        return None


def analyze_psbt():
    """
    Main function to handle command-line arguments and run the psbt analyzer.
    """
    parser = argparse.ArgumentParser(description="Bitcoin PSBT Analyzer & Optimizer")
    parser.add_argument("--psbt", type=str, help="PSBT Base64 string to analyze")
    parser.add_argument("--file", type=str, help="Path to a PSBT file")

    args = parser.parse_args()

    # Passed in string takes precendence as its both easier to pass in for the user and parse
    psbt_data_input = None
    if args.psbt:
        psbt_data_input = args.psbt
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                psbt_data_input = f.read().strip()
        except FileNotFoundError:
            console.print("[bold red]Error:[/bold red] File not found.")
            return
    
    parse_psbt_input(psbt_data_input)

if __name__ == "__main__":
    analyze_psbt()