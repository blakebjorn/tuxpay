from modules.coins.network import CoinNetwork
from modules.helpers import read_json_gz


# https://github.com/akhavr/electrum-dash/blob/master/electrum_dash/constants.py
class _DashMainnet(CoinNetwork):
    symbol = "DASH"
    name = "Dash"
    kraken = "DASHUSD"
    segwit = False
    address_format = 'p2pkh'
    bip21_intent = "dash:"

    TESTNET = False
    WIF_PREFIX = 204
    ADDRTYPE_P2PKH = 76
    ADDRTYPE_P2SH = 16

    SEGWIT_HRP = "XX"
    GENESIS = "00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6"

    CHECKPOINTS = read_json_gz('checkpoints.json.gz', [])
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS = None

    XPRV_HEADERS = {
        'standard': 0x0488ade4,  # xprv
    }

    XPUB_HEADERS = {
        'standard': 0x0488b21e,  # xpub
    }

    DRKV_HEADER = 0x02fe52f8  # drkv
    DRKP_HEADER = 0x02fe52cc  # drkp
    BIP44_COIN_TYPE = 5
    DIP3_ACTIVATION_HEIGHT = 1028160


class _DashTestnet(_DashMainnet):
    symbol = "tDASH"
    name = "Dash (Testnet)"
    TESTNET = True

    WIF_PREFIX = 239
    ADDRTYPE_P2PKH = 140
    ADDRTYPE_P2SH = 19
    GENESIS = "00000bafbc94add76cb75e2ec92894837288a481e5c005f6563d91623bf8bc2c"

    XPRV_HEADERS = {
        'standard': 0x04358394,  # tprv
    }
    XPUB_HEADERS = {
        'standard': 0x043587cf,  # tpub
    }
    DRKV_HEADER = 0x3a8061a0  # DRKV
    DRKP_HEADER = 0x3a805837  # DRKP
    BIP44_COIN_TYPE = 1
    DIP3_ACTIVATION_HEIGHT = 7000

    PEER_DEFAULT_PORTS = {'t': 51001, 's': 51002}


DashMainnet = _DashMainnet()
DashTestnet = _DashTestnet()
