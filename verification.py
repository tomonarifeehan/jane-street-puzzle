import sys
from collections import Counter
from math import prod


def parse_nums(line: str) -> list[int]:
    """
    Extracts all positive integers from a line of digits and zeros,
    splitting on zeros.
    """
    filtered = ''.join(ch for ch in line if ch.isdigit())
    return [int(piece) for piece in filtered.split('0') if piece]


def digits_of(n: int) -> list[int]:
    """Returns the list of decimal digits of n."""
    return [int(d) for d in str(n)]


def is_square(n: int) -> bool:
    """True if n is a perfect square."""
    root = int(n**0.5)
    return root * root == n


def product_of_digits_equals(target: int):
    """Returns a predicate checking whether the product of digits == target."""
    return lambda n: prod(digits_of(n)) == target


def is_multiple_of(divisor: int):
    """Returns a predicate checking whether n % divisor == 0."""
    return lambda n: n % divisor == 0


def divisible_by_each_digit(n: int) -> bool:
    """True if n is divisible by each of its (nonzero) digits."""
    return all(n % d == 0 for d in digits_of(n) if d != 0)


def is_odd_palindrome(n: int) -> bool:
    """True if n is an odd-leading palindrome."""
    s = str(n)
    return s == s[::-1] and int(s[0]) % 2 == 1


def is_fibonacci(n: int) -> bool:
    """True if n appears in the Fibonacci sequence."""
    a, b = 0, 1
    while b < n:
        a, b = b, a + b
    return b == n


def is_prime_from_file(n: int, path: str = "../resources/primes.txt") -> bool:
    """
    Checks primality by looking up n in a sorted list of primes (one per line).
    Stops early once primes exceed the length of n.
    """
    s = str(n)
    with open(path) as f:
        for line in f:
            p = line.strip()
            if p == s:
                return True
            if len(p) > len(s):
                break
    return False


def main():
    # One check per row, in the order given by the puzzle hints
    checks = [
        is_square,
        product_of_digits_equals(20),
        is_multiple_of(13),
        is_multiple_of(32),
        divisible_by_each_digit,
        product_of_digits_equals(25),
        divisible_by_each_digit,
        is_odd_palindrome,
        is_fibonacci,
        product_of_digits_equals(2025),
        is_prime_from_file,
    ]

    # Read all lines from stdin, parse into integer lists
    rows = [parse_nums(line) for line in sys.stdin.read().splitlines()]

    # Verify each row against its corresponding check
    for check, nums in zip(checks, rows):
        assert all(check(n) for n in nums), f"Check failed on {nums}"

    # Ensure every number from the grid appears exactly once
    flat = [n for row in rows for n in row]
    assert all(count == 1 for count in Counter(flat).values()), "Duplicate number found"

    # Output the final sum
    print(sum(flat))


if __name__ == "__main__":
    main()