from modules.coins.network import CoinNetwork
from modules.helpers import read_json


class _LitecoinMainnet(CoinNetwork):
    symbol = "LTC"
    name = "Litecoin"
    kraken = "XLTCZUSD"
    segwit = True
    bip21_intent = "litecoin:"

    TESTNET = False
    WIF_PREFIX = 0x80
    ADDRTYPE_P2PKH = 48
    ADDRTYPE_P2SH = 50
    SEGWIT_HRP = "ltc"
    GENESIS = "12a765e31ffd4059bada1e25190f6e98c99d9714d334efa41a195a7e7e04bfe2"

    CHECKPOINTS = read_json('checkpoints.json', [])
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS = 497000

    XPRV_HEADERS = {
        'standard': 0x0488ade4,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh': 0x0295b005,  # Yprv
        'p2wpkh': 0x04b2430c,  # zprv
        'p2wsh': 0x02aa7a99,  # Zprv
    }
    XPUB_HEADERS = {
        'standard': 0x0488b21e,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh': 0x0295b43f,  # Ypub
        'p2wpkh': 0x04b24746,  # zpub
        'p2wsh': 0x02aa7ed3,  # Zpub
    }
    BIP44_COIN_TYPE = 2
    LN_REALM_BYTE = 0
    LN_DNS_SEEDS = [
        'ltc.nodes.lightning.directory.',
    ]


class _LitecoinTestnet(_LitecoinMainnet):
    symbol = "tLTC"
    name = "Litecoin (Testnet)"

    TESTNET = True
    WIF_PREFIX = 0xbf
    ADDRTYPE_P2PKH = 111
    ADDRTYPE_P2SH = 58
    SEGWIT_HRP = "tltc"
    GENESIS = "4966625a4b2851d9fdee139e56211a0d88575f59ed816ff5e6a63deb4e3e29a0"

    XPRV_HEADERS = {
        'standard': 0x04358394,  # tprv
        'p2wpkh-p2sh': 0x044a4e28,  # uprv
        'p2wsh-p2sh': 0x024285b5,  # Uprv
        'p2wpkh': 0x045f18bc,  # vprv
        'p2wsh': 0x02575048,  # Vprv
    }
    XPUB_HEADERS = {
        'standard': 0x043587cf,  # tpub
        'p2wpkh-p2sh': 0x044a5262,  # upub
        'p2wsh-p2sh': 0x024289ef,  # Upub
        'p2wpkh': 0x045f1cf6,  # vpub
        'p2wsh': 0x02575483,  # Vpub
    }
    BIP44_COIN_TYPE = 1

    PEER_DEFAULT_PORTS = {'t': 51001, 's': 51002}


LitecoinMainnet = _LitecoinMainnet()
LitecoinTestnet = _LitecoinTestnet()
