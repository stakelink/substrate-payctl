from substrateinterface import Keypair

#
# get_config - Get a default and validator specific config elements from args and config.
#
def get_config(args, config, key, section='Defaults'):
    if vars(args).get(key) is not None:
        return vars(args)[key]

    if config[section].get(key) is not None:
        return config[section].get(key)

    return config['Defaults'].get(key)


#
# get_eras_rewards_point - Collect the ErasRewardPoints (total and invididual) for a given range of eras.
#
def get_eras_rewards_point(substrate, start, end):
    eras_rewards_point = {}

    for era in range(start, end):
        reward_points = substrate.query(
            module='Staking',
            storage_function='ErasRewardPoints',
            params=[era]
        )

        try:
            eras_rewards_point[era] = {}
            eras_rewards_point[era]['total'] = reward_points.value['total']
            eras_rewards_point[era]['individual'] = {}

            for reward_points_item in reward_points.value['individual']:
                eras_rewards_point[era]['individual'][reward_points_item[0]] = reward_points_item[1]
        except:
            continue

    return eras_rewards_point


#
# get_eras_validator_rewards - Collect the ErasValidatorReward for a given range of eras.
#
def get_eras_validator_rewards(substrate, start, end):
    eras_validator_rewards = {}

    for era in range(start, end):
        validator_rewards = substrate.query(
            module='Staking',
            storage_function='ErasValidatorReward',
            params=[era]
        )

        try:
            eras_validator_rewards[era] = validator_rewards.value
        except:
            continue

    return eras_validator_rewards

#
# get_eras_claims - Collect the ClaimedRewards for a given range of eras.
#
def get_eras_claims(substrate, start, end):
    eras_claims = {}

    for era in range(start, end):
        claims = substrate.query_map(
            module='Staking',
            storage_function='ClaimedRewards',
            params=[era]
        )

        # Extract the list of validators who claimed a reward in this era
        validators = list(map(lambda x: x[0].value, claims))

        eras_claims[era] = validators

    return eras_claims


#
# get_eras_payment_info - Combine information from ErasRewardPoints and ErasValidatorReward for given
#                         range of eras to repor the amount of per validator instead of era points.
#
def get_eras_payment_info(substrate, start, end):
    eras_rewards_point = get_eras_rewards_point(substrate, start, end)
    eras_validator_rewards = get_eras_validator_rewards(substrate, start, end)

    eras_payment_info = {}

    # era indexes with rewards points and validator rewards
    eras = list(set(eras_rewards_point.keys()) & set(eras_validator_rewards.keys()))

    for era in eras:
        total_points = eras_rewards_point[era]['total']

        for validatorId in eras_rewards_point[era]['individual']:
            total_reward = eras_validator_rewards[era]
            eras_rewards_point[era]['individual'][validatorId] *= (total_reward/total_points)

        eras_payment_info[era] = eras_rewards_point[era]['individual']

    return eras_payment_info

#
# get_eras_payment_info_filtered - Similar than get_eras_payment_info but applying some filters;
#                                  1 . Include only eras containing given acconts.
#                                  2 . Include only eras containing unclaimed rewards.
#
#                                  NOTE: The returned structure is slighly different than
#                                        get_eras_payment_info
#
def get_eras_payment_info_filtered(substrate, start, end, accounts=[], only_unclaimed=False):
    eras_payment_info_filtered = {}

    eras_payment_info = get_eras_payment_info(substrate, start, end)
    # get_accounts_ledger relies on a deprecated API that may stop working at some point
    accounts_ledger = get_accounts_ledger(substrate, accounts)
    # get_eras_claims replaces the previous call with a newer API
    claims = get_eras_claims(substrate, start, end)

    for era in eras_payment_info:
        for accountId in accounts:
            if accountId in eras_payment_info[era]:
                if era in accounts_ledger[accountId]['legacy_claimed_rewards'] or accountId in claims[era]:
                    claimed = True
                else:
                    claimed = False

                # if we only want the unclaimed rewards, skip
                if claimed and only_unclaimed:
                    continue

                if era not in eras_payment_info_filtered:
                    eras_payment_info_filtered[era] = {}

                eras_payment_info_filtered[era][accountId] = {}

                amount = eras_payment_info[era][accountId] / (10**substrate.token_decimals)

                eras_payment_info_filtered[era][accountId]['claimed'] = claimed
                eras_payment_info_filtered[era][accountId]['amount'] = amount

    return eras_payment_info_filtered


#
# get_included_accounts - Get the list (for the filtering) of included accounts from the args or config.
#
def get_included_accounts(args, config):
    if len(args.validators) != 0:
        return [validator for validator in args.validators]

    return [section for section in config.sections() if section != "Defaults"]



#
# get_accounts_ledger - Collect the Ledger for a given list of accounts.
#
def get_accounts_ledger(substrate, accounts):
    accounts_ledger = {}

    for account in accounts:
        try:
            controller_account = substrate.query(
                module='Staking',
                storage_function='Bonded',
                params=[accounts[0]]
            )

            ledger = substrate.query(
                module='Staking',
                storage_function='Ledger',
                params=[controller_account.value]
            )

            accounts_ledger[account] = ledger.value
        except:
            continue

    return accounts_ledger


#
# get_keypair - Generate a Keypair from args and config.
#
def get_keypair(args, config):
    signingseed = get_config(args, config, 'signingseed')
    signingmnemonic = get_config(args, config, 'signingmnemonic')
    signinguri = get_config(args, config, 'signinguri')
    
    ss58_format = get_ss58_address_format(get_config(args, config, 'network'))

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
def format_balance_to_symbol(substrate, amount, amount_decimals=0):
    formatted = amount / 10 ** (substrate.token_decimals - amount_decimals)
    formatted = "{:.{}f}".format(formatted, substrate.token_decimals)

    # expected format -> 5.780520362127 KSM
    return f"{formatted} {substrate.token_symbol}"


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
