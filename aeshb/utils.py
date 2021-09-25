

def bitlist(n: int, sz: int) -> list:
    bl = []
    for i in range(sz):
        bl.append(n & 1)
        n = n >> 1
    return bl