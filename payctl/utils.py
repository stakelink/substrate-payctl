from substrateinterface import Keypair
from substrateutils import SubstrateUtils
from copy import copy

#
# get_entries -
#
def get_entries(args, config):
    entries = []

    vargs = vars(args)

    for section in config:
        if section == 'DEFAULT':
            continue

        entry = {}
        for k in config[section].keys():
            entry[k] = config[section].get(k)

        for k in vargs:
            if vargs[k] is not None:
                entry[k] = vargs[k]            

        entry['validator'] = section
        del entry['config']
        del entry['command']

        entries.append(entry)

    return entries


#
# get_networks -
#
def get_networks(entries):
    networks = {}

    for entry in entries:
        if (entry['network'],entry['rpcurl']) not in networks:
            networks[(entry['network'],entry['rpcurl'])] = {}
            networks[(entry['network'],entry['rpcurl'])]['deptheras'] = entry['deptheras']
        else:
            if entry['mineras'] > networks[(entry['network'],entry['rpcurl'])]['deptheras']:
                networks[(entry['network'],entry['rpcurl'])]['deptheras'] = entry['deptheras']

    return networks


def get_batches(entries):
    batches = {}

    for entry in entries:
        if len(entry['rewards']) > 0 and len(entry['unclaimed_eras']) > int(entry['mineras']):
            batch_key = (entry['network'], entry['rpcurl'], entry['keypair'].ss58_address)
            if batch_key not in batches.keys():
                batches[batch_key] = {
                    'payouts': []
                }
            batches[batch_key]['payouts'].append(entry)
            batches[batch_key]['api'] = entry['network_data']['api']
            batches[batch_key]['signingaccount'] = entry['signingaccount']
            batches[batch_key]['keypair'] = entry['keypair']

    return batches



#
# get_rewards -
#
def enrich_rewards(entries):
    networks = get_networks(entries)
    
    for k in networks:
        network = networks[k]
        s = SubstrateUtils(
            type_registry_preset=get_type_preset(k[0]),
            url=k[1],
            cache_ttl = 3600,
            cache_storage = 'data.cache',
            cache_storage_sync_timer=30,
        )

        activeEra = s.Query('Staking', 'ActiveEra')['index']
        filters={'eras': range(activeEra - int(network['deptheras']), activeEra)}

        network['erasinfo'] = s.ErasInfo(filters)
        network['api'] = s
        network['activeera'] = activeEra

    for entry in entries:
        entry['network_data'] = networks[(entry['network'], entry['rpcurl'])]
        entry['rewards'] = {}
        entry['unclaimed_eras'] = []
        for era in range(activeEra - int(entry['deptheras']), activeEra):
            if entry['validator'] in entry['network_data']['erasinfo'][era]['validators']:
                v = entry['network_data']['erasinfo'][era]['validators'][entry['validator']]
                entry['rewards'][era] = v['rewards']
                if entry['rewards'][era]['claimed'] is False:
                    entry['unclaimed_eras'].append(era)

    return entries


#
# enrich_keypair -
#
def enrich_keypair(entries):
    for entry in entries:
        entry['keypair'] = get_keypair(entry)
    return entries



#
# get_keypair - Generate a Keypair from args and config.
#
def get_keypair(entry):
    signingseed = entry['signingseed'] if 'signingseed' in entry.keys() else None
    signingmnemonic = entry['signingmnemonic'] if 'signingmnemonic' in entry.keys() else None
    signinguri = entry['signinguri'] if 'signinguri' in entry.keys() else None
    
    ss58_format = get_ss58_address_format(entry['network'])

    if signingseed is not None:
        keypair = Keypair.create_from_seed(signingseed, ss58_format)
    elif signingmnemonic is not None:
        keypair = Keypair.create_from_mnemonic(signingmnemonic, ss58_format)
    elif signinguri is not None:
        keypair = Keypair.create_from_uri(signinguri, ss58_format)
    else:
        keypair = None

    return keypair


#
# get_account_info - Get the account info, including nonce and balance, for a given account.
#
def get_account_info(substrate, account):
    account_info = substrate.query(
        module='System',
        storage_function='Account',
        params=[account]
    )

    return account_info.value


#
# get_existential_deposit - Get the existential_deposit, the minimum amount required to keep an account open.
#
def get_existential_deposit(substrate):
    constants = substrate.get_metadata_constants()
    existential_deposit = 0

    for c in constants:
        if c['constant_name'] == 'ExistentialDeposit':
            existential_deposit = c.get('constant_value', 0)
    
    return existential_deposit


#
# format_balance_to_symbol - Formats a balance in the base decimals of the chain
#
def format_balance_to_symbol(amount, show_decimals=0, token_decimals=0, token_symbol=""):
    formatted = amount / 10 ** token_decimals
    formatted = "{:.{}f}".format(formatted, show_decimals)

    # expected format -> 5.780520362127 KSM
    return f"{formatted} {token_symbol}"


#
# get_ss58_address_format - Gets the SS58 address format depending on the network
# 
def get_ss58_address_format(network):
    network = network.lower()

    if network == "polkadot": return 0
    if network == "sr25519": return 1
    if network == "kusama": return 2
    if network == "ed25519": return 3
    if network == "katalchain": return 4
    if network == "plasm": return 5
    if network == "bifrost": return 6
    if network == "edgeware": return 7
    if network == "karura": return 8
    if network == "reynolds": return 9
    if network == "acala": return 10
    if network == "laminar": return 11
    if network == "polymath": return 12
    if network == "substratee": return 13
    if network == "totem": return 14
    if network == "synesthesia": return 15
    if network == "kulupu": return 16
    if network == "dark": return 17
    if network == "darwinia": return 18
    if network == "geek": return 19
    if network == "stafi": return 20
    if network == "dock-testnet": return 21
    if network == "dock-mainnet": return 22
    if network == "shift": return 23
    if network == "zero": return 24
    if network == "alphaville": return 25
    if network == "jupiter": return 26
    if network == "subsocial": return 28
    if network == "cord": return 29
    if network == "phala": return 30
    if network == "litentry": return 31
    if network == "robonomics": return 32
    if network == "datahighway": return 33
    if network == "ares": return 34
    if network == "vln": return 35
    if network == "centrifuge": return 36
    if network == "nodle": return 37
    if network == "kilt": return 38
    if network == "poli": return 41
    if network == "substrate": return 42
    if network == "westend": return 42
    if network == "amber": return 42
    if network == "secp256k1": return 43
    if network == "chainx": return 44
    if network == "uniarts": return 45
    if network == "reserved46": return 46
    if network == "reserved47": return 47
    if network == "neatcoin": return 48
    if network == "hydradx": return 63
    if network == "aventus": return 65
    if network == "crust": return 66
    if network == "equilibrium": return 67
    if network == "sora": return 69
    if network == "social-network": return 252
        
    return 42

#
# get_type_preset - Gets the type preset for the network
# 
def get_type_preset(network):
    supported_networks = [
        "polkadot",
        "kusama",
        "rococo",
        "westend",
        "statemine",
        "statemint",
    ]

    if network in supported_networks:
        return network
    else:
        return "default"
