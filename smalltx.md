# Create small transactions
Create small transactions that are also relayed by bitcoin core nodes. 

For now only in testnet.

## Premise
Testnet let you send non standard transactions, so when passing to mainnet that may be a problem.

Example of non standard transaction:
```
$ gettxout f1b53edee2b40f5823b0855d9278a900512a82e838d5a87e90070493c7672cf6 1
{
  "bestblock": "000000000000307fc50e26b656f115f2aab888f15542ca759a4c63e5e1d86f88",
  "confirmations": 3,
  "value": 0.00000000,
  "scriptPubKey": {
    "asm": "OP_CHECKSIG OP_RETURN",
    "hex": "ac6a",
    "type": "nonstandard"
  },
  "coinbase": false
}
```

## A sent small *standard* transaction

Extract the transaction from the testnet blockchain

```
$ gettransaction ab6f694c045fd8f9cdd47a4894b932e387b27c5508f3cbddf421356dd806b930
{
  "amount": 0.00000000,
  "fee": -0.05000000,
  "confirmations": 182,
  "blockhash": "0000000000000104a300da55c1d1b310f6f848cf52a807c2358c44f7873d2f64",
  "blockindex": 1,
  "blocktime": 1512043732,
  "txid": "ab6f694c045fd8f9cdd47a4894b932e387b27c5508f3cbddf421356dd806b930",
  "walletconflicts": [
  ],
  "time": 1512043719,
  "timereceived": 1512043719,
  "bip125-replaceable": "no",
  "details": [
    {
      "account": "",
      "category": "send",
      "amount": 0.00000000,
      "vout": 0,
      "fee": -0.05000000,
      "abandoned": false
    }
  ],
  "hex": "0200000001dfd3ba28fd4b7e20c497e31e1c8b1e819529e487f8a2ab681f5988e8e9d9ed770000000047463043021f0756003da43c7165b73d1420c41c202cb3b3b1ab46d951044667c1987b0cde02204b5fc12ec7411eceb382eae7235911e4675780afcc1ea6254e5ceeb0433aef7201ffffffff010000000000000000016a00000000"
}
```

Decode the raw transaction

```
$ decoderawtransaction 0200000001dfd3ba28fd4b7e20c497e31e1c8b1e819529e487f8a2ab681f5988e8e9d9ed770000000047463043021f0756003da43c7165b73d1420c41c202cb3b3b1ab46d951044667c1987b0cde02204b5fc12ec7411eceb382eae7235911e4675780afcc1ea6254e5ceeb0433aef7201ffffffff010000000000000000016a00000000
{
  "txid": "ab6f694c045fd8f9cdd47a4894b932e387b27c5508f3cbddf421356dd806b930",
  "hash": "ab6f694c045fd8f9cdd47a4894b932e387b27c5508f3cbddf421356dd806b930",
  "version": 2,
  "size": 132,
  "vsize": 132,
  "locktime": 0,
  "vin": [
    {
      "txid": "77edd9e9e888591f68aba2f887e42995811e8b1c1ee397c4207e4bfd28bad3df",
      "vout": 0,
      "scriptSig": {
        "asm": "3043021f0756003da43c7165b73d1420c41c202cb3b3b1ab46d951044667c1987b0cde02204b5fc12ec7411eceb382eae7235911e4675780afcc1ea6254e5ceeb0433aef72[ALL]",
        "hex": "463043021f0756003da43c7165b73d1420c41c202cb3b3b1ab46d951044667c1987b0cde02204b5fc12ec7411eceb382eae7235911e4675780afcc1ea6254e5ceeb0433aef7201"
      },
      "sequence": 4294967295
    }
  ],
  "vout": [
    {
      "value": 0.00000000,
      "n": 0,
      "scriptPubKey": {
        "asm": "OP_RETURN",
        "hex": "6a",
        "type": "nulldata"
      }
    }
  ]
}
```

