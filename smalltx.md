# Create small transactions
Create small transactions that are also relayed by bitcoin nodes. 

## A sent small transaction

Extract the transaction from the blockchain

```
$ gettransaction 3419cbc51cec42d4f55d4147d0c1cef54fbdabddf4384270e6e93970b2496f74
{
  "amount": 0.00000000,
  "fee": -0.00050000,
  "confirmations": 1,
  "blockhash": "00000000000000000007d491e5ff5d33f4df80bdbc26e0c8f4e140c85783deac",
  "blockindex": 133,
  "blocktime": 1512383418,
  "txid": "3419cbc51cec42d4f55d4147d0c1cef54fbdabddf4384270e6e93970b2496f74",
  "walletconflicts": [
  ],
  "time": 1512382225,
  "timereceived": 1512382225,
  "bip125-replaceable": "no",
  "details": [
    {
      "account": "",
      "category": "send",
      "amount": 0.00000000,
      "vout": 0,
      "fee": -0.00050000,
      "abandoned": false
    }
  ],
  "hex": "0200000001017a28f3d62d98803174bd1ba3827c62e4ccb28b4aa23aa5c7bec74301005f1b0000000044433040022002aedaad7897022be857509bbf753d5c05d6c20092cf5088413f31d6ff661f0b021c57e00a637102d8223360b6797d0bb33c2dfc4504c30d0c4ced29ddb301ffffffff010000000000000000016a00000000"
}
```

Decode the raw transaction

```
$ decoderawtransaction 0200000001017a28f3d62d98803174bd1ba3827c62e4ccb28b4aa23aa5c7bec74301005f1b0000000044433040022002aedaad7897022be857509bbf753d5c05d6c20092cf5088413f31d6ff661f0b021c57e00a637102d8223360b6797d0bb33c2dfc4504c30d0c4ced29ddb301ffffffff010000000000000000016a00000000
{
  "txid": "3419cbc51cec42d4f55d4147d0c1cef54fbdabddf4384270e6e93970b2496f74",
  "hash": "3419cbc51cec42d4f55d4147d0c1cef54fbdabddf4384270e6e93970b2496f74",
  "version": 2,
  "size": 129,
  "vsize": 129,
  "locktime": 0,
  "vin": [
    {
      "txid": "1b5f000143c7bec7a53aa24a8bb2cce4627c82a31bbd743180982dd6f3287a01",
      "vout": 0,
      "scriptSig": {
        "asm": "3040022002aedaad7897022be857509bbf753d5c05d6c20092cf5088413f31d6ff661f0b021c57e00a637102d8223360b6797d0bb33c2dfc4504c30d0c4ced29ddb3[ALL]",
        "hex": "433040022002aedaad7897022be857509bbf753d5c05d6c20092cf5088413f31d6ff661f0b021c57e00a637102d8223360b6797d0bb33c2dfc4504c30d0c4ced29ddb301"
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

Its size is 129 bytes:
1. 4 bytes for version
2. 1 byte for number of inputs
3. 32 bytes for txid
4. 4 bytes for vout
5. 1 byte for length of unlocking script
6. 1 byte for length of signature
7. 67 bytes for DER encoded signature (including sighash)
8. 4 bytes for sequence number
9. 1 byte for number of outputs
10. 8 bytes for amount
11. 1 byte for length of locking script
12. 1 bytes for locking script
13. 4 bytes for nlocktime

## How to obtain a small *standard* transaction?
Some consideration:
- a standard transaction must have at least one input and one output. Thus the small transaction will have one input and one output.
- the transaction has to be mined, so it has to spend a UTXO with some bitcoin locked in.
- the unlocking script must be the smallest possible, so P2PK is preferred to P2PKH because in the latter case, in addition to the signature, one has to provide also the public key (34 bytes).
- the generated UTXO is a *nulldata* script with nothing following the `OP_RETURN`.

Now there is still only one field that could be shrinked: the signature. Infact a DER encoded signature has not fixed length:
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

The idea is to try different nonces in order to find a smaller DER encoded signatures.
Generating multiple nonces doesn't have to be expensive, one can generate the first in the a standard way and then derive the next ones deterministically.

Some math (with an approximation, i.e. `order = 2**256`):
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

| Length of DER encoded signature | Probability | Avg number of tries to generate such length |
| :---: | :---: | :---: |
| 73 bytes | 0.25 | 4 |
| 72 bytes | 0.498046875 | 2 |
| 71 bytes | 0.24999618530273438 | 4 |
| 70 bytes | 0.00194549560546875 | 514 |
| ... | ... | ... |
| 67 bytes | 0.00000000028922197 | 3457551881 |
| ... | ... | ... |


If one has a lot of computational power he can sign several times to get a smaller signature and save some bytes.
However this shrinks the set of nonces and this could lead to privacy and/or security issues.

## Conclusion
Above one can see some techniques to create small transactions. Those techinques are independent, could be used singularly and adapted to particular cases. 

For each signature one can sign several times to save some bytes.

One can create a minimal transaction (1 input 1 'nulldata' output) to spend very small UTXO (close to dust limit). The utility of such transction could be inserting a commitment in the signature using *sign-to-contract* (in this case without shrinking the signature).
