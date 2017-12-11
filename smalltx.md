# Create small transactions
Create small transactions that are also relayed by bitcoin nodes. 

## A sent small transaction

Extract the transaction with `txid = 3419cbc51cec42d4f55d4147d0c1cef54fbdabddf4384270e6e93970b2496f74` from the blockchain.

Decode the corresponding raw transaction

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
Some considerations:
- a standard transaction must have at least one input and one output. Thus the small transaction will have one input and one output.
- the transaction has to be mined, so it has to spend a UTXO with some bitcoin locked in.
- the unlocking script must be the smallest possible, so P2PK is preferred to P2PKH because in the latter case, in addition to the signature, one has to provide also the public key (34 bytes).
- the generated UTXO is a *nulldata* script with nothing following the `OP_RETURN`.

Now there is still only one field that could be shrinked: the signature. Infact a DER encoded signature has not fixed length:
- a ECDSA signature is a couple of integer in `[1..order-1]`: `(r, s)`
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

In the following it will be used an **approximation**: `order = 2**256`. For instance `P(r < 2**255) != 1/2`, infact `P(r < 2**255) > P(r >= 2**255)` since `r` cannot assume values in `[order..2**256-1]`. 
So, despite being *extremely* close to the true results, in reality the following results are slightly overestimating the true ones (computed [here](exact_probabilities.md)).

Compute the cumulative distribution
```
P(len(encoded int) <= 33 bytes) = 1
P(len(encoded int) <= 32 bytes) = 1/2
P(len(encoded int) <= 31 bytes) = 1/256 * 1/2
P(len(encoded int) <= 30 bytes) = 1/256**2 * 1/2
...
P(len(encoded int) <= (33-n) bytes) = | 1                    if n = 0
                                      | 1/2 * 1/256**(n-1)   if n = 1, 2, ..., 32
```

Compute the discrete distribution per difference:
```
P(len(encoded int) = 33 bytes) = P(33) = 1 - 1/2 = 1/2
P(len(encoded int) = 32 bytes) = P(32) = 1/2 - 1/256 * 1/2 = 1/2 * 255/256
P(len(encoded int) = 31 bytes) = P(31) = 1/256 * 1/2 - 1/256**2 * 1/2 = 1/2 * 1/256 * 255/256
P(len(encoded int) = 30 bytes) = P(30) = 1/256**2 * 1/2 - 1/256**3 * 1/2 = 1/2 * 1/256**2 * 255/256
...
P(33-n) = | 1/2                if n = 0
          | 255/2 * 1/256**n   if n = 1, 2, ..., 32
```

Remembering that a DER signature is composed by `r` and `s` plus 7 bytes (sighash is included), compute the probability of obtaining a DER signature with a certain length. 
```
let a = 255/2, b = 1/256, recall P(33) = 1/2
P(len(encoded sig) = 73 bytes) = P(33) * P(33) = 1/4
P(len(encoded sig) = 72 bytes) = 2 * P(33) * P(32) = ab
P(len(encoded sig) = 71 bytes) = 2 * P(33) * P(31) + P(32) * P(32) = ab**2 + a**2*b**2 = b**2*(a + a**2)
P(len(encoded sig) = 70 bytes) = 2 * P(33) * P(30) + 2 * P(32) * P(31) =  ab**3 + 2*a**2*b**3 = b**3*(a + 2*a**2)
P(len(encoded sig) = 69 bytes) = 2 * P(33) * P(29) + 2 * P(32) * P(30) + P(31) * P(31) = ab**4 + 2*a**2*b**4 + a**2*b**4 = b**4*(a + 3*a**2)
P(len(encoded sig) = 68 bytes) = 2 * P(33) * P(28) + 2 * P(32) * P(29) + 2 * P(31) * P(30) = ab**5 + 2*a**2*b**5 + 2*a**2*b**5 = b**5*(a + 4*a**2)
...
P(len(encoded sig) = 73-n bytes) = | 1/4                    if n = 0
                                   | b**n*(a + (n-1)*a**2)  if n = 1,  ..., 32
                                   | b**n*(65-n)*a**2       if n = 33, ..., 65
```

Resuming:

| Length of DER encoded signature | Probability | Avg number of tries to generate such length |
| :---: | :---: | :---: |
| 73 bytes | 0.25 | 4 |
| 72 bytes | 0.498046875 | 2 |
| 71 bytes | 0.24999618530273438 | 4 |
| 70 bytes | 0.00194549560546875 | 514 |
| 69 bytes | 0.00001138454535976 | 87838 |
| 68 bytes | 0.00000005925585355 | 16875969 |
| 67 bytes | 0.00000000028922197 | 3457551881 |
| ... | ... | ... |

If one has a lot of computational power he can sign several times to get a smaller signature and save some bytes.
However this shrinks the set of nonces and this could lead to privacy and/or security issues.

## Conclusion
Above one can see some techniques to create small transactions. Those techinques are independent, could be used singularly and adapted to particular cases. 

For each signature one can sign several times to save some bytes.

One can create a minimal transaction (1 input 1 'nulldata' output) to spend very small UTXO (close to dust limit). The utility of such transction could be inserting a commitment in the signature using *sign-to-contract* (in this case without shrinking the signature).
