import argparse
from rich.console import Console
from rich.prompt import Prompt, Confirm
from bitcointx.core.psbt import PartiallySignedTransaction
from bitcointx.core.script import CScript
from bitcointx.wallet import CBitcoinAddress
import copy
import fee_service
import output_util
import random

script_types = ['pubkeyhash', 'scripthash', 'witness_v0_keyhash', 'witness_v0_scripthash', 'witness_v1_taproot']

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

def estimate_output_vbyte_from_script_type(script_type):
    # Simplified: assuming standard script lengths
    if script_type == 'pubkeyhash':
        return 25
    elif script_type == 'scripthash':
        return 23
    elif script_type == 'witness_v0_keyhash':
        return 22
    elif script_type == 'witness_v0_scripthash':
        return 34
    elif script_type == 'witness_v1_taproot':
        return 34
    else:
        return 34  # default

def is_output_likely_change(psbt_out, amount, address, address_type, input_address_types, input_addresses):
    """Does a best effort check of which output is change."""
    is_likely_change = False
    change_reason = ""
    if hasattr(psbt_out, 'bip32_derivation') and psbt_out.bip32_derivation or psbt_out.redeem_script or psbt_out.witness_script:
        is_likely_change = True
        change_reason = "Has BIP32 derivation or script metadata"
    else:
        is_round = (amount % 100000 == 0)
        if address_type in input_address_types and address not in input_addresses and 'OP_RETURN' not in address_type and not is_round:
            is_likely_change = True
            change_reason = "Has fresh address of matching type, non-round amount"
    
    return (is_likely_change, change_reason)

def fee_reasonableness_suggestion(rate: float, estimates: dict) -> str:
    """Determines fee reasonableness based on calculated rate."""
    if rate < estimates["halfHourFee"]:
        return f"The fee rate of {rate:.2f} sats/vB seems low. It may take longer than 30 minutes to confirm."
    if rate > estimates["fastestFee"]:
        return f"The fee rate of {rate:.2f} sats/vB is very high. You might be overpaying."
    return f"The fee rate of {rate:.2f} sats/vB is reasonable for a fast confirmation."

def format_script_type_summary(inputs: list, outputs: list) -> str:
    """Determines the script type summary based on inputs and outputs script types."""
    script_types = set()
    for item in inputs + outputs:
        if 'script_type' in item:
            script_types.add(item['script_type'])

    summary = []
    if 'witness_v1_taproot' in script_types:
        summary.append("Taproot scripts are used, providing maximum efficiency and privacy.")
    if 'witness_v0_keyhash' in script_types or 'witness_v0_scripthash' in script_types:
        summary.append("SegWit scripts are used, which are more space-efficient.")
    if 'pubkeyhash' in script_types or 'scripthash' in script_types:
        summary.append("Legacy scripts are used, which have higher transaction weight.")

    return " ".join(summary)


