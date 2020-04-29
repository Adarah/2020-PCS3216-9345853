from ctypes import c_int8
with open("test.bin", "wb") as f:
    for i in range(0, 50):
        f.write(c_int8(i))
