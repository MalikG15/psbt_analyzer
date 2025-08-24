import argparse
import base64
from rich.console import Console
from bitcointx.core.psbt import PartiallySignedTransaction
from bitcointx.core.script import CScript
from bitcointx.wallet import CBitcoinAddress

# Initialize Rich console for pretty output
console = Console()

def get_script_and_address_info(script_pubkey):
    script_type = CScript(script_pubkey)
    try:
        address_obj = CBitcoinAddress.from_scriptPubKey(script_pubkey)
        address = str(address_obj)
        address_type = address_obj.__class__.__name__
    except ValueError:
        address = "Non-standard"
        address_type = "Non-standard"

    return (get_script_type(script_type), address, address_type)

def get_script_type(script):
    if script.is_p2pkh():
        script_type = 'pubkeyhash'
    elif script.is_p2sh():
        script_type = 'scripthash'
    elif script.is_witness_v0_keyhash():
        script_type = 'witness_v0_keyhash'
    elif script.is_witness_v0_scripthash():
        script_type = 'witness_v0_scripthash'
    elif script.is_witness_v1_taproot():
        script_type = 'witness_v1_taproot'
    else:
        script_type = 'unknown'
    
    return script_type

def estimate_input_vbytes_from_script_type(script_type):
    # Estimate input contribution to vsize based on script type
    if script_type in ['pubkeyhash', 'scripthash']:
        input_vb = 148
    elif script_type == 'witness_v0_keyhash':
        input_vb = 68
    elif script_type == 'witness_v0_scripthash':
        input_vb = 100
    elif script_type == 'witness_v1_taproot':
        input_vb = 58
    else:
        input_vb = 148

    return input_vb

def estimate_output_vbyte_from_script(script):
    script_len = len(script)
    varint_len = 1 if script_len < 253 else 3
    return 8 + varint_len + script_len

def parse_psbt_input(psbt_base64: str):
    try:
        psbt_obj = PartiallySignedTransaction.from_base64(b64_data = psbt_base64)

        parsed_data = {
            "version": psbt_obj.version,
            "inputs": [],
            "outputs": [],
            "fee": 0, # Will be calculated later
        }

        total_amount = 0
        estimated_total_size = 0

        for i, txin in enumerate(psbt_obj.unsigned_tx.vin):
            psbt_in = psbt_obj.inputs[i]
            if psbt_in.witness_utxo:
                utxo = psbt_in.witness_utxo
            elif psbt_in.non_witness_utxo:
                prev_tx = psbt_in.non_witness_utxo
                utxo = prev_tx.vout[txin.prevout.n]
            else:
                print(f"Input {i}: No UTXO info available")
                continue
            
            (script_type, address, address_type) = get_script_and_address_info(utxo.scriptPubKey)

            estimated_input_vbytes = estimate_input_vbytes_from_script_type(script_type)
            estimated_total_size += estimated_input_vbytes
            amount = utxo.nValue
            total_amount += amount

            parsed_data["inputs"].append({
                "amount": amount,
                "script_type": script_type,
                "address": address,
                "address_type": address_type,
                "estimated_input_vbytes": estimated_input_vbytes
            })

        for txout in psbt_obj.unsigned_tx.vout:
            script = txout.scriptPubKey

            (script_type, address, address_type) = get_script_and_address_info(script)

            parsed_data["outputs"].append({
                "script_type": script_type,
                "address": address,
                "address_type": address_type,
                "estimated_output_vb": estimate_output_vbyte_from_script(script_type)
            })

        return parsed_data
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
    
    print(parse_psbt_input(psbt_data_input))

if __name__ == "__main__":
    analyze_psbt()