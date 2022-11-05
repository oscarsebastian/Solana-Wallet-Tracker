# Solana Wallet Tracker

Script to detect user's operation based on their public wallet address!
This version is fully on chain , it uses Solana's RPC also known as validators to monitor certain user's wallets and detect their minting, listings and sales operations.


## What do I need to know?

In order to be able to run this code you must follow some steps!

*1) Install the requirements.txt with pip install -r requirements.txt 
*2) Must also install !npx degit metaplex-foundation/python-api/metaplex metaplex
*3) You must add the webhook url where you will get pinged into config.csv under wallet_tracker_webhook_url
*4) You must add the webhook url where you will get notified after adding a wallet to the discord bot via command in a specific channel into config.csv under wallet_adding_bot_url
*5) It is important to change (message.channel.id : integer)  in main.py to the desired channel which you will use to add wallets with the command 
public_key : username 
*6) Finally you must add your discord bot token in the field bot.run (Last line of code : string)

## How does it work?

You can check in this docs to see how it works : [SolanaDocs](https://docs.solana.com/developing/clients/jsonrpc-api#getaccountinfo)


## Contributions!

If you are using this script for your DAO and want to contribute so I add more open source tools you can donate into this SOL wallet ALKMPuNt3pWd118cYkg4NPM6M5uiimyZLhKFWa44EDce

