# Overview
This project takes in a Partially Signed Bitcoin Transaction and analyzes it via the command line interface. In addition, you can edit the PSBT by adding/removing inputs, adding/removing outputs, or changing the output amount.

It will adjust the fee based on current fee rates from mempol.space and determine new change after edits.

# Setup
This project relies on some key libraries that can all be added via `pip install` and these include:
- python-bitcointx
- rich
- requests 

## Fetching Current Fee Rates
This project makes requests to mempool.space for current fee rates and pulls the API key from a file called `local.secrets`. To get the current fee rates, please create that file at the top directory level and add the api key to it (no formatting of the API key is expected). Otherwise, placeholder fee values will be used.

# Testing
Included in this project are three example PSBTs found over the internet. You can use these to test the functionality of the project.

## Start the Program (via the CLI)
You can execute the program in one of two ways:

1. Passing in a base64 encoded PSBT directly in the command line interface:
```
python3 psbt_analyzer.py --psbt cHNidP8BAKACAAAAAqsJSaCMWvfEm4IS9Bfi8Vqz9cM9zxU4IagTn4d6W3vkAAAAAAD+////qwlJoIxa98SbghL0F+LxWrP1wz3PFTghqBOfh3pbe+QBAAAAAP7///8CYDvqCwAAAAAZdqkUdopAu9dAy+gdmI5x3ipNXHE5ax2IrI4kAAAAAAAAGXapFG9GILVT+glechue4O/p+gOcykWXiKwAAAAAAAEA3wIAAAABJoFxNx7f8oXpN63upLN7eAAMBWbLs61kZBcTykIXG/YAAAAAakcwRAIgcLIkUSPmv0dNYMW1DAQ9TGkaXSQ18Jo0p2YqncJReQoCIAEynKnazygL3zB0DsA5BCJCLIHLRYOUV663b8Eu3ZWzASECZX0RjTNXuOD0ws1G23s59tnDjZpwq8ubLeXcjb/kzjH+////AtPf9QUAAAAAGXapFNDFmQPFusKGh2DpD9UhpGZap2UgiKwA4fUFAAAAABepFDVF5uM7gyxHBQ8k0+65PJwDlIvHh7MuEwAAAQEgAOH1BQAAAAAXqRQ1RebjO4MsRwUPJNPuuTycA5SLx4cBBBYAFIXRNTfy4mVAWjTbr6nj3aAfuCMIACICAurVlmh8qAYEPtw94RbN8p1eklfBls0FXPaYyNAr8k6ZELSmumcAAACAAAAAgAIAAIAAIgIDlPYr6d8ZlSxVh3aK63aYBhrSxKJciU9H2MFitNchPQUQtKa6ZwAAAIABAACAAgAAgAA&#61;
```

2. Passing in a file path with a base64 encoded PSBT:
```
python3 psbt_analyzer.py --file ./tests/example_psbt_2.psbt
```

## PSBT Analysis
If the PSBT can be decoded and is a valid PSBT, you should see an analysis of it immediately after entering either of the above commands:

<img width="613" height="466" alt="Screenshot 2025-08-27 at 7 42 54 PM" src="https://github.com/user-attachments/assets/0378e93c-be29-442b-8818-566370cd9df4" />

## Coin Selection Simulation
After analyzing the PSBT data once, you can then run a coin selection simulation which will attempt different strategies and show the associated changes if those strategies were chosen:

<img width="412" height="653" alt="Screenshot 2025-08-27 at 7 46 14 PM" src="https://github.com/user-attachments/assets/b330883b-ae25-49a4-8ae0-980b6b912bf7" />


## Editing the PSBT
You'll then be prompted to edit the PSBT via pre-defined options:

<img width="274" height="144" alt="Screenshot 2025-08-25 at 7 15 18 PM" src="https://github.com/user-attachments/assets/5a918f53-6a50-4783-b3de-d2b42f7b9d71" />


Once the PSBT edit is completed, the analysis can be re-run!

## Exiting the Program
You can exit the program by responding no to every `[y/n]` prompt.

# Learnings
I learned a great deal about PSBTs while doing this project. I had interacted with PSBTs before but never on a technical level.

Here's several things I learned:
- The fiat system is so seamless with debit/credit card payment rails easily managing inputs and outputs with no change, but of course this comes at the cost of a third party being involved when money is meant for only two (trustless) parties
- How fees are taken by miners based on the difference of inputs and outputs which explains why someone might overpay on fees. (I've heard this happen a couple times and always wondered how a mistake like that could happen)
- Receiving an accurate estimate on what the current fees are is extremely important, and this project sheds a new light on the mempool policy debate that occurred in the btc community a month or two ago
- Python has a ton of useful libraries to make it to create a great and interactive CLI interface

# Potential improvements
This project does a great deal of PSBT analysis (especially when editing) but like most projects it can be improved and we can do that by:
- Finding more example PSBTs to test against (I had a ton of difficultly finding base64 encoded PSBTs that can be parsed correctly)
- Failing open when a non number input is entered for the input, output or change amount
- Caching fee rate responses from mempool.space instead of making that call for each run
- Comparing multiple PSBT's at once (like the original and an edit of the original)
- Improving code readability by use more static variables like for the different pub key script types