Its size is 132 bytes:
1. 4 bytes for version
2. 1 byte for number of inputs
3. 32 bytes for txid
4. 4 bytes for vout
5. 1 byte for length of unlocking script
6. 1 byte for length of signature
7. 70 bytes for DER encoded signature (with sighash at the end)
8. 4 bytes for sequence number
9. 1 byte for number of outputs
10. 8 bytes for amount
11. 1 byte for length of locking script
12. 1 bytes for locking script
13. 4 bytes for nlocktime

## How to obtain a small *standard* transaction?
Some consideration:
- a standard transaction must have at least one input and one iutput. Thus the small transaction will have 1 input and 1 output
- the transaction has to be mined, so the it has to spend a UTXO with some bitcoin locked in
- the UTXO will be a P2PK since to spend it one need to provide only the signature, while with a P2PKH the signature must be followed by the public key (34 bytes)
- the generated UTXO is a *nulldata* script with nothing following the `OP_RETURN` (1 is the minimum length for an output).

Now there is still only one field that could be shrinked: the signature.
However a DER encoded signature has not fixed length:
- a ECDSA signature is a couple of integer in [1..order-1]: `(r, s)`
- as specified in BIP66, a DER encoded signature is composed by:
	- `0x30` DER encoded signature follows
	- 1 byte for length of signature
	- `0x02` int follows
	- 1 byte for length of `r`
	- `r` in bytes (33 or less bytes)
	- `0x02` int follows
	- 1 byte for length of `s`
	- `s` in bytes (33 or less bytes)
	- 1 byte for sighash
- when encoding `r` and `s` in bytes if the most signficant byte is `0x80` or more then prepend `0x00`

The idea is to try different nonces in order to obtain find smaller DER encoded signatures.
To generate the nonces in a secure but not expensive way one can generate the entropy to generate the first nonce and then derive the next ones deterministically.

Some math:
```
P(len(encoded int) <= 33 bytes) = 1
P(len(encoded int) <= 32 bytes) = 1/2
P(len(encoded int) <= 31 bytes) = 1/256 * 1/2
P(len(encoded int) <= 30 bytes) = 1/256**2 * 1/2
...

P(len(encoded int) = 33 bytes) = P(33) = 1 - 1/2 = 1/2
P(len(encoded int) = 32 bytes) = P(32) = 1/2 - 1/256 * 1/2 = 1/2 * 255/256
P(len(encoded int) = 31 bytes) = P(31) = 1/256 * 1/2 - 1/256**2 * 1/2 = 1/2 * 1/256 * 255/256
P(len(encoded int) = 30 bytes) = P(30) = 1/256**2 * 1/2 - 1/256**3 * 1/2 = 1/2 * 1/256**2 * 255/256
...

P(len(encoded sig) = 73 bytes) = P(33) * P(33) = 1/4
P(len(encoded sig) = 72 bytes) = P(33) * P(32) * 2 = 255/512
P(len(encoded sig) = 71 bytes) = P(33) * P(31) * 2 + P(32) * P(32) = 1/2 * 1/256 * 255/256 + (1/2 * 255/256)**2 = 255/512 * 257/512
P(len(encoded sig) = 70 bytes) = P(33) * P(30) * 2 + P(32) * P(31) * 2 = 1/2 * 1/256**2 * 255/256 + 255/256 * 1/2 * 1/256 * 255/256 = 255/512 * 1/256
...

```

Resuming:

| Length of DER encoded signature | Probability | Tries to generate such length |
| :---: | :---: | :---: |
| 73 bytes | 0.25 | 4 |
| 72 bytes | 0.498046875 | 2 |
| 71 bytes | 0.24999618530273438 | 4 |
| 70 bytes | 0.00194549560546875 | 514 |
| ... | ... | ... |

If one has a lot of computational power he can sign several times to get a smaller signature and save some bytes.
However this shrink the set of nonces and this could lead to privacy and/or security issues.

## Conclusion
One can sign several times to save some bytes.

One can create a minimal transaction (1 input 1 'nulldata' output) to spend very small UTXO (close to dust limit). The utility of such transction could be inserting a commitment in the signature using *sign-to-contract*.
