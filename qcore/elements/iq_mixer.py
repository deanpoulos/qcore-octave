""" """

import numpy as np


def correction_matrix(g: float, p: float) -> list[float, float, float, float]:
    """ """
    try:
        cos, sin = np.cos(p), np.sin(p)
        coefficient = 1 / ((1 - g**2) * (2 * cos**2 - 1))
    except TypeError:
        message = f"Invalid offset value(s): {g = }, {p = }, both must be {float}."
        raise ValueError(message) from None
    else:
        matrix = ((1 - g) * cos, (1 + g) * sin, (1 - g) * sin, (1 + g) * cos)
        return [coefficient * value for value in matrix]
