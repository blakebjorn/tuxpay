import unittest
from electroncash import cashaddr
from modules.electrum_mods.functions import BIP32Node, pubkey_to_address, hash_160
from mnemonic import Mnemonic
from modules.coins import ALL_COINS

SEED_TEST_CASES = {
    "spanish": {
        "phrase": "talar sermo\u0301n rodilla hallar lejano pirata curva toldo gigante nicho aran\u0303a taman\u0303o",
        "seed_hex": "4e14a46c498c1df983311076f2d8196d3bb4720bc7d5dcc353472557226a0c51e92bbb481b1ebfddccb832819395d3f5a0fae492351cbe65aed4b1d4ebcbb3da",
        "passphrase": "",
        "symbol": "BTC",
        "xpub_derivation": "84h/0h/0h",
        "xpriv": "xprv9zTqmWRUS9TVbiTYUYe3UfxiG4HotFyEWHDwSrT75mKnKNe3Fii7KbA9n4mkKwMCCgkPxu2Jrcz91y7PgXWaRJPTN2VPD3Hgh9UhDWpYmpW",
        "xpub": "xpub6DTCB1xNGX1npCY1aaB3qouSp68JHih5sW9YFErie6rmCAyBoG2MsPUddL9hWe2PoWsK25LmxYiDNFLfgCWDo4d2x9aSYGzcGUs8umFK7wm",
        "account": 5,
        "index": 17,
        "address": "bc1qeepyu6th28fdhusaeck7t7eju5easfr2hx62s7"
    },
    "spanish_pass": {
        "phrase": "talar sermo\u0301n rodilla hallar lejano pirata curva toldo gigante nicho aran\u0303a taman\u0303o",
        "seed_hex": "cc5c365f81fb155a673a489908c0469dec136695acc1874e5033376d5effc6d65b7ab77a7d5fd3c23d2a4f367fd1cb2719d8a14ea9c4b2b9319c33cd6a8a1b56",
        "passphrase": "talar",
        "symbol": "BTC",
        "xpub_derivation": "84h/0h/0h",
        "xpriv": "xprv9yq39NaKu5UKawTWWiAjzwPKjXGev62GqxhwqGU4SXtZ3rpLPk7vunADwpbpvvVPSRA8tnjXnme6qURpcTk4zaSAj3oWQc37Cx6inf1vYhq",
        "xpub": "xpub6CpPYt7DjT2coRXycjhkN5L4HZ79KYk8DBdYdesfzsRXvf9UwHSBTaUho5gPApwxVcHMP8yBrNFc4bhADpmRauRKsRGrZiE6uwjLpt8uU92",
        "account": 10,
        "index": 12,
        "address": "bc1qj6kttuur0juj2fj0f9yj8hclsjzrz57e359n08"
    },
    "english": {
        "phrase": "tomato chief text deal party refuse focus divert use fork hunt kite",
        "seed_hex": "4f122f73fef3b8374796086b6aff15ed71afb190ca9e7ba706d5794bffc12f899bbdddb7140a3999c07b754642ecf0248a22d206168491e8e50ec0f630634927",
        "passphrase": "",
        "symbol": "BTC",
        "xpub_derivation": "84h/0h/0h",
        "xpriv": "xprv9yw6XAhL7arrdvKe1gh2xipBaKGVsuzTuxv7tvqriZnC3ESSysbYFTpd33SLpc99SGcvcCNwwxLVihRQWK2q9CySe3NcKBasGN7r643CsJF",
        "xpub": "xpub6CvSvgEDwxR9rQQ77iE3Krkv8M6zHNiKHBqihKFUGuKAv2mbXQunoG96tHfhdjLHgag1w6eKmdEKF4j4R7PzsPoEXpkT2caU8UQq2NqkfRd",
        "account": 10,
        "index": 6,
        "address": "bc1q27w8n5mt03c0d05mwm5w6jymtwz2025qgrc7pm"
    },
    "english_pass": {
        "phrase": "tomato chief text deal party refuse focus divert use fork hunt kite",
        "seed_hex": "0c63f5cd9bdc86ffe0b2e20450da150d4599a63961783b6a629c3ff6a9b9ad4cc3f7dac35afaa0115acfb57fdbe4e55898878755c08baed2976babca553b4e70",
        "passphrase": "kite",
        "symbol": "tBCH",
        "xpub_derivation": "44h/1h/0h",
        "xpriv": "tprv8ggt24CXDaSND5RvtkbdvEAxDNbYFhomvGN8aGpbfLCzjfbuX21WbtVWP5KHNRntABvsHGmdiCTDYAMSdoBKvBMtVpGLN487C67aoRqiEKh",
        "xpub": "tpubDDNvAUEmMx836YTinQGEKdq4nQ7UR2zgVZxurnru5c1Pa9rg9Qq6nP7NZE6mBeFti16STBNhrXMwuMXWSayh44LjLxzYjMLRxsMYcaqTjpY",
        "account": 18,
        "index": 6,
        "address": "bchtest:qrp6p7xwvvhm3jtasaeqzq67rw5xqveu3ch99up839"
    },
    "japanese": {
        "phrase": "\u304f\u3099\u3063\u3059\u308a\u3000\u3051\u3093\u3089\u3093\u3000\u3044\u3078\u3093\u3000\u305d\u3080\u304f\u3000\u3044\u304a\u3093\u3000\u305b\u3044\u3088\u3046\u3000\u304f\u3089\u3078\u3099\u308b\u3000\u3053\u305b\u3099\u3093\u3000\u3066\u307f\u3057\u3099\u304b\u3000\u3064\u3044\u304b\u3000\u3044\u306a\u3044\u3000\u3055\u3068\u3057",
        "seed_hex": "b387b750a9e845df01f615b2dd5998d78b5b2502547a7bf4e0ff00da8e34bf31d577c552bbebf1f4c2b11fd0a8ec69bcd94e93b82b69d3e8bafe45aba31e8e7f",
        "passphrase": "",
        "symbol": "tBTC",
        "xpub_derivation": "84h/1h/0h",
        "xpriv": "tprv8g9Dtn9Yun7MrxYwVV712ue4n3KANMNiy8v36k1J93JvWTZTytEmFouZqWYCwbCSdCkugoBXG3jnWNut6qCzYUohxu5e2Z7dqBGeTCZH1Wo",
        "xpub": "tpubDCqG3CBo49o2kRajP8mbSKJBM4q6XgZdYSWpPG3bZK7KLwpEcH4MSJXS1ep7Zz9ieJyYKD8exitGdNshP8MJmCzaXu62jU8e8AcPv6G4cho",
        "account": 5,
        "index": 8,
        "address": "tb1q6nzmpxfwaem3yurv06y93h9amledp2u2ymrsxc"
    },
    "japanese_pass": {
        "phrase": "\u304f\u3099\u3063\u3059\u308a\u3000\u3051\u3093\u3089\u3093\u3000\u3044\u3078\u3093\u3000\u305d\u3080\u304f\u3000\u3044\u304a\u3093\u3000\u305b\u3044\u3088\u3046\u3000\u304f\u3089\u3078\u3099\u308b\u3000\u3053\u305b\u3099\u3093\u3000\u3066\u307f\u3057\u3099\u304b\u3000\u3064\u3044\u304b\u3000\u3044\u306a\u3044\u3000\u3055\u3068\u3057",
        "seed_hex": "fb32c582cfee302cd5ab4d32d00bfa9bb429d29d75c2698f4650bb334ee9ab0969cad688f28e87c8359280b9decd5e668cad15bb6de38206dad48a4f2c0cfb4f",
        "passphrase": "\u3064\u3044\u304b",
        "symbol": "tBCH",
        "xpub_derivation": "44h/1h/0h",
        "xpriv": "tprv8gvAn9k4zLJAKECrEiwL9tCxQcB1DkiQELHdUuGCyR4tHeN9ZdkiPfv73BR8zHDh2eWwGg39bK7dncCExbiHCXnQDKRsGZMcqmQ9bFZ1xpb",
        "xpub": "tpubDDcCvZnK8hyqChEe8NbvZHs4ydgwP5uJodtQmRJWPgsH88cvC2aJaAXyDJXXEnPuWmq4LYxsLgZ47VwARUdt8MQymiXdC9GypWtuvhU6d3F",
        "account": 3,
        "index": 3,
        "address": "bchtest:qqhtk7zcd3l449d6d9033t6mrsswuvm60gl793r7s5"
    },
    "french": {
        "phrase": "laitier inutile atelier aubaine opprimer jeudi laisser serein affecter fatigue ve\u0301ne\u0301rer imbiber",
        "seed_hex": "80f5b168dbb73bee9d8bff566cb4c9cbb93b0318e26654ac3c994e2891055fd244f0039d93cb963df06c2f04dcf68fbc19e1a09a0dd0b8940bc3595beb0321a6",
        "passphrase": "",
        "symbol": "tLTC",
        "xpub_derivation": "84h/1h/0h",
        "xpriv": "tprv8g5hG3TYizJoRCqxtVhxRttHZ8q6pPJzsHaFZkUTF8SHqLYfkV3Fajapo7PRR8GWW7fcFjd82QvNHTZezcaeKx8GiaE5TwXAbtjk7XcZsmy",
        "xpub": "tpubDCmjQTVnsMzUJfskn9NYqJYQ8AM2yiVuSbB2rGWkfQEgfpoSNsrqmECgyFEgw5PiinEsJD4qfNQPuxstKzDamSqi6AozMYHUWLeBuTCjdVY",
        "account": 10,
        "index": 1,
        "address": "tltc1q3p6ts8krplarhl5eur9mvwq05wh7z8rjuy0mxm"
    },
    "french_pass": {
        "phrase": "laitier inutile atelier aubaine opprimer jeudi laisser serein affecter fatigue ve\u0301ne\u0301rer imbiber",
        "seed_hex": "0edd5e821fb55199534e6382020f40198eb03119efb26dd3d99c4ab416d1e75651a36b20b29ffba88a47e637163b977f1a5306870e3437b57e1dd24c79300687",
        "passphrase": "laisser",
        "symbol": "BCH",
        "xpub_derivation": "44h/145h/0h",
        "xpriv": "xprv9zS5Kh4XHtw9iyyipDTCqBQ1omBqn8DevJCGBHafN3veNx37Kc9DHMmTyG7dSYDoc3Na1CwJBXiUuEJwncJoHRYLMvtRfLtGWKi95YZK1Ac",
        "xpub": "xpub6DRRjCbR8GVSwU4BvEzDCKLkMo2LBawWHX7ryfzGvPTdFkNFs9TTqA5wpXPtbvNmiVy9PCsaAPeZ4G4aDQ8xesgfrgKBJKdPApk5qKExrt2",
        "account": 11,
        "index": 8,
        "address": "bitcoincash:qrpmsfr3jhs2e5mzxtzhdj25ex4csenkuv0elrwe3t"
    },
    "italian": {
        "phrase": "notare teorema sociale sveglio mini movimento ascolto sabotato irrigato tubatura atomico stabile",
        "seed_hex": "438308adce98d413270efb2289639416303216f468cf80c23cf0b30cffaf841a338dabffd83eec8104fb5b887ba02496d8abb8906ae3ce8116dd40781b5c5a6f",
        "passphrase": "",
        "symbol": "tDASH",
        "xpub_derivation": "44h/1h/0h",
        "xpriv": "tprv8fxL775fc7TnRfZZWE35yJBQgeCr5S6SMBMFa73XLb8jPbfhgejhHxUFZPSVB1UTs9PZya9wp2xodqpYTtWK6KvhuZaSmVnsd2YM8iGMSm2",
        "xpub": "tpubDCeNFX7ukV9TK8bMPshgNhqXFfinEmHLvUx2rd5pkrw8E5vUK3ZHUT67jZEAtJyMa5W9E3Ecb2WdHrhUCjHrTQm1AuLnG2ErcA3o9oFXSVQ",
        "account": 1,
        "index": 9,
        "address": "yj1mP1XmJB9cL3G4PGYnazgJMxgWmyCMvq"
    },
    "italian_pass": {
        "phrase": "notare teorema sociale sveglio mini movimento ascolto sabotato irrigato tubatura atomico stabile",
        "seed_hex": "3ab1abb8ea4262f3d4fa4d012ea3ea51bdf92e2c0207204f0d5695723236e142c3e0889ac3703edab4f2ee2b0a51323f4829b1c2aee873a6488302ccd1edc1d5",
        "passphrase": "tubatura",
        "symbol": "tBTC",
        "xpub_derivation": "84h/1h/0h",
        "xpriv": "tprv8fttCch2Gw1HXkQvRpMTcaMbwmXsP68d6hLqoLVGrZ6oYQ1LjtRruDqRDgZQygu2hzfzzTPQscXyMN9aeKESzLyeLwrbBsGhW1N1yP2p9HE",
        "xpub": "tpubDCavM2jGRJgxRDSiKU241z1iWo3oYRKXfzwd5rXaGpuCNtG7NHFT5iTHPq1pTzeFbKJCF6NHrrAzgF3iLdHUYoK9k2Ngw5hR2rVrGNHGxDz",
        "account": 19,
        "index": 8,
        "address": "tb1q59r7kxkfhhfe90jh5svcexmp8guqp8ycrut06c"
    },
    "chinese_simplified": {
        "phrase": "\u5c1a \u6dfb \u8bf4 \u52aa \u5360 \u5a5a \u8de8 \u59fb \u578b \u671d \u5f99 \u971e",
        "seed_hex": "b4a53637f8af36b477f9f24a87414ef6d2a508dc387075210b1023badf8737f72d431ebff28d7522d123e93e6fc438ba8aaa40c60e25e6c8b9effa9cf32e1cec",
        "passphrase": "",
        "symbol": "tLTC",
        "xpub_derivation": "84h/1h/0h",
        "xpriv": "tprv8fiGgDjyTZRu1AaQoGZiKcQRT63xARMNss4Dxee1n3GsyC2WU7pFYuU57dSLX5uiW6ybk5srcJXEDoP4GaNc6rLpCEsaSQjMC4taTPyWTZz",
        "xpub": "tpubDCQJpdnDbw7ZtdcCgvEJj24Y27ZtKkYHTAf1FAgKCK5GogHH6WdqjQ5wHjvQTbPffEYEayDswv476WcRiesna2RVRQeecRfVAgwBB1q4vmf",
        "account": 20,
        "index": 16,
        "address": "tltc1qndkzw2f5ge68rddkufjc58m0089se3f27at43c"
    },
    "chinese_simplified_pass": {
        "phrase": "\u5c1a \u6dfb \u8bf4 \u52aa \u5360 \u5a5a \u8de8 \u59fb \u578b \u671d \u5f99 \u971e",
        "seed_hex": "ff73113b905bb25e1362caf83e8be9216c1ff52276efb18a7571f06af73de9bfa5090eb038cdd239bf89ff87bdfede069411530e5d40b55df25a4cb7df11dcf6",
        "passphrase": "\u8de8",
        "symbol": "BCH",
        "xpub_derivation": "44h/145h/0h",
        "xpriv": "xprv9ysqPxU692ov7ShsiQ6dUH1BKBsjQW6y16hqEB4Uznh4KFAQFjPnwgBfW5Ny19TNZryjLhduFhTNGRBJx2of5m1iGhL6BJmMuj9VGSNAm9C",
        "xpub": "xpub6CsBoTzyyQNDKvnLpRddqQwusDiDoxppNKdS2ZU6Z8E3C3VYoGi3VUW9MPw4KW9fKGcJo8XBteNAF2X8hiGWphekZvnUM6JHZw1WakxBHzU",
        "account": 16,
        "index": 2,
        "address": "bitcoincash:qzvlrfvz97lmjx4ls6kmmduevzzw77zta5074d6rlf"
    },
    "chinese_traditional": {
        "phrase": "\u8fa6 \u8cde \u68af \u737b \u56db \u5fb9 \u6b32 \u7f50 \u9806 \u6572 \u9047 \u5835",
        "seed_hex": "b096e4e3e99a8678e9e32badb981eb2979acca6d70a206f565857520daebb3f4fe2b94a3f2d3d4d4a428c58c95a59f27e14d3b1f8c7ff92bf628e7f42ec82ea4",
        "passphrase": "",
        "symbol": "tBCH",
        "xpub_derivation": "44h/1h/0h",
        "xpriv": "tprv8gc4ZnNhHrCUZ7PUuNJYreWemLK5eHHEXxqY8hqq6gCeqTr5vNsfQxDiWfU5ogkemFUYAC9dkafjVZhvNuVGa3vo6u47jj4YLuGeSAwmseY",
        "xpub": "tpubDDJ6iCQwSDt9SaRGo1y9G4AmLMq1ocU97GSKRDt8Wx13fx6rYmhFbSqagop465VVXJ9TWU1qBvExfRBBSKsbFd1TFEGxeYoerJaRTHSjbN8",
        "account": 12,
        "index": 11,
        "address": "bchtest:qzscj9vpdee8tppchpyus3td4s4zf6xjsv6r5v9vz7"
    },
    "chinese_traditional_pass": {
        "phrase": "\u8fa6 \u8cde \u68af \u737b \u56db \u5fb9 \u6b32 \u7f50 \u9806 \u6572 \u9047 \u5835",
        "seed_hex": "ddc451feefda79ec56a1cc08e7cdd4c056a5fc225813038e5d6f4cda72875bb32d765abc48f20bc9ef0e2365cf20f1bfaada17877b56d679891d81920f81453d",
        "passphrase": "\u56db",
        "symbol": "tBCH",
        "xpub_derivation": "44h/1h/0h",
        "xpriv": "tprv8gZPsY2p16NuSpfxWK7aJ6Uov5r7HyyGMvbEdYRbo2VX7Lg26EnMDv7WJruvk4s7s3YKef8sQP8WB2ytH8BaNMQZEqsHUnNoAXaYRTgtDU3",
        "xpub": "tpubDDFS1x549U4aLHhkPxnAhW8vV7N3TKAAwEC1v4TuDJHuwpvnidbwQQjNUyyisorUC2fMJg1xcGmEK5dZFg3Kq13kk165FDNeo4bZPm6suqv",
        "account": 20,
        "index": 1,
        "address": "bchtest:qzsmmq0zuwq9lcd4yczxmvdk29zx25z7tqyea6r882"
    },
    "korean": {
        "phrase": "\u110e\u1165\u11ab\u110c\u1162 \u1100\u1169\u11bc\u110d\u1161 \u1100\u1161\u11c0\u110b\u1175 \u1109\u1162\u1107\u1167\u11a8 \u1109\u1175\u11af\u1109\u116e \u1109\u1175\u11b7\u1105\u1175 \u1109\u1162\u11bc\u1112\u116a\u11af \u1110\u1161\u11a8\u110c\u1161 \u110e\u116a\u11af\u110b\u1167\u11bc \u1100\u1167\u11bc\u110b\u116e \u1112\u1173\u11bc\u1106\u1175 \u1109\u1165\u11bc\u110c\u1165\u11a8",
        "seed_hex": "a6ff75923ee60ad727be50c01dbdb56832b2b8752cbbe705af0d30f009499aac243c41b7ab056e0d5334a34923e71d90813752def05a3e88d4b79877f3ffc3c8",
        "passphrase": "",
        "symbol": "LTC",
        "xpub_derivation": "84h/2h/0h",
        "xpriv": "xprv9zXEAmZ5ec2KvZ8sd2mmCnFHqjgUtw81ixFDuHCxJH2PbwX3GL2ciSUhfEaUhXh14cDsjoyKY57zExwvacx1JL4oTESU2Wmf2HxNA11rGyo",
        "xpub": "xpub6DWaaH5yUyad93DLj4JmZvC2PmWyJPqs6BAphfcZrcZNUjrBosLsGEoBWXY3Pz3DPdnhz6gzcvrTtUh843sZEKES13uQw9rbgs6JSF4iq6o",
        "account": 12,
        "index": 20,
        "address": "ltc1qzwgsuttxd8qcsfkme49vuprpvqzxyrrham8tm2"
    },
    "korean_pass": {
        "phrase": "\u110e\u1165\u11ab\u110c\u1162 \u1100\u1169\u11bc\u110d\u1161 \u1100\u1161\u11c0\u110b\u1175 \u1109\u1162\u1107\u1167\u11a8 \u1109\u1175\u11af\u1109\u116e \u1109\u1175\u11b7\u1105\u1175 \u1109\u1162\u11bc\u1112\u116a\u11af \u1110\u1161\u11a8\u110c\u1161 \u110e\u116a\u11af\u110b\u1167\u11bc \u1100\u1167\u11bc\u110b\u116e \u1112\u1173\u11bc\u1106\u1175 \u1109\u1165\u11bc\u110c\u1165\u11a8",
        "seed_hex": "bfa38155c62d7e24af676a8d7b4150bbdb48f35c44786ca18b0a4dddb19c28c3fa1cc3f6420c19d9aabedc5df586b1da34250a65d38239659f5c530a3bbf3581",
        "passphrase": "\u110e\u1165\u11ab\u110c\u1162",
        "symbol": "BTC",
        "xpub_derivation": "84h/0h/0h",
        "xpriv": "xprv9yktoBA5dtvNgTmETnhbAJ4dQWdJf2wg5mEKjrhr7q9LRJDJ8eULM8hp6Sa3rfNHw7C3zfNZMYNhCNuQXByXEfLvDrqTFqGjQ9hv75kvWts",
        "xpub": "xpub6CkFCggyUGUftwqhZpEbXS1MxYTo4VfXSz9vYF7TgAgKJ6YSgBnatw2HwgNuhLdkpGBtvpxXvVmbBi1wK57GvEehpG2ytwuvkaGwapcLWS5",
        "account": 11,
        "index": 4,
        "address": "bc1q2v9da63ttxgkzfq6g6knss8xtzq3gvekc0d9qx"
    }
}


