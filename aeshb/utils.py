

def int2bitlist(n: int, sz: int) -> list:
    bl = []
    for i in range(sz):
        bl.append(n & 1)
        n = n >> 1
    return bl

def bitlist2int(bl: list) -> int:
    n = 0
    for i, b in enumerate(bl):
        assert 0 <= b <= 1
        n |= (b << i)
    return n
