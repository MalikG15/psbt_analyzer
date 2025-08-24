import argparse
from rich.console import Console

# Initialize Rich console for pretty output
console = Console()

def analyze_psbt():
    """
    Main function to handle command-line arguments and run the psbt analyzer.
    """
    parser = argparse.ArgumentParser(description="Bitcoin PSBT Analyzer & Optimizer")
    parser.add_argument("--psbt", type=str, help="PSBT Base64 string to analyze")
    parser.add_argument("--file", type=str, help="Path to a PSBT file")

    args = parser.parse_args()
    print(args)

    # Passed in string takes precendence as its both easier to pass in for the user and parse
    if args.psbt:
        psbt_data_input = args.psbt
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                psbt_data_input = f.read().strip()
        except FileNotFoundError:
            console.print("[bold red]Error:[/bold red] File not found.")
            return

if __name__ == "__main__":
    analyze_psbt()