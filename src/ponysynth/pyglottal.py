# Taken from https://github.com/serwy/hilbertgci with minor
# modifications.

from pylab import *
from numpy import *
import scipy.signal as sig
from numpy import where as find

__all__ = ['fasthilbert', 'inlier_elim',
       'butter1', 'gadfli', 'quick_gci',
       'compare_markings', 'compare_cycles',
       'cycle_stats']

def fasthilbert(x):
    # zero-pad to next power of 2...
    L = len(x)
    z = zeros(int(2**(floor(log2(L)) + 1)))
    z[:L] = x
    y = sig.hilbert(z)
    return y[:L]


def inlier_elim(b, m):
    """ Apply inlier elimination, return remaining samples. """
    while True:
        s = b.std()
        idx = find(abs(b) >= m*s)
        if len(idx) != len(b):
            b = b[idx]
        else:
            return b

def butter1(fc, btype='low'):
    """ Generate a 1st order Butterworth filter. """
    # equivalent to sig.butter(1, fc, btype)
    a1 = -(1 - tan(pi*fc/2)) / (1 + tan(pi*fc/2))
    A = array([1, a1])
    if btype == 'low':
        bl = (1+a1) / 2
        B = array([bl, bl])
    elif btype == 'high':
        bh = (1-a1) / 2
        B = array([bh, -bh])
    return B, A


def der(x):
    """ Apply a first difference. """
    dx = sig.lfilter([1, -1], [1], x)
    dx[0] = dx[1] # avoid initial spike
    return dx


def gadfli(g, fmin=20, fmax=1000, fs=20000, m=0.25, tau=-0.25,
        theta=0, reps=2, inside=False):
    """ Return GCIs using GADFLI algorithm. """

    Bh, Ah = butter1(fmin/(fs/2), 'high')
    Bl, Al = butter1(fmax/(fs/2), 'low')

    for i in range(reps):
        g = sig.filtfilt(Bh, Ah, g)
        g = sig.filtfilt(Bl, Al, g)

    dg = der(g)
    h = fasthilbert(dg) * exp(1j * theta)

    dphi = der(angle(h))
    gci_c = find(dphi < -1.5*pi) # candidates

    rh = real(h)
    kept = inlier_elim(rh, m)
    scale = kept.std()

    gci = array([i for i in gci_c if rh[i] < tau*scale])

    if not inside: return gci
    else: return gci, locals()


def quick_gci(g, fmin=20, fmax=1000, fs=20000, theta=0,
             reps=2, reps2=None, gamma=1, inside=False):
    """ Return GCIs using QuickGCI algorithm. """

    Bh, Ah = butter1(fmin/(fs/2), 'high')
    Bl, Al = butter1(fmax/(fs/2), 'low')

    for i in range(reps):
        g = sig.filtfilt(Bh, Ah, g)
        g = sig.filtfilt(Bl, Al, g)

    x = fasthilbert(g) * exp(1j*theta)
    q = abs(x) ** gamma * imag(-x)

    for i in range(reps if reps2 is None else reps2):
        q = sig.filtfilt(Bl, Al, q)

    r = fasthilbert(q)

    dphi = der(angle(r))
    gci = find(dphi < -1.5*pi)

    if not inside: return gci
    else: return gci, locals()


def _get_bounds(x, y, idx, half=True):
    """ return search boundaries for x[idx]"""
    mid = x[idx]
    if idx == 0:
        lo = min([x[0], y[0]]) - 1
    else:
        lo = x[idx-1]
        if half:
            lo = lo + (mid - lo) // 2
    if idx == len(x) - 1:
        hi = max([x[-1], y[-1]]) + 1
    else:
        hi = x[idx+1]
        if half:
            hi = mid + (hi - mid) // 2
    return lo, hi


def _get_match(x, y, half=True):
    """ return matches between x and y """
    match = []
    for x_idx, a in enumerate(x):
        lo_x, hi_x = _get_bounds(x, y, x_idx, half)
        y_win = [n for n, v in enumerate(y)
                if lo_x < v <= hi_x]
        for y_idx in y_win:
            lo_y, hi_y = _get_bounds(y, x, y_idx, half)
            b = y[y_idx]
            if lo_y < a <= hi_y:
                match.append((a, b))
    return match

def compare_markings(x, y, thresh=None, inside=False):
    match_half = _get_match(x, y, half=True)
    match_full = _get_match(x, y, half=False)
    match_conflict = set(match_full) - set(match_half)

    keep = match_half.copy()
    for lb, ub in match_conflict:
        for i,j in keep:
            if i==lb or j==ub:
                break
        else:
            #both end points not already matched
            keep.append((lb, ub))

    if thresh: # purge matches too distant
        keep = [(i,j) for i,j in keep if abs(i-j) <= thresh]

    cx, cy = zip(*keep) if keep else ([], [])
    x_only = sorted(set(x) - set(cx))
    y_only = sorted(set(y) - set(cy))

    cd = [(i, (j-i)) for i,j in keep]
    common, diff = zip(*cd) if cd else ([], [])
    r = tuple(map(array, [x_only, y_only, common, diff]))

    if not inside: return r
    else: return r, locals()

def compare_cycles(x, y, HP, vt=True, centered=False):
    """ Find all markings in y within a glottal cycle
        derived from GCI markings in x, to within a
        maximum half-period in samples.
    """

    x = sorted(x)
    y = sorted(y)

    cycles = {i:[] for i in x}
    bounds = {}
    other = []

    # handle edge cases in x
    if not x: return {}, {}, y
    x = [x[0] - 3*HP] + x + [x[-1] + 3*HP]
    b = 0

    for a in range(1, len(x)-1):
        lo, mid, hi = x[a-1], x[a], x[a+1]
        # Adjust bounds to be halfway between
        # previous and next GCI markings.
        lo = lo + (mid - lo) // 2
        hi = mid + (hi - mid) // 2

        if mid - HP > lo:
            if vt: # voicing transition
                # likely at onset of voicing,
                # use next period
                lo = max([mid-HP, 2*mid-hi])
            else:
                lo = mid - HP

        if mid + HP < hi:
            if vt:
                # likely at offset of voicing,
                # use previous period
                hi = min([mid+HP, 2*mid-lo])
            else:
                hi = mid + HP

        if centered:
            # shrink bounds such that mid is centered
            d = min([hi-mid, mid-lo])
            lo, hi = mid-d, mid+d

        bounds[mid] = (lo, hi)
        # find all the indices in y within bounds
        while b < len(y) and y[b] < hi:
            if y[b] >= lo:
                cycles[mid].append(y[b])
            else:
                other.append(y[b])
            b += 1

    other.extend(y[b:])  # leftover
    return cycles, bounds, other

def cycle_stats(cycles):
    """ Compute the number of hits, misses, alarms
        using the output of compare_cycles."""
    v = list(map(len, cycles.values()))
    hit   = v.count(1)
    miss  = v.count(0)
    alarm = len(v) - miss - hit
    return hit, miss, alarm
