from solana.rpc.api import Client
import requests 
import json
import time
from discord_webhook import DiscordWebhook,DiscordEmbed
import discord
from discord.ext import commands
import threading


"""" INPUTS """

wallet_identifier={'public_wallet_adress':'person_to_monitor_nick'}

"Insert here the webhook where you will receive the notifications"
webhook_url=''  
"Insert here the webhook of the channel where you will add new wallets via command!"
webhook_bot=''  




""" WEBHOOK SEND"""

"""Function will receive public wallet key , tx signature , operation price , image and type of operation"""

def send_hook(wallet,nft_signature,nft_price,nft_name,nft_image,mode):
        webhook = DiscordWebhook(url=webhook_url)
        first_txs=f"{nft_signature[0:3]}..."
        tx_link=f"https://solscan.io/tx/{nft_signature}"
        wallet_link=f"https://solscan.io/account/{wallet}"
        embed = DiscordEmbed(title=f"New {mode} detected :bomb:",url=f"https://solscan.io/account/{wallet}",color='0x7b253c')
        minter=wallet_identifier.get(wallet)
        if not minter:
            minter=f"{wallet[0:3]}.."
        embed.add_embed_field(name='**Who?**',value=f"[{minter}]({wallet_link})",inline=True) 
        if nft_price:
            embed.add_embed_field(name='**Price**',value=f"{nft_price} SOL",inline=True)
        if nft_name:
            embed.add_embed_field(name='**Token Name**',value=nft_name,inline=False)
        if nft_image:
            embed.set_thumbnail(url=nft_image)
        embed.add_embed_field(name='**Transaction**',value=f"[{first_txs}]({tx_link})",inline=True)  
  
        embed.set_timestamp()
        webhook.add_embed(embed)
        hook_response = webhook.execute()
        while hook_response.status_code == 429:
            hook_response = webhook.execute()
            time.sleep(5)



""" GET TX INFO """

""" With this function which is blockchain based, we will get the tx info of a specific public key!"""

def tx_info(signature,wallet):
    print(f"Fetching info for tx : {[signature]}")
    endpoint = 'https://api.mainnet-beta.solana.com'
    json_data = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'getTransaction',
    'params': [
        f'{signature}',
        'json',
    ]}
    response = requests.post(endpoint, json=json_data)
    response=json.loads(response.text)
    return response

""" GET NFT NAME | IMAGE (API BASED) NEW ONE WILL BE BLOCKCHAIN BASED"""

"""ME API"""

def get_token_info(token_addy):
    try:
        response = requests.get(f'http://api-mainnet.magiceden.dev/v2/tokens/{token_addy}')
        response=json.loads(response.text)
        name=response['name']
        image=response['image']
        return name,image,True
    except:
        return None,None,False

"""SOLSCAN API"""

def get_alternative_token_info(token_addy):
    try:
        headers = {
            'authority': 'api.solscan.io',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                }

        params = {
            'address': token_addy,
        }
        response = requests.get('https://api.solscan.io/account', params=params, headers=headers)
        response=json.loads(response.text)['data']
        metadata=response['metadata']['data']
        name=metadata['name']
        image=metadata['uri']
        return name,image
    except Exception as E:
        return None,None

""" METHOD TO GRAB INFO WITH ME API | SOLSCAN API"""

def get_token_information(token_addy):
    name,image,status=get_token_info(token_addy)
    if not status:
        print('Trying alternative method')
        name,image=get_alternative_token_info(token_addy)
    if name and image:
        return name,image
    else:
        print('Nothing found.')
        return None,None

""" PRICE DETECTION OF TX LOG | BLOCKCHAIN BASED"""


def detect_price(log):
    lamport_scale= 0.000000001
    if log:
        nft_sell_info=json.loads(log.split('log:')[1].strip())
        if 'price' in nft_sell_info.keys():
            nft_price=round(nft_sell_info['price']*lamport_scale,3)
            return nft_price
    else:
        return None


""" CHECK OPERATION TYPE"""

"""This code could actually be simplified alot. Will update real soon."""

