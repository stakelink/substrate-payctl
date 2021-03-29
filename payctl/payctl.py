from argparse import ArgumentParser, RawDescriptionHelpFormatter
from configparser import ConfigParser

from .utils import *


#
# cmd_list - 'list' subcommand handler.
#
def cmd_list(args, config):
    substrate = SubstrateInterface(
        url=get_config(args, config, 'rpcurl'),
        type_registry_preset=get_config(args, config, 'network')
    )

    current_era = substrate.query(
    module='Staking',
    storage_function='CurrentEra'
    )
    history_depth = substrate.query(
    module='Staking',
    storage_function='HistoryDepth'
    )

    current_era = current_era.value - 1

    depth = int(get_config(args, config, 'deptheras'))
    if depth is None:
        depth = 84

    #depth = min(history_depth.value, int(config['Defaults'].get('eradepth')))

    start = current_era - depth
    end = current_era

    eras_paymemt_info = get_eras_payment_info_filtered(
        substrate, start, end,
        accounts=get_included_accounts(substrate, args, config),
        unclaimed=args.unclaimed
    )

    for era in eras_paymemt_info:
        print("Era: %s" % era)
        for accountId in eras_paymemt_info[era]:
            if eras_paymemt_info[era][accountId]['claimed'] is True:
                msg = "claimed"
            else:
                msg = "unclaimed"

            account = ss58_encode(accountId, ss58_format=substrate.ss58_format)
            amount = eras_paymemt_info[era][accountId]['amount']

            print("\t %s => %s %s  (%s)" % (account, amount, substrate.token_symbol, msg))


#
# cmd_pay - 'pay' subcommand handler.
#
def cmd_pay(args, config):
    substrate = SubstrateInterface(
        url=get_config(args, config, 'rpcurl'),
        type_registry_preset=get_config(args, config, 'network')
    )

    current_era = substrate.query(
        module='Staking',
        storage_function='CurrentEra'
    )
    history_depth = substrate.query(
        module='Staking',
        storage_function='HistoryDepth'
    )

    current_era = current_era.value - 1

    depth = int(get_config(args, config, 'deptheras'))
    if depth is None:
        depth = 82
    #depth = min(history_depth.value, int(config['Defaults'].get('eradepth')))

    eras_paymemt_info = get_eras_payment_info_filtered(
        substrate, current_era - depth, current_era,
        accounts=get_included_accounts(substrate, args, config),
        unclaimed=True
    )

    if len(eras_paymemt_info) < int(get_config(args, config, 'mineras')):
        return

    keypair = get_keypair(args, config)

    payout_calls = []
    for era in eras_paymemt_info:
        for accountId in eras_paymemt_info[era]:
            payout_calls.append({
                'call_module': 'Staking',
                'call_function': 'payout_stakers',
                'call_args': {
                    'validator_stash': accountId,
                    'era': era,
                }                
            })


    call = substrate.compose_call(
        call_module='Utility',
        call_function='batch',
        call_params={
            'calls': payout_calls
        }
    )

    nonce = get_nonce(substrate, config['Defaults'].get('signingaccount'))

    signature_payload = substrate.generate_signature_payload(
        call=call,
        nonce=nonce
    )
    signature = keypair.sign(signature_payload)

    extrinsic = substrate.create_signed_extrinsic(
        call=call,
        keypair=keypair,
        nonce=nonce,
        signature=signature
    )

    result = substrate.submit_extrinsic(
        extrinsic=extrinsic
    )

    print(result)



def main():
    args_parser = ArgumentParser(prog='payctl')
    args_parser.add_argument("-c", "--config", help="read config from a file", default="/usr/local/etc/payctl/default.conf")

    args_parser.add_argument("-r", "--rpc-url", dest="rpcurl", help="substrate RPC Url")
    args_parser.add_argument("-n", "--network", dest="network", help="name of the network to connect")
    args_parser.add_argument("-d", "--depth-eras", dest="deptheras", help="depth of eras to include")

    args_subparsers = args_parser.add_subparsers(title="Commands", help='', dest="command")

    args_subparser_list = args_subparsers.add_parser("list", help="list rewards")
    args_subparser_list.add_argument("-u", "--unclaimed", help='show unclaimed only', action='store_true', default=False)
    args_subparser_list.add_argument("validators", nargs='*', help="", default=None)
    
    args_subparser_pay = args_subparsers.add_parser('pay', help="pay rewards")
    args_subparser_pay.add_argument("validators", nargs='*', help="", default=None)
    args_subparser_pay.add_argument("-m", "--min-eras", dest="mineras", help="minum eras pending to pay to proceed payment")
    args_subparser_pay.add_argument("-a", "--signing-account", dest="signingaccount", help="account used to sign requests")
    args_subparser_pay.add_argument("-n", "--signing-mnemonic", dest="signingmnemonic", help="mnemonic to generate the signing key")
    args_subparser_pay.add_argument("-s", "--signing-seed", dest="signingseed", help="seed to generate the signing key")
    args_subparser_pay.add_argument("-u", "--signing-uri", dest="signinguri", help="uri to generate the signing key")

    args = args_parser.parse_args()

    try:
        config = ConfigParser()
        config.read_file(open(args.config))
    except Exception as exc:
        print(f"Unable to read config: {str(exc)}")
        exit(0)

    if not args.command:
        args_parser.print_help()
        exit(1)

    if args.command == 'list':
        cmd_list(args, config)
    if args.command == 'pay':
        cmd_pay(args, config)


if __name__ == '__main__':
    main()
