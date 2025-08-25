# Overview
This project takes in a Partially Signed Bitcoin Transaction and analyzes it via the command line interface. In addition, you can edit the PSBT by adding/removing inputs, adding/removing outputs, or changing the output amount.

It will adjust the fee based on current fee rates from Mempool.space and determine new change.

# Setup
This project relies on some key libraries that can all be added via `pip install` and these include:
- python-bitcointx
- rich
- requests 

# Testing
Included in this project are three example PSBTs found over the internet.

You can test the PSBT Analyzer a couple of ways:

1. Passing in a base64 encoded PSBT directly in the CLI
```
python3 psbt_analyzer.py --psbt cHNidP8BAKACAAAAAqsJSaCMWvfEm4IS9Bfi8Vqz9cM9zxU4IagTn4d6W3vkAAAAAAD+////qwlJoIxa98SbghL0F+LxWrP1wz3PFTghqBOfh3pbe+QBAAAAAP7///8CYDvqCwAAAAAZdqkUdopAu9dAy+gdmI5x3ipNXHE5ax2IrI4kAAAAAAAAGXapFG9GILVT+glechue4O/p+gOcykWXiKwAAAAAAAEA3wIAAAABJoFxNx7f8oXpN63upLN7eAAMBWbLs61kZBcTykIXG/YAAAAAakcwRAIgcLIkUSPmv0dNYMW1DAQ9TGkaXSQ18Jo0p2YqncJReQoCIAEynKnazygL3zB0DsA5BCJCLIHLRYOUV663b8Eu3ZWzASECZX0RjTNXuOD0ws1G23s59tnDjZpwq8ubLeXcjb/kzjH+////AtPf9QUAAAAAGXapFNDFmQPFusKGh2DpD9UhpGZap2UgiKwA4fUFAAAAABepFDVF5uM7gyxHBQ8k0+65PJwDlIvHh7MuEwAAAQEgAOH1BQAAAAAXqRQ1RebjO4MsRwUPJNPuuTycA5SLx4cBBBYAFIXRNTfy4mVAWjTbr6nj3aAfuCMIACICAurVlmh8qAYEPtw94RbN8p1eklfBls0FXPaYyNAr8k6ZELSmumcAAACAAAAAgAIAAIAAIgIDlPYr6d8ZlSxVh3aK63aYBhrSxKJciU9H2MFitNchPQUQtKa6ZwAAAIABAACAAgAAgAA&#61;
```

2. Passing in a file path with a base64 encoded PSBT
```
python3 psbt_analyzer_with_simulation.py --file ./tests/example_psbt_3.psbt
```

If the PSBT can be decoded and is a valid PSBT, you should see it an analysis immediately after entering any of the above commands:



# Learnings

# Potential improvements