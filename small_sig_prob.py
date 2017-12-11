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


# Step 1: P(n-th byte strictly below 0x80)
P1 = []
for i in range(32):
    P1 += [min(1, 2 ** (8 * (32 - i) - 1) / (drop_bytes_to_int(ec_order, i) - 1))]
# Step 2: P(n-th byte equal t0 0x00)
P2 = []
for i in range(32):
    P2 += [2 ** (8 * (32 - i - 1)) / (drop_bytes_to_int(ec_order, i) - 1)]
# Step 3: P(int encoded in n or less bytes), i.e. cumulative distribution
P3 = [1]
for i in range(32):
    tot = 1
    for j in range(i):
        tot *= P2[j]
    P3 += [P1[i] * tot]
P3 += [0]
# Step 4: P(int encoded in n bytes)
P4 = []
for i in range(33):
    P4 += [P3[i] - P3[i + 1]]
# Step 5: P(signature encoded in n bytes)
P5 = []
for i in range(66):
    tot = 0
    for j in range(i + 1):
        tot += (0 if j > 32 else P4[j]) * (0 if i - j < 0 or i - j > 32 else P4[i - j])
    P5 += [tot]


# Print results
print("\nExact probabilities of having a DER encoded signature of a certain length")
print("________________________________________")
print("Step 1: P(n-th byte strictly below 0x80)")
print(" n | P")
print("-------")
for i in range(len(P1)):
    padding = " " if len(str(i + 1)) < 2 else ""
    print(padding + str(i + 1) + " | " + str(P1[i]))
print("________________________________________")
print("Step 2: P(n-th byte equal t0 0x00)")
print(" n | P")
print("-------")
for i in range(len(P2)):
    padding = " " if len(str(i + 1)) < 2 else ""
    print(padding + str(i + 1) + " | " + str(P2[i]))
print("________________________________________")
print("Step 3: P(int encoded in n or less bytes), i.e. cumulative distribution")
print(" n | P")
print("-------")
for i in range(len(P3)):
    padding = " " if len(str(33 - i)) < 2 else ""
    print(padding + str(33 - i) + " | " + str(P3[i]))
print("________________________________________")
print("Step 4: P(int encoded in n bytes)")
print(" n | P")
print("-------")
for i in range(len(P4)):
    padding = " " if len(str(33 - i)) < 2 else ""
    print(padding + str(33 - i) + " | " + str(P4[i]))
print("________________________________________")
print("Step 5: P(signature encoded in n bytes)")
print(" n | P")
print("-------")
for i in range(len(P5)):
    padding = " " if len(str(73 - i)) < 2 else ""
    print(padding + str(73 - i) + " | " + str(P5[i]))


"""
# create tables to insert in the .md 
print("\n| n | P(n-th byte strictly below 0x80)| P(n-th byte equal t0 0x00) |")
print("| --- | --- | --- |")
for i in range(32):
    print("| " + str(i + 1) + " | " + str(P1[i]) + " |" + str(P2[i]) + " |")
print("\n| n | P(int encoded in n or less bytes) | P(int encoded in n bytes) |")
print("| --- | --- | --- |")
for i in range(33):
    print("| " + str(33 - i) + " | " + str(P3[i]) + " |" + str(P4[i]) + " |")
print("| " + str(0) + " | " + str(P3[33]) + " |" + "-" + " |")
print("\n| n | true P(signature encoded in n bytes) | approx P(signature encoded in n bytes) |")
print("| --- | --- | --- |")
a = 255 / 2
b = 1 / 256
for i in range(66):
    if i == 0:
        approx = 1/4
    elif i in range(1, 33):
        approx = b**i * (a + (i - 1) * a**2)
    else:
        approx = b**i * (65-i) * a**2
    print("| " + str(73 - i) + " | " + str(P5[i]) + " | " + str(approx) + " |")
"""