def parse_psbt_input(psbt_base64: str):
    """Analyzes the original PSBT input."""
    try:
        psbt_obj = PartiallySignedTransaction.from_base64(b64_data = psbt_base64)

        parsed_data = {
            "version": psbt_obj.version,
            "inputs": [],
            "outputs": [],
        }

        total_btc_input_amount = 0
        total_btc_output_amount = 0
        estimated_total_input_size = 0
        estimate_output_vbytes = 0

        input_address_types = []
        input_addresses = []
        for i, txin in enumerate(psbt_obj.unsigned_tx.vin):
            psbt_in = psbt_obj.inputs[i]
            if psbt_in.witness_utxo:
                utxo = psbt_in.witness_utxo
            elif psbt_in.non_witness_utxo:
                prev_tx = psbt_in.non_witness_utxo
                utxo = prev_tx.vout[txin.prevout.n]
            else:
                console.print(f"Input {i}: No UTXO info available")
                continue
            
            (script_type, address, address_type) = get_script_and_address_info(utxo.scriptPubKey)
            input_address_types.append(address_type)
            input_addresses.append(address)

            estimated_input_vbytes = estimate_input_vbytes_from_script_type(script_type)
            estimated_total_input_size += estimated_input_vbytes
            amount = utxo.nValue
            total_btc_input_amount += amount

            parsed_data["inputs"].append({
                "amount": amount,
                "script_type": script_type,
                "address": address,
                "address_type": address_type,
                "estimated_input_vbytes": estimated_input_vbytes
            })

        likely_change_output_index = -1
        change_reason = ""
        for i, txout in enumerate(psbt_obj.unsigned_tx.vout):
            psbt_out = psbt_obj.outputs[i]
            script = txout.scriptPubKey

            (script_type, address, address_type) = get_script_and_address_info(script)
            estimated_size = estimate_output_vbyte_from_script(script)
            estimate_output_vbytes += estimated_size
            amount = txout.nValue
            total_btc_output_amount += amount

            parsed_data["outputs"].append({
                "amount": amount,
                "script_type": script_type,
                "address": address,
                "address_type": address_type,
                "estimated_output_vbytes": estimated_size
            })

            is_likely_change, change_reason = is_output_likely_change(psbt_out, amount, address, address_type, input_address_types, input_addresses)
            if is_likely_change:
                likely_change_output_index = i

        fee = total_btc_input_amount - total_btc_output_amount
        
        if fee < 0:
            console.print("[bold red]Warning: Negative fee detected in parsing![/bold red]")
            fee = 0
            fee_rate = 0
        else:
            input_vbytes_list = [input["estimated_input_vbytes"] for input in parsed_data["inputs"]]
            output_vbytes_list = [output["estimated_output_vbytes"] for output in parsed_data["outputs"]]
            total_estimated_vbytes = estimate_tx_vsize(len(parsed_data["inputs"]), len(parsed_data["outputs"]), input_vbytes_list, output_vbytes_list)
            fee_rate = fee / total_estimated_vbytes if total_estimated_vbytes > 0 else 0
            

        parsed_data["inferred_fee"] = fee
        parsed_data["inferred_fee_rate"] = fee_rate
        
        fetched_fee_rates = fee_service.get_recommended_fees()
        fee_reasonableness = {
            "suggestion": "Invalid: negative fee" if fee == 0 and total_btc_input_amount - total_btc_output_amount < 0 else fee_reasonableness_suggestion(fee_rate, fetched_fee_rates),
        }

        parsed_data["change_output"] = parsed_data["outputs"][likely_change_output_index] if likely_change_output_index != -1 else {}
        if parsed_data["change_output"]:
            parsed_data["change_output"]["reason"] = change_reason
        
        parsed_data["fee_reasonableness"] = fee_reasonableness
        parsed_data["total_input_value"] = total_btc_input_amount
        parsed_data["total_output_value"] = total_btc_output_amount
        parsed_data["script_summary"] = format_script_type_summary(parsed_data["inputs"], parsed_data["outputs"])

        return parsed_data
    except Exception as e:
        console.print(f"[bold red]Error parsing PSBT with python-bitcointx:[/bold red] {e}")
        return None

def get_utxos_from_inputs(inputs):
    """Extract UTXOs from parsed inputs for simulation."""
    utxos = []
    for inp in inputs:
        utxos.append({
            'amount': inp['amount'],
            'script_type': inp['script_type'],
            'estimated_vbytes': inp['estimated_input_vbytes']
        })
    return utxos

def calculate_target_amount(parsed_data):
    """Calculate target amount from outputs (excluding change if any)."""
    if parsed_data['change_output']:
        return parsed_data['total_output_value'] - parsed_data['change_output']['amount']
    else:
        return parsed_data['total_output_value']

def estimate_tx_vsize(num_inputs, num_outputs, input_vbytes_list, output_vbytes_list):
    """Estimate total vsize for edited PSBTs."""
    base_size = 10  # version + locktime
    input_varint = 1 if num_inputs < 253 else 3
    output_varint = 1 if num_outputs < 253 else 3
    total_input_vbytes = sum(input_vbytes_list)
    total_output_vbytes = sum(output_vbytes_list)
    return base_size + input_varint + output_varint + total_input_vbytes + total_output_vbytes

