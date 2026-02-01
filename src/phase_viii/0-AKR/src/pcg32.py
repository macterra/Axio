"""
PCG32 Pseudorandom Number Generator

Deterministic PRNG per Q20 for AKR-0 harness.
Implementation follows PCG32 specification for cross-platform reproducibility.
"""


class PCG32:
    """
    PCG32 (Permuted Congruential Generator) implementation.

    Produces deterministic sequences identical across platforms.
    State is 64-bit, output is 32-bit.

    Reference: https://www.pcg-random.org/
    """

    # PCG32 constants
    MULTIPLIER = 6364136223846793005
    INCREMENT_BASE = 1442695040888963407
    MASK_64 = (1 << 64) - 1
    MASK_32 = (1 << 32) - 1

    def __init__(self, seed: int, stream: int = 0):
        """
        Initialize PCG32 with seed and stream.

        Args:
            seed: Initial seed value
            stream: Stream ID (default 0 per preregistration)
        """
        # Compute increment from stream (must be odd)
        self.increment = ((stream << 1) | 1) & self.MASK_64

        # Initialize state
        self.state = 0
        self._step()
        self.state = (self.state + seed) & self.MASK_64
        self._step()

    def _step(self) -> None:
        """Advance internal state by one step."""
        self.state = (self.state * self.MULTIPLIER + self.increment) & self.MASK_64

    def next_u32(self) -> int:
        """
        Generate next 32-bit unsigned integer.

        Returns:
            Random integer in [0, 2^32 - 1]
        """
        # Save old state for output generation
        old_state = self.state

        # Advance state
        self._step()

        # Output function: XSH-RR (xorshift high, random rotate)
        xorshifted = (((old_state >> 18) ^ old_state) >> 27) & self.MASK_32
        rot = (old_state >> 59) & 31

        return ((xorshifted >> rot) | (xorshifted << (32 - rot))) & self.MASK_32

    def next_bounded(self, bound: int) -> int:
        """
        Generate random integer in [0, bound).

        Uses rejection sampling for uniform distribution.

        Args:
            bound: Upper bound (exclusive)

        Returns:
            Random integer in [0, bound)
        """
        if bound <= 0:
            raise ValueError("Bound must be positive")
        if bound == 1:
            return 0

        # Compute threshold for rejection sampling
        threshold = ((self.MASK_32 + 1) - bound) % bound

        while True:
            r = self.next_u32()
            if r >= threshold:
                return r % bound

    def choice(self, seq: list) -> any:
        """
        Choose a random element from a sequence.

        Args:
            seq: Non-empty sequence

        Returns:
            Random element from seq
        """
        if not seq:
            raise ValueError("Cannot choose from empty sequence")
        return seq[self.next_bounded(len(seq))]

    def sample(self, population: list, k: int) -> list:
        """
        Choose k unique elements from population without replacement.

        Uses Fisher-Yates shuffle (partial).

        Args:
            population: Sequence to sample from
            k: Number of elements to choose

        Returns:
            List of k unique elements
        """
        if k < 0:
            raise ValueError("k must be non-negative")
        n = len(population)
        if k > n:
            raise ValueError("Sample larger than population")

        # Make a copy to shuffle
        pool = list(population)
        result = []

        for i in range(k):
            j = self.next_bounded(n - i)
            result.append(pool[j])
            pool[j] = pool[n - 1 - i]

        return result

    def shuffle(self, seq: list) -> list:
        """
        Return a shuffled copy of the sequence.

        Uses Fisher-Yates shuffle.

        Args:
            seq: Sequence to shuffle

        Returns:
            New shuffled list
        """
        result = list(seq)
        n = len(result)

        for i in range(n - 1, 0, -1):
            j = self.next_bounded(i + 1)
            result[i], result[j] = result[j], result[i]

        return result

    def random_float(self) -> float:
        """
        Generate random float in [0, 1).

        Returns:
            Random float
        """
        return self.next_u32() / (self.MASK_32 + 1)

    def bernoulli(self, p: float) -> bool:
        """
        Return True with probability p.

        Args:
            p: Probability in [0, 1]

        Returns:
            Boolean with P(True) = p
        """
        return self.random_float() < p


def test_pcg32():
    """
    Test PCG32 produces expected reference values.

    These values must match across all implementations.
    """
    # Test with seed=11, stream=0 (first run configuration)
    rng = PCG32(seed=11, stream=0)

    # Generate first 10 values for reference
    values = [rng.next_u32() for _ in range(10)]

    print("PCG32 reference values (seed=11, stream=0):")
    for i, v in enumerate(values):
        print(f"  [{i}] = {v}")

    # Test bounded generation
    rng2 = PCG32(seed=22, stream=0)
    bounded = [rng2.next_bounded(100) for _ in range(10)]
    print(f"\nBounded [0,100) values (seed=22): {bounded}")

    # Test sample
    rng3 = PCG32(seed=33, stream=0)
    population = list(range(20))
    sampled = rng3.sample(population, 5)
    print(f"\nSample 5 from 0-19 (seed=33): {sampled}")


if __name__ == "__main__":
    test_pcg32()
