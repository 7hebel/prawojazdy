import random
seed = 123
data = list(range(1, 10))

random.seed(123)
random.shuffle(data)
print(data)
