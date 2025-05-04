# Case 1: The arbitrary node has value 0 (probability p).
# Case 2: The node has value 1 - in which case no all-zero path can start here.

# Now consider the children. For an infinite all-zero path to exist, we need:
# - The current node to be 0.
# - At least one of its children to be the root of an inifinite all-zero path.

# The probability that neither child continues an all-zero path is:
# (Eq. I)       p = (1 - x) ^ 2

# This implies the probability that at least one child continues the path is:
# (Eq. 2)       1 - p = 1 - (1 - x)^2

# Combining this with the requirement that the current node is 0 implies:
# (Eq. 3)       x = p * (1 - (1 - x)^2)

####################################################

# More annoying shit...
# Now we have to expand to allow one node in the path to have value 1 (i.e. total sum at most 1).

# Define f(p) := probability that there exists an infinite path with at most one node of value 1

# There are two cases:
# Case 1: Root has value 1.
# Then no further 1s are allowed. The remaining path must be all zeros. This occurs with probability:
# (Eq. 4)       (1 - p) * (1 - (1 - x) ^ 2) 

# Case 2: Root has value 0.
# Then a future node may be 1, and the rest must be zeros. Recursively, this occurs with probability:
# (Eq. 5)       p * (1 - (1 - f(p))^2) 

# Therefore, we have the recursion:
# (Eq. 6)       f(p) = (1 - p) * (1 - (1 - x) ^ 2) + p * (1 - (1 - f(p))^2)

# Combining (Eq. 3) and solving for x yields:
# (Eq. 7)       x = (2p - 1) / p

####################################################

# Substituting (Eq. 7) into (Eq. 6) and solving for the condition f(p) = 1/2 yields the cubic:
# (Eq. 8)       3p^3 - 10p^2 + 12p - 4 = 0

# Now solve the cubic using numerical methods (Newton-Raphson) yields:
# Root found: 0.5306035754

from typing import Callable

def newton_raphson(
    func: Callable[[float], float],
    derivative: Callable[[float], float],
    initial_guess: float = 0.5,
    tolerance: float = 1e-10,
    max_iterations: int = 100
) -> float:
    """
    Find a root of a function using the Newton–Raphson method.

    Args:
        func: The function f(p) whose root we want.
        derivative: The derivative f′(p) of the function.
        initial_guess: Starting value for p.
        tolerance: Convergence criterion for |Δp|.
        max_iterations: Maximum allowed iterations before giving up.

    Returns:
        The estimated root p.

    Raises:
        ValueError: If the derivative is zero at any iterate.
        RuntimeError: If the method fails to converge within max_iterations.
    """
    p = initial_guess
    for iteration in range(1, max_iterations + 1):
        f_val = func(p)
        df_val = derivative(p)
        if df_val == 0:
            raise ValueError(f"Zero derivative at iteration {iteration} (p={p})")
        delta = f_val / df_val
        p -= delta
        if abs(delta) < tolerance:
            return p

    raise RuntimeError(f"No convergence after {max_iterations} iterations")


def main() -> None:
    # Define the target function and its derivative
    def f(p: float) -> float:
        return 3 * p**3 - 10 * p**2 + 12 * p - 4

    def df(p: float) -> float:
        return 9 * p**2 - 20 * p + 12

    try:
        root = newton_raphson(f, df, initial_guess=0.5)
        print(f"Root found: {root:.10f}")
    except (ValueError, RuntimeError) as e:
        print(f"Computation error: {e}")


if __name__ == "__main__":
    main()