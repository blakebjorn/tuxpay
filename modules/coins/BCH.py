from typing import TYPE_CHECKING

from electroncash import cashaddr

from modules.coins.network import CoinNetwork
from modules.electrum_mods.functions import hash160_to_p2pkh, address_to_script, script_to_scripthash, hash_160

if TYPE_CHECKING:
    from modules.electrum_mods import PartialTransaction, BIP32Node


class _BitcoinCashMainnet(CoinNetwork):
    symbol = "BCH"
    name = "Bitcoin Cash"
    kraken = "BCHUSD"
    segwit = False
    address_format = "p2pkh"
    bip21_intent = ""

    SIGHASH_FLAG = 0x00000041
    TX_VERSION = 1

    TESTNET = False
    WIF_PREFIX = 0x80
    ADDRTYPE_P2PKH = 0
    ADDRTYPE_P2PKH_BITPAY = 28
    ADDRTYPE_P2SH = 5
    ADDRTYPE_P2SH_BITPAY = 40
    SEGWIT_HRP = "XX"
    CASHADDR_PREFIX = "bitcoincash"
    HEADERS_URL = "http://bitcoincash.com/files/blockchain_headers"  # Unused
    GENESIS = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"

    TITLE = 'Electron Cash'

    # Bitcoin Cash fork block specification
    BITCOIN_CASH_FORK_BLOCK_HEIGHT = 478559
    BITCOIN_CASH_FORK_BLOCK_HASH = "000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec"

    # Nov 13. 2017 HF to CW144 DAA height (height of last block mined on old DAA)
    CW144_HEIGHT = 504031

    # Note: this is not the Merkle root of the verification block itself , but a Merkle root of
    # all blockchain headers up until and including this block. To get this value you need to
    # connect to an ElectrumX server you trust and issue it a protocol command. This can be
    # done in the console as follows:
    #
    #    network.synchronous_get(("blockchain.block.header", [height, height]))
    #
    # Consult the ElectrumX documentation for more details.
    VERIFICATION_BLOCK_MERKLE_ROOT = "68077352cf309072547164625deb11e92bd379e759e87f3f9ac6e61d1532c536"
    VERIFICATION_BLOCK_HEIGHT = 661942

    # Version numbers for BIP32 extended keys
    # standard: xprv, xpub
    XPRV_HEADERS = {
        'standard': 0x0488ade4,
    }
    XPUB_HEADERS = {
        'standard': 0x0488b21e,
    }
    BIP44_COIN_TYPE = 145

    def make_address(self, xpub_node: 'BIP32Node' = None, account=0, index=0):
        assert isinstance(index, int) and index >= 0
        assert isinstance(account, int) and account >= 0
        xpub_node = xpub_node or self.xpub_node

        subkey = xpub_node.subkey_at_public_derivation(f"/{account}/{index}")
        pubkey_bytes = subkey.eckey.get_public_key_bytes(compressed=True)
        return cashaddr.encode_full(self.CASHADDR_PREFIX, cashaddr.PUBKEY_TYPE, hash_160(pubkey_bytes))

    def address_to_script(self, address: str):
        if address.startswith(self.CASHADDR_PREFIX):
            prefix, key_type, hash160 = cashaddr.decode(address)
            address = hash160_to_p2pkh(hash160, net=self)
            return address_to_script(address, net=self)
        else:
            return address_to_script(address, net=self)

    def address_to_scripthash(self, address):
        script = self.address_to_script(address)
        return script_to_scripthash(script)

    def estimate_tx_size(self, tx: 'PartialTransaction'):
        assert not tx.is_complete()
        return len(tx.serialize()) // 2


class _BitcoinCashTestnet(_BitcoinCashMainnet):
    symbol = "tBCH"
    name = "Bitcoin Cash (Testnet)"

    TESTNET = True
    WIF_PREFIX = 0xef
    ADDRTYPE_P2PKH = 111
    ADDRTYPE_P2PKH_BITPAY = 111  # Unsure
    ADDRTYPE_P2SH = 196
    ADDRTYPE_P2SH_BITPAY = 196  # Unsure
    CASHADDR_PREFIX = "bchtest"
    HEADERS_URL = "http://bitcoincash.com/files/testnet_headers"  # Unused
    GENESIS = "000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943"

    TITLE = 'Electron Cash Testnet'

    # Nov 13. 2017 HF to CW144 DAA height (height of last block mined on old DAA)
    CW144_HEIGHT = 1155875

    # Bitcoin Cash fork block specification
    BITCOIN_CASH_FORK_BLOCK_HEIGHT = 1155876
    BITCOIN_CASH_FORK_BLOCK_HASH = "00000000000e38fef93ed9582a7df43815d5c2ba9fd37ef70c9a0ea4a285b8f5"

    VERIFICATION_BLOCK_MERKLE_ROOT = "d97d670815829fddcf728fa2d29665de53e83609fd471b0716a49cde383fb888"
    VERIFICATION_BLOCK_HEIGHT = 1421482

    # Version numbers for BIP32 extended keys
    # standard: tprv, tpub
    XPRV_HEADERS = {
        'standard': 0x04358394,
    }
    XPUB_HEADERS = {
        'standard': 0x043587cf,
    }


BitcoinCashMainnet = _BitcoinCashMainnet()
BitcoinCashTestnet = _BitcoinCashTestnet()
