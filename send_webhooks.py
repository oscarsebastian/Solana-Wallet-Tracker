from discord_webhook import DiscordWebhook,DiscordEmbed
import discord
from discord.ext import commands
import time
import pandas as pd

CONFIG=pd.read_csv('config.csv')


""" Obtains links and transactions identifiers which will be used in the webhooks."""

def transaction_hook_information(nft_signature,wallet):
    tx_short_id=f"{nft_signature[0:3]}..."
    tx_link=f"https://solscan.io/tx/{nft_signature}"
    wallet_link=f"https://solscan.io/account/{wallet}"
    return tx_short_id,tx_link,wallet_link


""" Function which will send the upcoming operations of the given Solana wallets."""

def send_hook(wallet,nft_signature,nft_price,nft_name,nft_image,nft_royalties,mode):
    
    WALLETS_TO_MONITOR=pd.read_csv('wallets.csv')
    wallet_identifier=WALLETS_TO_MONITOR.set_index('public_key')
    webhook_url=CONFIG['wallet_tracker_webhook_url'].values[0]

    wallet_identifier=wallet_identifier['wallet_identifier'].to_dict()

    tx_short_id,tx_link,wallet_link=transaction_hook_information(nft_signature,wallet)
    webhook = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title=f"New {mode} detected :white_check_mark:",url=tx_link,color='0x7b253c')
    embed.set_author(name='Wallet Tracker',icon_url='https://pbs.twimg.com/profile_images/1588831094492766210/bP1cJnSN_400x400.jpg')

    identified_wallet=wallet_identifier.get(wallet)
    if not identified_wallet:
        identified_wallet=f"{wallet[0:3]}.."
    embed.add_embed_field(name='**Who?**',value=f"[{identified_wallet}]({wallet_link})",inline=False) 
  
    if nft_name:
        embed.add_embed_field(name='Token Name',value=f"```{nft_name}```",inline=True)    
    if nft_price:
        embed.add_embed_field(name='Price',value=f"```{nft_price} SOL```",inline=True)  
    if nft_royalties:
        embed.add_embed_field(name='Royalties',value=f"```{str(round(nft_royalties/100,2))}%```",inline=True)
    if nft_image:
        embed.set_thumbnail(url=nft_image)

    embed.add_embed_field(name='**Transaction**',value=f"[{tx_short_id}]({tx_link})",inline=False)  
    embed.set_footer(text='Wallet Tracker by o s c a r#6467')
    embed.set_timestamp()
    webhook.add_embed(embed)

    hook_response = webhook.execute()
    while hook_response.status_code == 429:
        hook_response = webhook.execute()
        time.sleep(5)