class Test_AddressGeneration(unittest.TestCase):

    def test_mnemonic_to_seed_basic(self):
        seed = Mnemonic.to_seed(mnemonic='foobar', passphrase='none')
        self.assertEqual(
            '30a7f31981208c55102f15de25c5d9b9cacabec0dbc67eb4bcb18335e311a32cd6cd3f59c712d1671d7d7c88a3799896558aa717aa4fd612488d01313dc1c187',
            seed.hex()
        )

    def test_mnemonic_to_seed(self):
        for test_name, test in SEED_TEST_CASES.items():
            # Phrase -> Seed
            self.assertEqual(Mnemonic.to_seed(mnemonic=test['phrase'], passphrase=test['passphrase']).hex(),
                             test['seed_hex'], msg=test_name)

            # Seed -> xpriv + xpub
            network = ALL_COINS[test['symbol']]
            node = BIP32Node.from_rootseed(bytes.fromhex(test['seed_hex']), xtype='standard')
            sub_node = node.subkey_at_private_derivation(test['xpub_derivation'])
            self.assertEqual(sub_node.to_xprv(net=network), test['xpriv'], msg=test_name)
            xpub = sub_node.to_xpub(net=network)
            self.assertEqual(xpub, test['xpub'], msg=test_name)

            # xpub -> address
            xpub_node = BIP32Node.from_xkey(test['xpub'], net=network)

            subkey = xpub_node.subkey_at_public_derivation(f"/{test['account']}/{test['index']}")
            pubkey = subkey.eckey.get_public_key_bytes(compressed=True)

            if hasattr(network, "CASHADDR_PREFIX"):
                address = cashaddr.encode_full(network.CASHADDR_PREFIX, cashaddr.PUBKEY_TYPE, hash_160(pubkey))
            else:
                address = pubkey_to_address(network.address_format, pubkey.hex(), net=network)

            self.assertEqual(address, test['address'], msg=test_name)
            self.assertEqual(address,
                             network.make_address(xpub_node, account=test['account'], index=test['index']),
                             msg=test_name)