def coin_selection(utxos, target, fee_rate, strategy='largest_first', change_output_vbytes=34, target_output_vbytes=[34], force_no_change=False, num_outputs=0):
    """Basic coin selection simulation based on strategy."""
    if strategy == 'smallest_first':
        utxos = sorted(utxos, key=lambda x: x['amount'])
    elif strategy == 'largest_first':
        utxos = sorted(utxos, key=lambda x: x['amount'], reverse=True)
    elif strategy == 'random':
        utxos = random.sample(utxos, len(utxos))
    else:
        raise ValueError("Unknown strategy")
    
    selected = []
    total = 0
    selected_vbytes = []
    
    for utxo in utxos:
        selected.append(utxo)
        total += utxo['amount']
        selected_vbytes.append(utxo['estimated_vbytes'])
        
        if force_no_change:
            # Only try no change
            output_vbytes_list = target_output_vbytes
            vsize = estimate_tx_vsize(len(selected), num_outputs, selected_vbytes, output_vbytes_list)
            min_fee = int(vsize * fee_rate)
            if total >= target + min_fee:
                actual_fee = total - target  # excess goes to fee
                return {
                    'selected': [s['amount'] for s in selected],
                    'total_input': total,
                    'fee': actual_fee,
                    'change': 0,
                    'vsize': vsize,
                    'effective_rate': actual_fee / vsize
                }
        else:
            # Estimate vsize with change output if needed
            num_outputs_w_change = num_outputs + 1  # targets + change
            output_vbytes_list = target_output_vbytes + [change_output_vbytes]
            vsize = estimate_tx_vsize(len(selected), num_outputs_w_change, selected_vbytes, output_vbytes_list)
            fee = int(vsize * fee_rate)  # int for sats
            
            if total >= target + fee:
                change = total - target - fee
                if change > 546:  # dust threshold approx
                    return {
                        'selected': [s['amount'] for s in selected],
                        'total_input': total,
                        'fee': fee,
                        'change': change,
                        'vsize': vsize,
                        'effective_rate': fee / vsize
                    }
                else:
                    # No change
                    output_vbytes_list = target_output_vbytes
                    vsize = estimate_tx_vsize(len(selected), num_outputs, selected_vbytes, output_vbytes_list)
                    fee = int(vsize * fee_rate)
                    if total >= target + fee:
                        actual_fee = fee + (total - (target + fee))  # add excess to fee if any
                        return {
                            'selected': [s['amount'] for s in selected],
                            'total_input': total,
                            'fee': actual_fee,
                            'change': 0,
                            'vsize': vsize,
                            'effective_rate': actual_fee / vsize
                        }
    
    return None  # Insufficient funds

def simulate_coin_selection(parsed_data, fee_rate):
    """Simulate coin selection based on parsed data."""
    if parsed_data['inferred_fee'] < 0:
        return {"error": "Negative fee, simulation skipped"}
    
    utxos = get_utxos_from_inputs(parsed_data['inputs'])
    target = calculate_target_amount(parsed_data)
    
    change_output_vbytes = parsed_data['change_output'].get('estimated_output_vbytes', 34) if parsed_data['change_output'] else 34
    
    non_change_outputs = [out for out in parsed_data['outputs'] if out != parsed_data['change_output']]
    target_output_vbytes = [out['estimated_output_vbytes'] for out in non_change_outputs]
    
    force_no_change = not bool(parsed_data['change_output'])
    
    strategies = ['largest_first', 'smallest_first', 'random']
    
    results = {}
    for strategy in strategies:
        # Pass a copy of utxos to each call to ensure independence
        result = coin_selection(copy.deepcopy(utxos), target, fee_rate, strategy, change_output_vbytes, target_output_vbytes, force_no_change, len(parsed_data["outputs"]))
        if result:
            results[strategy] = result
        else:
            results[strategy] = {"error": "Insufficient funds for this strategy"}
    
    return results

