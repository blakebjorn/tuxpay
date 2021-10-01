import hashlib
import json
import re
import sys
from pathlib import Path

from PyInquirer import prompt
from modules.electrum_mods.functions import BIP32Node
from mnemonic import Mnemonic
from mnemonic.mnemonic import ConfigurationError

from modules.config import get_app_secret
from modules.coins.BTC import BitcoinMainnet, BitcoinTestnet
from modules.coins.BCH import BitcoinCashMainnet, BitcoinCashTestnet
from modules.coins.DASH import DashMainnet, DashTestnet
from modules.coins.LTC import LitecoinMainnet, LitecoinTestnet
from modules.models import synchronous_engine, metadata, SeedPhrase, Payment, User
from modules.credentials import CredentialManager, generate_password_hash

get_app_secret()

conf_dir = Path("data")
conf_dir.mkdir(exist_ok=True)
xpub_file = conf_dir / ".xpubs.json"

engine = synchronous_engine()
metadata.create_all(bind=engine)
connection = engine.connect()


def question(**kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = 'prompt'
    name = kwargs['name']
    ret = prompt(kwargs)
    if not ret:
        sys.exit(0)
    return ret[name]


def get_user_seed():
    while True:
        phrase = question(type='input',
                          message="Enter your 12/18/24 word seed phrase to proceed")

        _seed = re.sub("\s+", " ", phrase)
        try:
            lang = Mnemonic.detect_language(_seed)
            if Mnemonic(language=lang).check(_seed):
                return _seed
        except ConfigurationError:
            pass
        print("Invalid seed phrase provided.")


def get_seed():
    while True:
        language = question(type="list",
                            message="Need to generate new seed phrase. Pick a language to begin",
                            choices=['english'] + [x for x in Mnemonic.list_languages() if x != 'english'] +
                                    ['none (I will provide my own)'])

        if language == 'none (I will provide my own)':
            return get_user_seed()
        else:
            words = question(type="list",
                             message="Generate 12 (exodus, etc) or 24 (coinomi, etc) word seed phrase?",
                             choices=['12', '24'])

            _seed = Mnemonic(language).generate(256 if words == '24' else 128)
            c = prompt(dict(type='confirm', name='confirm',
                            message="This is your 24 word seed. This will be used to generate ALL of your TuxPay wallets.\n"
                                    f"\n    {' '.join(_seed.split()[:12])}"
                                    f"\n    {' '.join(_seed.split()[12:])}\n\n"
                                    "Please write down a copy of this, it WILL NOT be saved. "
                                    "Failure to do so will render all of your received funds inaccessible. "
                                    "Do you understand?"))
            if c['confirm']:
                return _seed
            else:
                print("Exiting")
                sys.exit(0)


def get_passphrase():
    use_passphrase = question(type='confirm',
                              message="Use a passphrase for this seed? (The passphrase determines how to derive addresses from the seed - it does not encrypt or obfuscate your seed in any way)",
                              default=False)
    if use_passphrase:
        return get_pass('passphrase')
    return ""


def get_pass(name):
    while True:
        ret = prompt([dict(type="password",
                           name="password",
                           message=f"Enter {name}"),
                      dict(type="password",
                           name="confirmation",
                           message=f"Confirm {name}")
                      ])
        if 'confirmation' not in ret:
            sys.exit(0)
        if ret['password'] == ret['confirmation']:
            return ret['password']
        else:
            print(f"{name.title()}s do not match.")


def get_hot_wallet():
    use_hot_wallet = question(type='confirm',
                              message="Set this server up to operate as a hot wallet? "
                                      "(Seed phrase will be stored on the device)\n "
                                      "WARNING: This is a convenience feature that allows for transaction sending and "
                                      "automated wallet sweeping. While convenient, keeping your wallet seed on an "
                                      "internet-connected device is inherently risky and may lead to loss of funds.",
                              default=False)

    if use_hot_wallet:
        use_password = question(type='confirm',
                                message="Encrypt credentials? (You will need to enter a password to authorize transactions. "
                                        "Automated sweeping will be disabled)",
                                default=False)
        if use_password:
            return True, get_pass('password')
        return True, None
    return False, None


def get_existing_seed():
    result = connection.execute(SeedPhrase.select())
    return result.fetchone()


def register_seed_to_db(checksum):
    # Check if the seed has previously been registered
    ex_seed = get_existing_seed()
    if ex_seed and ex_seed['checksum'] == checksum:
        print("This seed phrase has been used before, existing configuration will be updated")
    else:
        if ex_seed:
            payments = connection.execute(Payment.select()).fetchone()
            if payments is not None:
                print("Error: There are existing payments generated in this database using a different seed phrase")
                print(
                    "Cannot add a 2nd seed phrase to an existing instance - please set up a fresh schema to proceed")
                sys.exit(0)
            else:
                res = question(type='confirm',
                               message="There is already a seed set up for this database which has not been used."
                                       " Delete the existing setup configuration and proceed?")
                if res:
                    d = connection.execute(SeedPhrase.delete())
                    print("Deleted", d)
                else:
                    sys.exit(0)

        connection.execute(SeedPhrase.insert().values(checksum=checksum))
        print("Seed phrase registered to DB")


def setup_user():
    existing_users = connection.execute(User.select()).fetchall()
    ret = question(type="confirm",
                   message="Set up an administrator account?")
    if ret:
        email = None
        while not email:
            email = question(type="input", message="Enter email address")
            if email in (x['email'] for x in existing_users):
                print(f"Email {email} already exists, please enter a new email")
                email = None

        password = generate_password_hash(get_pass("password"))
        connection.execute(User.insert().values(email=email, password=password))


def wallet_setup():
    seed_phrase = get_seed()
    lang = Mnemonic.detect_language(seed_phrase)
    mnemo = Mnemonic(language=lang)

    passphrase = get_passphrase()

    seed_binary = mnemo.to_seed(seed_phrase, passphrase=passphrase)
    seed_n_words = len(seed_phrase.split())
    seed_sha = hashlib.sha256(hashlib.sha256(seed_binary).digest()).hexdigest()

    register_seed_to_db(seed_sha)

    node = BIP32Node.from_rootseed(seed_binary, xtype='standard')

    coins = question(type='checkbox',
                     message="Which coins do you want to set up?",
                     choices=[
                         {'name': '[BTC] Bitcoin', 'checked': True, 'value': "BTC"},
                         {'name': '[BCH] Bitcoin Cash', 'checked': True, 'value': "BCH"},
                         {'name': '[DASH] Dash', 'checked': True, 'value': "DASH"},
                         {'name': '[LTC] Litecoin', 'checked': True, 'value': "LTC"},
                     ],
                     validate=lambda x: 'You must choose at least one currency.' if len(x) == 0 else True)

    xpub_out = {}
    for network in [BitcoinMainnet, BitcoinTestnet,
                    BitcoinCashMainnet, BitcoinCashTestnet,
                    DashMainnet, DashTestnet,
                    LitecoinMainnet, LitecoinTestnet]:
        if network.root_symbol not in coins:
            print(f"Skipping {network.name}")
            continue

        print(f"Setting up {network.name}")
        subkey = node.subkey_at_private_derivation(network.default_xpub_derivation_path)

        xpub_out[network.symbol] = {
            "derivation_path": network.default_xpub_derivation_path,
            "xpub": subkey.to_xpub(net=network),
        }

    print(f"Writing XPUB keys to {xpub_file.absolute()}")
    xpub_file.write_text(json.dumps(xpub_out, indent=2))

    hot_wallet, password = get_hot_wallet()

    CredentialManager.write_secrets(
        mnemonic=seed_phrase if hot_wallet else None,
        passphrase=passphrase if hot_wallet else None,
        language=lang,
        decryption_password=password
    )

    print_out = question(type='confirm',
                         message="Print selections to console in plain text for review? (WARNING: Some consoles may log output)",
                         default=False)
    if print_out:
        print(f"Mnemonic: {seed_phrase}")
        if passphrase:
            print(f"Passphrase: `{passphrase}`")
        else:
            print(f"Passphrase? NO")

        print(f"Hot Wallet? {'YES' if hot_wallet else 'NO'}")
        if hot_wallet and password:
            print(f"Hot Wallet Password: `{password}`")
        elif hot_wallet:
            print(f"Hot Wallet Password? NO")
        print("Enabled Currencies:")
        for symbol, data in xpub_out.items():
            print(f"  {symbol} - {data['derivation_path']} - {data['xpub']}")


if __name__ == "__main__":
    existing_seed = get_existing_seed()
    if existing_seed is None:
        wallet_setup()
    elif question(type='confirm', message="There is already a seed phrase set up - modify wallet settings?"):
        wallet_setup()

    setup_user()
    print("Setup complete - Exiting.")