### Code to generate initial test cases ###
# import random
# output = {}
# for language in Mnemonic.list_languages():
#     memo = Mnemonic(language)
#     phrase_128 = memo.generate(128)
#     for passphrase in ('', random.choice(phrase_128.split())):
#         seed = memo.to_seed(phrase_128, passphrase=passphrase)
#
#         node = BIP32Node.from_rootseed(seed, xtype='standard')
#         network = random.choice(list(ALL_COINS.values()))
#
#         derivation_path = network.default_xpub_derivation_path
#
#         priv_node = node.subkey_at_private_derivation(derivation_path)
#         xpriv = priv_node.to_xprv(net=network)
#         xpub = priv_node.to_xpub(net=network)
#
#         account = random.randint(0, 20)
#         index = random.randint(0, 20)
#
#         xpub_node = BIP32Node.from_xkey(xpub, net=network)
#         addr = network.make_address(xpub_node, account=account, index=index)
#
#         output[language + ('_pass' if passphrase else '')] = {
#             "phrase": phrase_128,
#             "seed_hex": seed.hex(),
#             "passphrase": passphrase,
#             "symbol": network.symbol,
#             "xpub_derivation": derivation_path,
#             "xpriv": xpriv,
#             "xpub": xpub,
#             "account": account,
#             "index": index,
#             "address": addr
#         }
#
# import json
#
# print(json.dumps(output, indent=2))