# For editing PSBT - since we can't easily edit the PSBT object and re-sign, we'll edit the parsed_data structure
# and assume re-analysis on modified data
def edit_parsed_data(parsed_data):
    """Creates the interface for editing the PSBT via the command line."""
    while True:
        console.print("\n[bold]Edit Menu:[/bold]")
        console.print("1. Add input")
        console.print("2. Remove input")
        console.print("3. Add output")
        console.print("4. Remove output")
        console.print("5. Change output amount")
        console.print("6. Done editing")
        
        choice = Prompt.ask("Choose an option", choices=["1","2","3","4","5","6"])
        
        if choice == "1":
            amount = int(Prompt.ask("Enter input amount (sats)"))
            script_type = Prompt.ask("Enter script type", choices=script_types)
            estimated_vbytes = estimate_input_vbytes_from_script_type(script_type)
            parsed_data['inputs'].append({
                'amount': amount,
                'script_type': script_type,
                'address': 'edited',
                'address_type': 'edited',
                'estimated_input_vbytes': estimated_vbytes
            })
            console.print("Input added.")
        
        elif choice == "2":
            console.print("Inputs:")
            for i, inp in enumerate(parsed_data['inputs']):
                console.print(f"{i}: {inp['amount']} sats, {inp['script_type']}")
            idx = int(Prompt.ask("Enter index to remove"))
            if 0 <= idx < len(parsed_data['inputs']):
                del parsed_data['inputs'][idx]
                console.print("Input removed.")
        
        elif choice == "3":
            amount = int(Prompt.ask("Enter output amount (sats)"))
            script_type = Prompt.ask("Enter script type", choices=script_types)
            estimated_vb = estimate_output_vbyte_from_script_type(script_type)
            parsed_data['outputs'].append({
                'amount': amount,
                'script_type': script_type,
                'address': 'edited',
                'address_type': 'edited',
                'estimated_output_vbytes': estimated_vb
            })
            console.print("Output added.")
        
        elif choice == "4":
            console.print("Outputs:")
            for i, out in enumerate(parsed_data['outputs']):
                console.print(f"{i}: {out['amount']} sats, {out['script_type']}")
            idx = int(Prompt.ask("Enter index to remove"))
            if 0 <= idx < len(parsed_data['outputs']):
                del parsed_data['outputs'][idx]
                console.print("Output removed.")
        
        elif choice == "5":
            console.print("Outputs:")
            for i, out in enumerate(parsed_data['outputs']):
                console.print(f"{i}: {out['amount']} sats, {out['script_type']}")
            idx = int(Prompt.ask("Enter index to change"))
            if 0 <= idx < len(parsed_data['outputs']):
                new_amount = int(Prompt.ask("Enter new amount (sats)"))
                parsed_data['outputs'][idx]['amount'] = new_amount
                console.print("Amount updated.")
        
        elif choice == "6":
            break
    
    # Recompute totals and vbytes
    parsed_data['total_input_value'] = sum(inp['amount'] for inp in parsed_data['inputs'])
    parsed_data['total_output_value'] = sum(out['amount'] for out in parsed_data['outputs'])
    
    estimated_total_input_size = [inp['estimated_input_vbytes'] for inp in parsed_data['inputs']]
    estimate_output_vbytes = [out['estimated_output_vbytes'] for out in parsed_data['outputs']]
    input_count = len(parsed_data['inputs'])    
    output_count = len(parsed_data['outputs'])
    total_estimated_vbytes = estimate_tx_vsize(input_count, output_count, estimated_total_input_size, estimate_output_vbytes)
    
    # Assume last output as change after edit if multiple outputs
    if len(parsed_data['outputs']) > 1:
        likely_change_output_index = len(parsed_data['outputs']) - 1
        parsed_data['change_output'] = parsed_data['outputs'][likely_change_output_index]
        parsed_data['change_output']['reason'] = "Assumed last output as change after edit"
    else:
        parsed_data['change_output'] = {}
    
    # Adjust change output if present
    if parsed_data['change_output']:
        non_change_outputs = [out for out in parsed_data['outputs'] if out != parsed_data['change_output']]
        target = sum(out['amount'] for out in non_change_outputs)
        
        fetched_fee_rates = fee_service.get_recommended_fees()
        fee_rate = fetched_fee_rates['hourFee']  # Use hourFee for reasonable confirmation
        
        fee = int(total_estimated_vbytes * fee_rate)
        
        if parsed_data['total_input_value'] >= target + fee + 546:  # dust threshold
            new_change = parsed_data['total_input_value'] - target - fee
            parsed_data['change_output']['amount'] = new_change
            parsed_data['total_output_value'] = target + new_change
            parsed_data['inferred_fee'] = fee
            parsed_data['inferred_fee_rate'] = fee_rate
            parsed_data['fee_reasonableness']['suggestion'] = fee_reasonableness_suggestion(fee_rate, fetched_fee_rates)
        else:
            # Try without change
            vbytes_without_change = total_estimated_vbytes - parsed_data['change_output']['estimated_output_vbytes']
            if output_count - 1 < 253 and output_count >= 253:
                vbytes_without_change -= 2  # from 3 to 1
            fee_without = int(vbytes_without_change * fee_rate)
            if parsed_data['total_input_value'] >= target + fee_without:
                console.print("[yellow]Change would be dust or negative; removing change output and adjusting fee.[/yellow]")
                parsed_data['outputs'].pop(likely_change_output_index)
                parsed_data['total_output_value'] = target
                parsed_data['inferred_fee'] = parsed_data['total_input_value'] - target
                parsed_data['inferred_fee_rate'] = parsed_data['inferred_fee'] / vbytes_without_change if vbytes_without_change > 0 else 0
                parsed_data['change_output'] = {}
                parsed_data['fee_reasonableness']['suggestion'] = fee_reasonableness_suggestion(parsed_data['inferred_fee_rate'], fetched_fee_rates)
            else:
                console.print("[bold red]Insufficient funds even without change.[/bold red]")
                parsed_data['inferred_fee'] = parsed_data['total_input_value'] - parsed_data['total_output_value']
                parsed_data['inferred_fee_rate'] = 0
    else:
        # No change, excess to fee
        parsed_data['inferred_fee'] = parsed_data['total_input_value'] - parsed_data['total_output_value']
        parsed_data['inferred_fee_rate'] = parsed_data['inferred_fee'] / total_estimated_vbytes if total_estimated_vbytes > 0 else 0
        fetched_fee_rates = fee_service.get_recommended_fees()
        parsed_data['fee_reasonableness']['suggestion'] = fee_reasonableness_suggestion(parsed_data['inferred_fee_rate'], fetched_fee_rates)
    
    parsed_data['script_summary'] = format_script_type_summary(parsed_data['inputs'], parsed_data['outputs'])
    
    return parsed_data

