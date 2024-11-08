from math import comb


def calculateProbability(N, p, M):
    binomialCoeff = comb(N, M)
    probability = binomialCoeff * p**M * (1 - p) ** (N - M)
    return probability
