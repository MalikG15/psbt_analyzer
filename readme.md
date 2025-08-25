# Overview
This project takes in a Partially Signed Bitcoin Transaction and analyzes it via the command line interface. In addition, you can edit the PSBT by adding/removing inputs, adding/removing outputs, or changing the output amount.

It will adjust the fee based on current fee rates from Mempool.space and determine new change.

# Setup
This project relies on some key libraries that can all be added via `pip install` and these include:
- python-bitcointx
- rich
- requests 

## Mempool.space API Key
This project makes requests to mempool.space for current fee rates and pulls the API key from a file called `local.secrets`. To get the current fee rates, please create that file in the top level directory and add the api key to it. Otherwise, placeholder fee values will be used.

# Testing
Included in this project are three example PSBTs found over the internet.

You can test the PSBT Analyzer a couple of ways:

## Starting the Program via the CLI
You can execute the program in one of two ways:

1. Passing in a base64 encoded PSBT directly in the CLI
```
python3 psbt_analyzer.py --psbt cHNidP8BAKACAAAAAqsJSaCMWvfEm4IS9Bfi8Vqz9cM9zxU4IagTn4d6W3vkAAAAAAD+////qwlJoIxa98SbghL0F+LxWrP1wz3PFTghqBOfh3pbe+QBAAAAAP7///8CYDvqCwAAAAAZdqkUdopAu9dAy+gdmI5x3ipNXHE5ax2IrI4kAAAAAAAAGXapFG9GILVT+glechue4O/p+gOcykWXiKwAAAAAAAEA3wIAAAABJoFxNx7f8oXpN63upLN7eAAMBWbLs61kZBcTykIXG/YAAAAAakcwRAIgcLIkUSPmv0dNYMW1DAQ9TGkaXSQ18Jo0p2YqncJReQoCIAEynKnazygL3zB0DsA5BCJCLIHLRYOUV663b8Eu3ZWzASECZX0RjTNXuOD0ws1G23s59tnDjZpwq8ubLeXcjb/kzjH+////AtPf9QUAAAAAGXapFNDFmQPFusKGh2DpD9UhpGZap2UgiKwA4fUFAAAAABepFDVF5uM7gyxHBQ8k0+65PJwDlIvHh7MuEwAAAQEgAOH1BQAAAAAXqRQ1RebjO4MsRwUPJNPuuTycA5SLx4cBBBYAFIXRNTfy4mVAWjTbr6nj3aAfuCMIACICAurVlmh8qAYEPtw94RbN8p1eklfBls0FXPaYyNAr8k6ZELSmumcAAACAAAAAgAIAAIAAIgIDlPYr6d8ZlSxVh3aK63aYBhrSxKJciU9H2MFitNchPQUQtKa6ZwAAAIABAACAAgAAgAA&#61;
```

2. Passing in a file path with a base64 encoded PSBT
```
python3 psbt_analyzer.py --file ./tests/example_psbt_3.psbt
```

## PSBT Analysis
If the PSBT can be decoded and is a valid PSBT, you should see it an analysis immediately after entering any of the above commands:

<img width="565" height="467" alt="Screenshot 2025-08-25 at 7 11 23 PM" src="https://github.com/user-attachments/assets/f64a8c9c-783e-4577-87ed-f3d552073ce7" />

## Coin Selection Simulation
After analyzing the PSBT data once, you can then run a coin selection simulation which will attempt different strategies and show the associated changes if those strategies were chosen:

<img width="418" height="653" alt="Screenshot 2025-08-25 at 7 23 43 PM" src="https://github.com/user-attachments/assets/f7de032c-4c42-4e8e-ad22-439a8fe5b1fc" />

## Editing the PSBT
You'll then be prompted to edit the PSBT via defined options:

<img width="274" height="144" alt="Screenshot 2025-08-25 at 7 15 18 PM" src="https://github.com/user-attachments/assets/5a918f53-6a50-4783-b3de-d2b42f7b9d71" />


Once the PSBT edit is completed, the analysis can be re-run!
# Learnings
I learned a great deal about PSBTs while doing this project. I had interacted with PSBTs before but of course never in such detail.

I think the main thing I learned was how the fiat system has got us so accustomed to transactions happening where the input matches the output and there is no change. It just seems like all payment information has be obfiscuated from us. Of course, when using a credit card, there are fees that are paid by the merchant where the card is being spent but even that is hidden from the consumer.

Working on this PSBT project emphasized how it used to be when money transactions were between only the two parties involved. Everything has to be handled by either party a or party b which means handling fees and change if any.

# Potential improvements
This project does a great deal of PSBT analysis (especially when editing) but like most projects it can be improved in several such as:
- Finding more example PSBTs to test against (I had a ton of difficultly finding PSBTs that can be parsed correctly)
- Failing open when a non number input is entered for the input or change amount
- Caching fee rate responses from mempool.space instead of making that call for each run
- Comparing multiple PSBT's at once (like the original and an edit of the original)
