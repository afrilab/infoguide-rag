import math
import time

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = int(math.sqrt(n)) + 1
    for i in range(3, limit, 2):
        if n % i == 0:
            return False
    return True

start = time.time()

N = 100000
count = sum(1 for i in range(2, N + 1) if is_prime(i))

end = time.time()

print(f"Checked numbers up to: {N}")
print(f"Prime count: {count}")
print(f"Elapsed time: {end - start:.4f} seconds")
