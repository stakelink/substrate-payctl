from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.utils.ss58 import ss58_encode, ss58_decode

#
# get_config - Get a default and validator specific config elements from args and config.
#
def get_config(args, config, key, section='Defaults'):
    if vars(args)[key] is not None:
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
                eras_rewards_point[era]['individual'][reward_points_item['col1']] = reward_points_item['col2']
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
# get_eras_payment_info - Combine information from ErasRewardPoints and ErasValidatorReward for given
#                         range of eras to repor the amount of per validator instead of era points.
#
def get_eras_payment_info(substrate, start, end):
    eras_rewards_point = get_eras_rewards_point(substrate, start, end)
    eras_validator_rewards = get_eras_validator_rewards(substrate, start, end)

    eras_payment_info = {}
    for era in list(set(eras_rewards_point.keys()) & set(eras_validator_rewards.keys())):
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
def get_eras_payment_info_filtered(substrate, start, end, accounts=[], unclaimed=False):
    eras_paymemt_info_filtered = {}

    eras_paymemt_info = get_eras_payment_info(substrate, start, end)
    accounts_ledger = get_accounts_ledger(substrate, accounts)

    for era in eras_paymemt_info:
        for accountId in accounts:
            if accountId in eras_paymemt_info[era]:
                if era in accounts_ledger[accountId]['claimedRewards']:
                    if unclaimed == True:
                        continue
                    claimed = True
                else:
                    claimed = False

                if era not in eras_paymemt_info_filtered:
                    eras_paymemt_info_filtered[era] = {}

                eras_paymemt_info_filtered[era][accountId] = {}

                amount = eras_paymemt_info[era][accountId] / (10**substrate.token_decimals)

                eras_paymemt_info_filtered[era][accountId]['claimed'] = claimed
                eras_paymemt_info_filtered[era][accountId]['amount'] = amount

    return(eras_paymemt_info_filtered)


#
# get_included_accounts - Get the list (for the filtering) of included accounts from the args and config.
#
def get_included_accounts(substrate, args, config):
    included_accounts = []

    if len(args.validators) != 0:
        for validator in args.validators:
            included_accounts.append('0x' + ss58_decode(validator, valid_ss58_format=substrate.ss58_format))
    else:
        for section in config.sections():
            if section == 'Defaults':
                continue
            included_accounts.append('0x' + ss58_decode(section, valid_ss58_format=substrate.ss58_format))

    return(included_accounts)


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
    enabled_signing_methods = config['Defaults'].keys() & {'signingseed', 'signingmnemonic', 'signinguri'}

    if (len(enabled_signing_methods) != 1):
        return None

    signing_method = list(enabled_signing_methods)[0]

    if signing_method == 'signingseed':
        keypair = Keypair.create_from_seed(config['Defaults'].get('signingseed'))
    if signing_method == 'signingmnemonic':
        keypair = Keypair.create_from_mnemonic(config['Defaults'].get('signingmnemonic'))
    if signing_method == 'signinguri':
        keypair = Keypair.create_from_uri(config['Defaults'].get('signinguri'))

    return keypair

#
# get_nonce - Get the next nonce to be used on a signature for a given account.
#
def get_nonce(substrate, account):
    account_info = substrate.query(
        module='System',
        storage_function='Account',
        params=[account]
    )

    return account_info.value['nonce']