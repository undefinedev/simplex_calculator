import random

num_vars = 25
num_constraints = 25

print(f"{num_vars} {num_constraints}")


goal_type = "min"

goal_coefs = []
for _ in range(num_vars):
    val = random.randint(-10, 10)
    goal_coefs.append(str(val))

print(" ".join(goal_coefs), goal_type)


relation = "<="


for _ in range(num_constraints):
    coeffs = []
    for __ in range(num_vars):
        val = random.randint(-10, 10)
        coeffs.append(str(val))
    rhs_val = str(random.randint(-10, 10))
    print(" ".join(coeffs), relation, rhs_val)
