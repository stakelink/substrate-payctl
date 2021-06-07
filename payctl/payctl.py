from argparse import ArgumentParser
from configparser import ConfigParser
from collections import OrderedDict
from substrateinterface import SubstrateInterface

from .utils import *

#
# cmd_list - 'list' subcommand handler.
#
def cmd_list(entries):
    entries = enrich_rewards(entries)

    for entry in entries:
        print(entry['validator'])

        if len(entry['rewards']) > 0:
            for era in entry['rewards'].keys():
                v = entry['network_data']['erasinfo'][era]['validators'][entry['validator']]
                s = entry['network_data']['api']

                # TODO: move to substrateutils
                formatted_amount = format_balance_to_symbol(v['rewards']['amount'], 3, s.token_decimals, s.token_symbol)
                msg = "claimed" if v['rewards']['claimed'] else "unclaimed"
                
                print(f"\t- {era} => {formatted_amount} ({msg})")
        else:
            print(f"\t- Not an active validator")

    return


#
# cmd_pay - 'pay' subcommand handler.
#
def cmd_pay(entries):
    entries = enrich_rewards(entries)
    entries = enrich_keypair(entries)
    batches = get_batches(entries)

    for k in batches:
        payout_calls = []
        for i in batches[k]['payouts']:
            s = batches[k]['api']

            for era in i['unclaimed_eras']:
                payout_calls.append({
                    'call_module': 'Staking',
                    'call_function': 'payout_stakers',
                    'call_args': {
                        'validator_stash': i['validator'],
                        'era': era,
                    }                
                })
        if len(payout_calls) > 0:
            call = s.compose_call(
                call_module='Utility',
                call_function='batch',
                call_params={
                    'calls': payout_calls
                }
            )

            payment_info = s.get_payment_info(call=call, keypair=batches[k]['keypair'])

            # TODO: move to substrateutils.
            account_info = get_account_info(s, batches[k]['signingaccount'])
            expected_fees = payment_info['partialFee']
            free_balance = account_info['data']['free']
            existential_deposit = get_existential_deposit(s)

            if (free_balance - expected_fees) < existential_deposit:
                print(f"Account with not enough funds. Needed {existential_deposit + expected_fees}, but got {free_balance}")
                continue


            signature_payload = s.generate_signature_payload(
                call=call,
                nonce=account_info['nonce']
            )
            signature = batches[k]['keypair'].sign(signature_payload)

            extrinsic = s.create_signed_extrinsic(
                call=call,
                keypair=batches[k]['keypair'],
                nonce=account_info['nonce'],
                signature=signature
            )
    
            extrinsic_receipt = s.submit_extrinsic(
                extrinsic=extrinsic,
                wait_for_inclusion=True
            )

            fees = extrinsic_receipt.total_fee_amount

            print(f"\t Extrinsic hash: {extrinsic_receipt.extrinsic_hash}")
            print(f"\t Block hash: {extrinsic_receipt.block_hash}")
            #print(f"\t Fee: {format_balance_to_symbol(s, fees)} ({fees})")
            print(f"\t Status: {'ok' if extrinsic_receipt.is_success else 'error'}")
            if not extrinsic_receipt.is_success:
                print(f"\t Error message: {extrinsic_receipt.error_message.get('docs')}")     

    return


def main():
    args_parser = ArgumentParser(prog='payctl')
    args_parser.add_argument("-c", "--config", help="read config from a file", default="/usr/local/etc/payctl/default.conf")

    args_parser.add_argument("-r", "--rpc-url", dest="rpcurl", help="Defines Substrate default RPC URL")
    args_parser.add_argument("-n", "--network", dest="network", help="Defines the default name of the network to connect")
    args_parser.add_argument("-d", "--depth-eras", dest="deptheras", help="Defines the default depth of eras to include")

    args_subparsers = args_parser.add_subparsers(title="Commands", help='', dest="command")

    args_subparser_list = args_subparsers.add_parser("list", help="list rewards")
    args_subparser_list.add_argument("-u", "--unclaimed", dest="only_unclaimed", help='Show unclaimed only', action='store_true', default=False)
    args_subparser_list.add_argument("validators", nargs='*', help="", default=None)
    
    args_subparser_pay = args_subparsers.add_parser('pay', help="pay rewards")
    args_subparser_pay.add_argument("validators", nargs='*', help="", default=None)
    args_subparser_pay.add_argument("-m", "--min-eras", dest="mineras", help="Minum eras pending to pay to proceed payment")
    args_subparser_pay.add_argument("-a", "--signing-account", dest="signingaccount", help="Account used to sign requests")
    args_subparser_pay.add_argument("-n", "--signing-mnemonic", dest="signingmnemonic", help="Mnemonic to generate the signing key")
    args_subparser_pay.add_argument("-s", "--signing-seed", dest="signingseed", help="Seed to generate the signing key")
    args_subparser_pay.add_argument("-u", "--signing-uri", dest="signinguri", help="Uri to generate the signing key")

    args = args_parser.parse_args()
    
    if not args.command:
        args_parser.print_help()
        exit(1)

    try:
        config = ConfigParser()
        config.read_file(open(args.config))
    except Exception as exc:
        print(f"Unable to read config: {str(exc)}")
        exit(0)

    entries = get_entries(args, config)

    if args.command == 'list':
        cmd_list(entries)
    if args.command == 'pay':
        cmd_pay(entries)


if __name__ == '__main__':
    main()
