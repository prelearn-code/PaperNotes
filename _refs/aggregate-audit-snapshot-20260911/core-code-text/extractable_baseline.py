"""Small response-code baseline used to validate the extraction harness."""
from __future__ import annotations

from .common import hash_int

FIELD = 2_147_483_647


def coefficients(seed: bytes, width: int) -> list[int]:
    return [hash_int(FIELD, b"baseline", seed, i.to_bytes(8, "big"), nonzero=True) for i in range(width)]


def respond(message: list[int], seed: bytes) -> int:
    return sum(a * b for a, b in zip(coefficients(seed, len(message)), message)) % FIELD


def solve(matrix: list[list[int]], vector: list[int]) -> list[int]:
    if not matrix or len(matrix) != len(vector) or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("invalid linear system")
    rows = [list(map(lambda x: x % FIELD, row)) + [value % FIELD]
            for row, value in zip(matrix, vector)]
    height, width = len(rows), len(matrix[0])
    pivot_row = 0
    pivots: list[int] = []
    for column in range(width):
        pivot = next((r for r in range(pivot_row, height) if rows[r][column]), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        inv = pow(rows[pivot_row][column], -1, FIELD)
        rows[pivot_row] = [x * inv % FIELD for x in rows[pivot_row]]
        for r in range(height):
            if r != pivot_row and rows[r][column]:
                factor = rows[r][column]
                rows[r] = [(x - factor * y) % FIELD for x, y in zip(rows[r], rows[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == height:
            break
    if len(pivots) < width:
        raise ValueError("rank-deficient responses")
    answer = [0] * width
    for r, column in enumerate(pivots[:width]):
        answer[column] = rows[r][-1]
    return answer


def extract(message_width: int, seeds: list[bytes], responses: list[int]) -> list[int]:
    return solve([coefficients(seed, message_width) for seed in seeds], responses)
