#!usr/bin/env python3

"""
Compute the exact probabilities of obtaining a DER encoded signature of certain length.
The code is kept simple and explicit and not optimized.
"""

# order of secp256k1 curve
ec_order = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141


def drop_bytes_to_int(inp, n):
    """convert the int 'inp' to bytes (32), drop the first n bytes, return the corresponding int
    """
    return int.from_bytes((inp.to_bytes(32, "big")[n:]), "big")


print("\n1. Probability of having the n-th byte below 0x80")
print("  n | probability ")
print(" ---|-------------")
p_no_00 = []
for i in range(32):
    p = 2**(8*(32-i)-1) / (drop_bytes_to_int(ec_order, i) - 1)
    if p > 1:
        p = 1
    p_no_00 += [p]
    padding = " " if len(str(i + 1)) < 2 else ""
    print(" " + padding + str(i + 1) + " | " + str(p))


print("\n2. Probability of having the n-th byte equal to 0x00")
print("  n | probability ")
print(" ---|-------------")
p_start_00 = []
for i in range(32):
    p = 2**(8*(32-i-1)) / (drop_bytes_to_int(ec_order, i) - 1)
    p_start_00 += [p]
    padding = " " if len(str(i + 1)) < 2 else ""
    print(" " + padding + str(i + 1) + " | " + str(p))


print("\n3. Probability of having an int encoded in n or less bytes")
print("  n | probability ")
print(" ---|-------------")
p_cum = []
p_cum += [1]
print(" " + str(33) + " | " + str(1))
for i in range(32):
    tot = 1
    for j in range(i):
        tot *= p_start_00[j]
    p = p_no_00[i] * tot
    p_cum += [p]
    padding = " " if len(str(32 - i)) < 2 else ""
    print(" " + padding + str(32 - i) + " | " + str(p))
p_cum += [1 / ec_order]
print(" " + " " + str(0) + " | " + str(p_cum[-1]))


print("\n4. Probability of having an int encoded in n bytes")
print("  n | probability ")
print(" ---|-------------")
p_dist = []
for i in range(33):
    p = p_cum[i] - p_cum[i+1]
    p_dist += [p]
    padding = " " if len(str(33 - i)) < 2 else ""
    print(" " + padding + str(33 - i) + " | " + str(p))


print("\n5. Probability of having a signature encoded in n bytes")
print("  n | probability ")
print(" ---|-------------")
p_sig = []
for i in range(67):
    tot = 0
    start = max(i - 32, 0)
    end = i + 1
    for j in range(start, end):
        first = j
        second = end - 1 - j
        if first > 32 or second < 0:
            tot += 0
        else:
            tot += p_dist[first] * p_dist[second]
    p_sig += [tot]
    padding = " " if len(str(73 - i)) < 2 else ""
    print(" " + padding + str(73 - i) + " | " + str(tot))
