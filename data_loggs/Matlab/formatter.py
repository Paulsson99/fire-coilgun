#Program to remove empty lines and rename files

from ctypes import sizeof
import sys
arg = sys.argv[1]

input = open(arg)
lines = input.readlines()
last = ""
out = lines[1]
for i in range(2,len(lines)):
    if len(lines[i]) > 2:
        if lines[i][2] != 'i':
            out += lines[i]
            last = lines[i]
    else:
        break

print(last)

filename = str(out.count('\n')) + '_' + str(last[2:7]) + '.csv'
f = open(filename, "x")
f.write(out)