def analyze_psbt():
    """
    Main function to handle command-line arguments and run the psbt analyzer.
    """
    parser = argparse.ArgumentParser(description="Bitcoin PSBT Analyzer & Optimizer")
    parser.add_argument("--psbt", type=str, help="PSBT Base64 string to analyze")
    parser.add_argument("--file", type=str, help="Path to a PSBT file")

    args = parser.parse_args()

    # Passed in string takes precedence as its both easier to pass in for the user and parse
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
    
    parsed_data = parse_psbt_input(psbt_data_input)
    if parsed_data is None:
        return
    
    while True:
        output_util.display_analysis(parsed_data)
        
        # Simulate coin selection
        if Confirm.ask("Run coin selection simulation?"):
            fee_rate = parsed_data['inferred_fee_rate'] if parsed_data['inferred_fee_rate'] > 0 else fee_service.get_recommended_fees()['fastestFee']
            sim_results = simulate_coin_selection(parsed_data, fee_rate)
            console.print("\n[bold]Coin Selection Simulation:[/bold]")
            output_util.display_coin_simulation(sim_results)
        
        # Edit
        if Confirm.ask("Edit the PSBT data?"):
            parsed_data = edit_parsed_data(copy.deepcopy(parsed_data))  # Work on copy
        
        if not Confirm.ask("Re-run analysis?"):
            break

if __name__ == "__main__":
    analyze_psbt()