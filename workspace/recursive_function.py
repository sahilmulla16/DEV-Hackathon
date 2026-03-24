def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test the function
print(factorial(5))