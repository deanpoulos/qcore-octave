""" """

from inspect import isfunction
import math

import lmfit
from lmfit import Model
from lmfit.models import LinearModel
import numpy as np


def create_params(**kwargs):
    """patch method because lmfit does not like working with np datatypes"""
    params = {}
    for name, value in kwargs.items():
        if isinstance(value, dict):
            value = {k: v.item() for k, v in value.items() if isinstance(v, np.number)}
        else:
            value = value.item()
        params[name] = value
    return lmfit.create_params(**params)


def atan(y, x):
    """ """

    def fn(x, fr, Ql, theta, sign=1):
        """
        Arctan fit for resonator phase response around complex plane origin
        x: array of probe frequencies (independent variables)
        fr: resonant frequency
        Ql: loaded (total) quality factor
        theta: arbitrary phase y-offset
        sign: +1 if S shape, -1 if reverse S shape phase response, not varied
        note that np.arctan return real values in the interval [-pi/2, pi/2]
        """
        return theta + 2 * np.arctan(2 * Ql * sign * (x / fr - 1))

    def params():
        """ """
        sign = 1 if y[0] < y[-1] else -1
        fr = x[np.argmax(np.gradient(y))]
        Ql = (fr / (max(x) - min(x))) * np.sqrt(len(x))
        pts = len(y) // 8
        theta = np.average((y[:pts] + y[-pts:]) / 2)
        sign_dict = {"value": sign, "vary": False}
        return create_params(fr=fr, Ql=Ql, theta=theta, sign=sign_dict)

    result = Model(fn).fit(y, params(), x=x)
    return result.best_fit, result.best_values


def displacement_cal(y, x):
    """ """

    def fn(x, dispscale, ofs, amp, n):
        """ """
        alphas = x * dispscale
        nbars = alphas**2
        return ofs + amp * nbars**0 / math.factorial(0) * np.exp(-nbars)

    def params():
        """ """
        mul = -1 if (x[-1] > x[0]) else 1
        amp = mul * (y[-1] - y[0])
        ofs = np.max(y) if (amp < 0) else np.min(y)
        return create_params(dispscale=1.0, ofs=ofs, amp=amp, n=0)

    result = Model(fn).fit(y, params(), x=x)
    return result.best_fit, result.best_values


def double_gaussian_2dhist(z, y, x):
    """ """

    def fn(y, x, y0, x0, y1, x1, a0, a1, ofs, sigma=2):
        """ """
        r0 = (x - x0) ** 2 + (y - y0) ** 2
        r1 = (x - x1) ** 2 + (y - y1) ** 2
        a0_exp, a1_exp = np.exp(-0.5 * r0 / sigma**2), np.exp(-0.5 * r1 / sigma**2)
        return ofs + a0 * a0_exp + a1 * a1_exp

    def params():
        """ """
        zofs = np.mean([z[0, :], z[-1, :], z[:, 0], z[:, -1]])
        z = z - zofs

        # Locate first max
        maxidx0 = np.argmax(np.abs(z))
        x0 = x.flatten()[maxidx0]
        y0 = y.flatten()[maxidx0]
        a0 = z.flatten()[maxidx0]

        # Other estimates
        dmin = (np.max(x) - np.min(x)) / 8
        mask = ((x - x0) ** 2 + (y - y0) ** 2) > dmin**2
        sigma = np.abs(dmin)

        # Locate second max
        maxidx1 = np.argmax(np.abs(z[mask]))
        x1 = x[mask].flatten()[maxidx1]
        y1 = y[mask].flatten()[maxidx1]
        a1 = z[mask].flatten()[maxidx1]

        return create_params(y0=y0, x0=x0, y1=y1, x1=x1, a0=a0, a1=a1, sigma=sigma)

    result = Model(fn).fit(z, params(), y=y, x=x)
    return result.best_fit, result.best_values


def exp_decay(y, x):
    """ """

    def fn(x, A, tau, ofs):
        """ """
        return A * np.exp(-x / tau) + ofs

    def params():
        """ """
        ofs = y[-1]
        y = y - ofs
        tau = (x[-1] - x[0]) / 5
        tau_dict = {"value": tau, "min": 0, "max": 100 * tau}
        return create_params(A=y[0], tau=tau_dict, ofs=ofs)

    result = Model(fn).fit(y, params(), x=x)
    return result.best_fit, result.best_values


