# Subtrate Validator Pay Control

Simple command line application to control the payouts of Substrate validators (Polkadot and Kusama among others).

## About 

[Substrate](https://substrate.dev/) is a modular framework that enables the creation of new blokchains by composing custom pre-build components, and it is the foundation on which some of the most important recent blockchains, such as [Polkadot](https://polkadot.network/) and [Kusama](https://kusama.network/), are built.

Substrate provides an [Staking](https://substrate.dev/rustdocs/v3.0.0/pallet_staking/index.html) module that enables network protection through a NPoS (Nominated Proof-of-Stake) algorithm, where validators and nominators may stake funds as a gurantee to protect the network and in return they receive a reward.

The paymemt of the reward to validators and nominators is not automatic, and must be triggered by activating the function **payout_stakers**. It can be done using a browser and the [Polkador.{js} app](https://polkadot.js.org/apps/), but this tool provides an alternative way to do it in the command line, which in turn facilitates the automation of recurring payments.

## Install

Clone the repository and install the package:

```
git clone http://github.com/stakelink/substrate-payctl
pip install substrate-payctl/
```

NOTE: pip install argument is ambiguous at it can refer to a python package or a local folder. Make sure to include the '/' at the end to avoid ambiguity.


## Usage

After installig the package the _payctl_ executable should be available on the system.

```
$ payctl
usage: payctl [-h] [-c CONFIG] [-n NETWORK] [-r RPCURL] [-d DEPTHERAS]
              {list,pay} ...

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        specify config file
  -n NETWORK, --network NETWORK
  -r RPCURL, --rpc-url RPCURL
  -d DEPTHERAS, --depth-eras DEPTHERAS

subcommands:
  {list,pay}
    list
    pay
```

### Configuration 

The config contains default parameters, and a list of validators used by default:

```
[Defaults]
RPCURL = wss://kusama-rpc.polkadot.io/
Network = kusama
DepthEras = 10
MinEras = 5
SigningAccount=
SigningMnemonic=

[GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E]
```

The payment functionalities requires to sign the extrinsic. _SigningAccount_ is used to specify the account used for the signature, while the secret to generate the key could be specified in tree ways; _SigningMnemonic_, _SigningSeed_ or _SigningUri_. 

That information can also be provided on the command-line:

```
$ payctl pay --help
usage: payctl pay [-h] [-m MINERAS] [-a SIGNINGACCOUNT] [-n SIGNINGMNEMONIC]
                  [-s SIGNINGSEED] [-u SIGNINGURI]
                  [validators [validators ...]]

positional arguments:
  validators            specify validator

optional arguments:
  -h, --help            show this help message and exit
  -m MINERAS, --min-eras MINERAS
  -a SIGNINGACCOUNT, --signing-account SIGNINGACCOUNT
  -n SIGNINGMNEMONIC, --signing-mnemonic SIGNINGMNEMONIC
  -s SIGNINGSEED, --signing-seed SIGNINGSEED
  -u SIGNINGURI, --signing-uri SIGNINGURI
```

Important security considerations:

1. Signing information must be secret. Be careful on not exposing the configuration file if it contains signing information.
2. Use accounts with limited balance to sign petitions in order to minimize the impact of secret's leak.


### Examples

List rewards for default validators (NOTE: execution may take some time):

```
$ payctl list
Era: 2020
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.321933155324 KSM  (claimed)
Era: 2021
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.646077588588 KSM  (claimed)
Era: 2022
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.965218253805 KSM  (claimed)
Era: 2023
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.804815899715 KSM  (claimed)
Era: 2024
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.645752264159 KSM  (claimed)
Era: 2025
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 1.291473497890 KSM  (claimed)
Era: 2026
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.643756878971 KSM  (claimed)
Era: 2027
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.323847362646 KSM  (claimed)
Era: 2028
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.160875886681 KSM  (claimed)
Era: 2029
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.803195226697 KSM  (claimed)
Era: 2030
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 1.445198542873 KSM  (claimed)

```

List rewards for default validators including the last 30 eras:

```
$ payctl -d 30 list
Era: 2000
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.636226339558 KSM  (claimed)
Era: 2001
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.951997041045 KSM  (claimed)

	 ...

Era: 2029
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 0.803195226697 KSM  (claimed)
Era: 2030
	 GetZUSLFAaKorkQU8R67mA3mC15EpLRvk8199AB5DLbnb2E => 1.445198542873 KSM  (claimed)
```

List rewards for an specific validator:

```
$ payctl list DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5
Era: 2020
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.643866310648 KSM  (claimed)
Era: 2021
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.161519397147 KSM  (claimed)

	 ...

Era: 2029
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.803195226697 KSM  (unclaimed)
Era: 2030
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.802888079374 KSM  (unclaimed)
```

List **only pending** rewards for an specific validator:

```
$ payctl list DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 --unclaimed
Era: 2027
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.971542087938 KSM  (unclaimed)
Era: 2028
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.643503546725 KSM  (unclaimed)
Era: 2029
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.803195226697 KSM  (unclaimed)
Era: 2030
	 DSA55HQ9uGHE5MyMouE8Geasi2tsDcu3oHR4aFkJ3VBjZG5 => 0.802888079374 KSM  (unclaimed)
```

Pay rewards for the default validators:

```
$payctl pay
```

Pay rewards for the default validators only if there are more than 4 eras pending:

```
$payctl pay -m 4
```