def check_signature_json(nft_signature,transaction_json,public_wallet):
    try:
        is_ME=False
        count_system=0
        count_mint=0
        is_listing=False
        nft_price=None
        if not transaction_json['result']['meta']['err']:
          for log in transaction_json['result']['meta']['logMessages']:
              if 'deposit'in log.lower() or 'buy' in log.lower() or 'executesale' in log.lower():
                  count_system+=1
              if 'M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K' in log:
                  is_ME=True
              if 'price' in log:
                  nft_price=detect_price(log)
              if 'SetAuthority' in log:
                  is_listing=True
              if 'MintE' in log or 'InitializeMint' in log or 'MintTo' in log or 'mint' in log or 'MintNft' in log:
                  count_mint+=1
                  
          nft_ownership_data=transaction_json['result']['meta']['postTokenBalances']
          nft_token_adress=nft_ownership_data[len(nft_ownership_data)-1]['mint']
          nft_owner=nft_ownership_data[len(nft_ownership_data)-1]['owner'] 
          nft_name,nft_image=get_token_information(nft_token_adress)
          
          if count_system>1:
              if nft_owner == public_wallet: 
                  if is_ME:
                      print(f'BUY operation Detected! with cost {nft_price} SOL on ME')
                      send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Buy')
                  else:
                      print(f'BUY operation Detected! with cost {nft_price} SOL on an alternative Marketplace')
                      send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Buy')
              else:
                  if is_ME:
                      print(f'SALE operation Detected! with cost {nft_price} SOL on ME')
                      send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Sale')
                  else:
                      print(f'SALE operation Detected! with cost {nft_price} SOL on an alternative Marketplace')
                      send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Sale')
  
          elif is_listing and count_mint <1:
              if price:
                  print(f'LIST operation Detected! with cost {nft_price} SOL on ME')
                  send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Listing')
              else:
                  print(f'Delist operation Detected!')
                  send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'Delist')
  
          elif is_listing and count_mint > 2:
              print(f'MINT operation Detected!')
              send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,'MINT')
          else:
              print('Not a interesting TX to explore.')
    except Exception as e:
        print(f'Not a interesting TX to explore. {[e]}')
        pass


""" MONITOR ADDRESS BLOCKCHAIN BASED"""

def monitor_address(address,delay):
    endpoint = 'https://api.mainnet-beta.solana.com'
    solana_client = Client(endpoint)
    checked=[]
    while True:
        try:
            result = solana_client.get_signatures_for_address(address)
            if 'result' in result:
                for number, item in enumerate(result['result'][:1], 1):
                    print(f"TX found with signature :[{item['signature']}]")
                    if item['signature'] not in checked:
                        transaction_json=tx_info(item['signature'],address)
                        checked.append(item['signature'])
                        check_signature_json(item['signature'],transaction_json,address) 
                    else:
                        print(f'No new TXs found for wallet : [{address}]')
            else:
                print(result)
                
            time.sleep(delay)
            
        except Exception as e:
            print(f"Exception [{e}] found.")
            pass


"""DISCORD IMPLEMENTATION"""



bot = commands.Bot(command_prefix='!', description="SOLANA WALLET TRACKER")
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching))
    print('My bot is ready')

monitoring_wallets=[]
@bot.event
async def on_message(message):
  if message.channel.id == 'INPUT_CHANNEL_ID_HERE' # Add Channel Id where you will add the wallets to monitor.
    msg = message.content
    try:
        msg=msg.split(':')
        wallet=msg[0].strip()
        user=msg[1].strip()
        if wallet not in wallet_identifier:
            webhook = DiscordWebhook(url=webhook_bot, content=f"Added {user}'s wallet {wallet} to monitor..")
            t = threading.Thread(target=monitor_address, args=(wallet,3,))
            t.start()
            wallet_identifier[wallet]=user
            monitoring_wallets.append(wallet)
            webhook.execute()
        else:
            webhook = DiscordWebhook(url=webhook_bot, content=f"Wallet {wallet} already running in monitor..")
            webhook.execute()
    except:
        pass

for wallet,user in wallet_identifier.items():
  t = threading.Thread(target=monitor_address, args=(wallet,3,))
  t.start()


bot.run('INPUT BOT_TOKEN_HERE')