def exp_decay_sine(y, x):
    """ """

    def fn(x, amp=1, f0=0.05, phi=np.pi / 4, ofs=0, tau=0.5):
        return amp * np.sin(2 * np.pi * x * f0 + phi) * np.exp(-x / tau) + ofs

    def params():
        """ """
        params = sine(y, x, return_params=True)
        params.add("tau", value=np.average(x), min=0, max=10 * x[-1])
        return params

    result = Model(fn).fit(y, params(y, x), x=x)
    return result.best_fit, result.best_values


def gaussian(y, x):
    """ """

    def fn(x, x0, sig, ofs, amp):
        """ """
        return ofs + amp * np.exp(-((x - x0) ** 2) / (2 * sig**2))

    def params():
        """ """
        ofs = (y[0] + y[-1]) / 2
        peak_idx = np.argmax(abs(y - ofs))
        sig = abs(x[-1] - x[0]) / 10
        yrange = np.max(y) - np.min(y)
        ofs_min, ofs_max = np.min(y) - 0.3 * yrange, np.max(y) + 0.3 * yrange
        return create_params(
            x0={"value": x[peak_idx], "min": np.min(x), "max": np.max(x)},
            sig={"value": sig, "min": abs(x[1] - x[0]), "max": abs(x[-1] - x[0])},
            ofs={"value": ofs, "min": ofs_min, "max": ofs_max},
            amp={"value": y[peak_idx] - ofs, "min": -3 * yrange, "max": 3 * yrange},
        )

    result = Model(fn).fit(y, params(), x=x)
    return result.best_fit, result.best_values


def linear(y, x):
    """ """
    result = LinearModel.fit(y, x=x)
    return result.best_fit, result.best_values


def lorentzian(y, x, return_params=False):
    """ """

    def fn(x, fr, ofs, height, fwhm):
        """ """
        return np.abs(ofs + height / (1 + 2j * ((x - fr) / fwhm)))

    def params():
        """ """
        pts = len(y) // 8
        ofs = np.average((y[:pts] + y[-pts:]) / 2)
        height = np.abs(np.max(y) - np.min(y))
        fr_idx = (y - np.abs(ofs + height)).argmin()
        fr = x[fr_idx]
        is_inverted = np.abs(y[0] - y.max()) < np.abs(y[-1] - y.min())
        height = -height if is_inverted else height
        amp, left, right = height / 2 + ofs, y[:fr_idx], y[fr_idx:]
        fwhm = x[fr_idx + np.abs(right - amp).argmin()] - x[np.abs(left - amp).argmin()]
        return create_params(fr=fr, ofs=ofs, height=height, fwhm=fwhm)

    fit_params = params()
    if return_params:
        return fit_params
    result = Model(fn).fit(y, fit_params, x=x)
    return result.best_fit, result.best_values


def lorentzian_asymmetric(y, x):
    """ """

    def fn(x, fr, ofs, height, fwhm, phi):
        """ """
        return np.abs(ofs + height * np.exp(1j * phi) / (1 + 2j * ((x - fr) / fwhm)))

    def params():
        """ """
        params = lorentzian(y, x, return_params=True)
        ofs, height, fr = params["ofs"].value, params["height"].value, params["fr"]
        phi = 4 * np.arcsin((np.max(y) - ofs) / height)
        params.add("phi", value=phi)
        fr_idx = (y - np.abs(ofs + height * np.exp(1j * phi))).argmin()
        fr.set(value=x[fr_idx])
        return params

    result = Model(fn).fit(y, params(), x=x)
    return result.best_fit, result.best_values


def sine(y, x, return_params=False):
    """ """

    def fn(x, f0, ofs, amp, phi):
        """ """
        return ofs + amp * np.sin(2 * np.pi * f0 * x + phi)

    def params():
        """ """
        fs = np.fft.rfftfreq(len(x), x[1] - x[0])
        ofs = np.mean(y)
        fft = np.fft.rfft(y - ofs)
        idx = np.argmax(abs(fft))
        return create_params(
            f0={"value": fs[idx], "min": fs[0], "max": fs[-1]},
            ofs={"value": ofs, "min": np.min(y), "max": np.max(y)},
            amp={"value": np.std(y - ofs), "min": 0, "max": np.max(y) - np.min(y)},
            phi={"value": np.angle(fft[idx]), "min": -2 * np.pi, "max": 2 * np.pi},
        )

    fit_params = params()
    if return_params:
        return fit_params
    result = Model(fn).fit(y, fit_params, x=x)
    return result.best_fit, result.best_values


FITFN_MAP = {
    k: v for k, v in locals().items() if not k == "isfunction" and isfunction(v)
}
