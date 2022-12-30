
""" All imports """

from libraries import *
from send_webhooks import send_hook


CONFIG=pd.read_csv('config.csv')
WALLETS_TO_MONITOR=pd.read_csv('wallets.csv')


""" Monitor Solana Adress """

def monitor_address(address:str,
                    delay:int):

    endpoint = 'https://api.mainnet-beta.solana.com'
    solana_client = Client(endpoint)
    while True:
        print(f"Monitoring wallet {address}..")
        try:
            result = solana_client.get_signatures_for_address(address)
            if 'result' in result:
                for last_tx in result['result'][:4]:
                    last_signature=last_tx['signature']
                    print(f"Tx found with signature : {last_signature}")
                    if not checked_transactions(last_signature):
                        transaction_json=tx_info(last_signature)
                        check_signature_json(last_signature,
                                            transaction_json,
                                            address) 
                    else:
                        print(f"No new TXs found for wallet : {address}")
            time.sleep(delay) 
        except Exception as e:
            print(f"Exception [{e}] found.")
            

""" Function which checks if last wallet tx has already been analyzed."""

def checked_transactions(last_signature:str):

    with open('checked_txs.csv', 'r') as fp:
                checked_txs = fp.read()
    if last_signature not in checked_txs:
        f = open('checked_txs.csv', 'a', newline="")
        writer = csv.writer(f)
        writer.writerow((last_signature, 'Checked'))
        f.close()
        return False
    else:
        return True

""" Function used to detect price """

def detect_price(log:str):

    lamport_scale= 0.000000001
    if log:
        nft_sell_info=json.loads(log.split('log:')[1].strip())
        if 'price' in nft_sell_info.keys():
            nft_price=round(nft_sell_info['price']*lamport_scale,3)
            return nft_price
    else:
        return None

""" Parsed last transaction"""

def tx_info(signature:str):

    print(f"Fetching info for tx : {[signature]}")
    rpc = 'https://api.mainnet-beta.solana.com'
    solana_client = Client(rpc)
    parsed_results=0
    while parsed_results<=0:
        try:
            parsed=solana_client.get_transaction(signature)
            parsed_results=len(parsed['result'])
            return parsed
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt.args)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc.args)
            
    
""" Get NFT information."""

def get_atts(mint_id:str):

    client = Client("http://api.mainnet-beta.solana.com")
    data = metadata.get_metadata(client, mint_id)['data']
    if 'name' in data.keys():
        nft_name=data['name']
    if 'seller_fee_basis_points' in data.keys():
        nft_royalties=data['seller_fee_basis_points']       
    if 'uri' in data.keys():
        nft_more_info=data['uri']
        r=requests.get(nft_more_info)
        parsed=r.json()
        if not nft_name:
            nft_name=parsed['name']
        if 'image' in parsed.keys():
            nft_image=parsed['image']
    return nft_name,nft_image,nft_royalties

""" Function to check TX Type"""

def check_signature_json(nft_signature:str,
                        transaction_json:dict,
                        public_wallet:str):

    count_mint,nft_price=0,None
    if not transaction_json['result']['meta']['err']:
        count=0
        list_count=0
        nft_ownership_data=transaction_json['result']['meta']['postTokenBalances']
        nft_token_adress=nft_ownership_data[len(nft_ownership_data)-1]['mint']
        nft_owner=nft_ownership_data[len(nft_ownership_data)-1]['owner'] 
        nft_name,nft_image,nft_royalties=get_atts(nft_token_adress)
        for log in transaction_json['result']['meta']['logMessages']:
            if any(word in log.lower() for word in ['deposit','buy','executesale']):
                count+=1
            if any(word in log.lower() for word in ['minte','initializemint','mintto','mint','mintnft']):
                count_mint+=1
            if 'price' in log:
                nft_price=detect_price(log)
            if any(word in log.lower() for word in ['cancelsell','setauthority']):
                list_count+=1
                if list_count==1:
                    mode='List'
                elif list_count==2:
                    mode='Delist'
        if count_mint > 1: 
            mode='mint'    
        if count > 1:
                if nft_owner == public_wallet:
                    mode='Buy'
                    print(f'Secondary Buy operation Detected! with cost {nft_price} SOL.') 
                else:
                    mode='Sale'
                    print(f'Secondary Sale operation Detected! with cost {nft_price} SOL.')
        print(f"{mode} operation detected.")            
        send_hook(public_wallet,nft_signature,nft_price,nft_name,nft_image,nft_royalties,mode)


"""Function to add wallets to csv"""

def check_wallet(wallet:str,
                 user:str):

    with open('wallets.csv', 'r') as fp:
        wallets = fp.read()
    if wallet not in wallets:
        f = open('wallets.csv', 'a', newline="")
        writer = csv.writer(f)
        writer.writerow((wallet, user))
        f.close()
        return False
    else:
        return True


for index, row in WALLETS_TO_MONITOR.iterrows():
    public_key,wallet_identifier=row['public_key'],row['wallet_identifier']

    t = threading.Thread(target=monitor_address, args=(public_key,3,))
    t.start()

bot = commands.Bot(command_prefix='!', description="Wallet Tracker.")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching))
    print('My bot is ready')


@bot.event
async def on_message(message):
  if message.channel.id == CHANNEL_ID_HERE_INT:
    msg = message.content
    try:
        msg=msg.split(':')
        wallet=msg[0].strip()
        user=msg[1].strip()
        if not check_wallet(wallet,user):
            print('New wallet added to monitor!')
            webhook = DiscordWebhook(url=CONFIG['wallet_adding_bot_url'].values[0], content=f"Added {user}'s wallet {wallet} to monitor..")
            t = threading.Thread(target=monitor_address, args=(wallet,3,))
            t.start()
            webhook.execute()
        else:
            webhook = DiscordWebhook(url=CONFIG['wallet_adding_bot_url'].values[0], content=f"Wallet {wallet} already running in monitor..")
            webhook.execute()
    except:
        pass

bot.run('BOT_TOKEN_HERE_STR')

