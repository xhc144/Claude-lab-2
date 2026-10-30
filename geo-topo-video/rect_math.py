# -*- coding: utf-8 -*-
"""第五题用到的数值计算：闭曲线、点对映射、内接矩形族。"""
import json
import os

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.abspath(__file__))
CENTER = np.array([0.0, 0.0])


def radius(s):
    th = 2 * np.pi * s
    return 2.0 * (1 + 0.24 * np.cos(2 * th + 0.5) + 0.15 * np.sin(3 * th) + 0.07 * np.cos(5 * th + 1.0))


def gamma(s):
    s = np.asarray(s, float)
    th = 2 * np.pi * s
    r = radius(s)
    return np.stack([CENTER[0] + r * np.cos(th), CENTER[1] + r * np.sin(th)], axis=-1)


def lift(s, t):
    """无序点对 {γ(s), γ(t)} → (中点 x, 中点 y, 距离)。"""
    a, b = gamma(s), gamma(t)
    m = (a + b) / 2
    d = np.linalg.norm(a - b, axis=-1)
    return np.concatenate([m, d[..., None]], axis=-1)


def residual(x):
    s1, t1, s2, t2 = x
    return lift(s1, t1) - lift(s2, t2)


def rect_from(x):
    s1, t1, s2, t2 = x
    A, C = gamma(s1), gamma(t1)
    B, D = gamma(s2), gamma(t2)
    return np.array([A, B, C, D])


def distinct(x, tol=0.03):
    s1, t1, s2, t2 = np.mod(x, 1.0)
    def cd(a, b):
        d = abs(a - b) % 1.0
        return min(d, 1 - d)
    pts = [s1, t1, s2, t2]
    return all(cd(pts[i], pts[j]) > tol for i in range(4) for j in range(i + 1, 4))


def find_seeds(n=500):
    s = np.linspace(0, 1, n, endpoint=False)
    I, J = np.triu_indices(n, 1)
    P = lift(s[I], s[J])
    tree = cKDTree(P)
    pairs = tree.query_pairs(0.02)
    seeds = []
    for a, b in pairs:
        x = np.array([s[I[a]], s[J[a]], s[I[b]], s[J[b]]])
        if distinct(x, 0.05):
            seeds.append(x)
    return seeds


def refine(x0, fix_index=None, fix_value=None):
    if fix_index is None:
        r = least_squares(residual, x0, xtol=1e-12, ftol=1e-12)
        return r.x, np.linalg.norm(r.fun)
    idx = [i for i in range(4) if i != fix_index]

    def f(y):
        x = np.empty(4)
        x[fix_index] = fix_value
        x[idx] = y
        return residual(x)
    r = least_squares(f, x0[idx], xtol=1e-13, ftol=1e-13)
    x = np.empty(4)
    x[fix_index] = fix_value
    x[idx] = r.x
    return x, np.linalg.norm(r.fun)


def aspect(x):
    A, B, C, D = rect_from(x)
    a, b = np.linalg.norm(B - A), np.linalg.norm(C - B)
    return min(a, b) / max(a, b)


def trace_family(x0, steps=400, h=0.0025):
    """以 s1 为参数做延拓，追踪一族连续变化的内接矩形。"""
    fam = [x0]
    for direction in (+1, -1):
        x = x0.copy()
        for _ in range(steps):
            x_new, err = refine(x, 0, x[0] + direction * h)
            if err > 1e-7 or not distinct(x_new, 0.02) or np.max(np.abs(x_new - x)) > 0.05:
                break
            x = x_new
            if direction > 0:
                fam.append(x)
            else:
                fam.insert(0, x)
    return np.array(fam)


if __name__ == "__main__":
    seeds = find_seeds()
    print("seeds", len(seeds))
    rng = np.random.default_rng(0)
    best = []
    for x0 in [seeds[i] for i in rng.choice(len(seeds), min(60, len(seeds)), replace=False)]:
        x, err = refine(x0)
        if err < 1e-9 and distinct(x, 0.05):
            A, B, C, D = rect_from(x)
            u, v = C - A, D - B
            area = 0.5 * abs(u[0] * v[1] - u[1] * v[0])
            best.append((area, x))
    best.sort(key=lambda t: -t[0])
    print("solutions", len(best))
    fams = []
    for area, x in best[:12]:
        fam = trace_family(x)
        asp = [aspect(f) for f in fam]
        fams.append((len(fam), area, max(asp), min(asp), fam))
        print(len(fam), round(area, 3), "aspect range", round(min(asp), 3), round(max(asp), 3))
    fams.sort(key=lambda t: (-t[2], -t[0]))
    out = {"family": fams[0][4].tolist(), "rect": best[0][1].tolist()}
    with open(os.path.join(ROOT, "rect_family.json"), "w") as f:
        json.dump(out, f)
