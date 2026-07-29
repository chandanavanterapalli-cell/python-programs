even = 0
odd = 0

for i in range(1, 21):
    if i % 2 == 0:
        even += 1
    else:
        odd += 1

print("Even count =", even)
print("Odd count =", odd)