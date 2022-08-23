import math
import sys

def check(num, prime_num):
    index = 0
    if not prime_num:
        prime_num = [2]
    min_factor = prime_num[index]
    max_factor = math.floor(math.sqrt(num))
    while min_factor <= max_factor:
        remainder_big = num % max_factor
        remainder_small = num % min_factor
        if remainder_big == 0 or remainder_small == 0:
            return False
        else:
            index += 1
            min_factor = prime_num[index]
            if num / min_factor <= max_factor:
                max_factor = math.floor(num / min_factor)
            else:
                max_factor -= 1
    return True

num = 2
prime_num = list()
max = int(sys.argv[1])
while num <= max:
    if check(num, prime_num):
        prime_num.append(num)
    num += 1
for i in prime_num:
    print(i)