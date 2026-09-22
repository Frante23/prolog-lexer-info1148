from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (ROOT / "docs" / "figures", ROOT / "informe" / "figuras")


def save(fig, filename):
    """Genera una imagen y sincroniza la copia utilizada por el informe."""
    for directory in OUTPUTS:
        directory.mkdir(parents=True, exist_ok=True)
    destination = OUTPUTS[0] / filename
    fig.savefig(destination, bbox_inches="tight", facecolor="white")
    for directory in OUTPUTS[1:]:
        shutil.copyfile(destination, directory / filename)
    plt.close(fig)


def arrow(ax, start, end, label, bend=0.0, offset=(0, 0), size=11):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.5,
        color="#25364A",
        connectionstyle=f"arc3,rad={bend}",
        shrinkA=18,
        shrinkB=18,
    )
    ax.add_patch(patch)
    x = (start[0] + end[0]) / 2 + offset[0]
    y = (start[1] + end[1]) / 2 + offset[1] + bend * 0.8
    ax.text(x, y, label, ha="center", va="center", fontsize=size, color="#111111", backgroundcolor="white")


def loop(ax, center, label, above=True, size=9):
    x, y = center
    dy = 0.23 if above else -0.23
    start = (x - 0.22, y + dy)
    end = (x + 0.22, y + dy)
    rad = -1.45 if above else 1.45
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.4,
        color="#25364A",
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(patch)
    ax.text(x, y + (0.72 if above else -0.72), label, ha="center", va="center", fontsize=size, backgroundcolor="white")


def state(ax, xy, name, accepting=False, subtitle=None, radius=0.35):
    ax.add_patch(Circle(xy, radius, facecolor="white", edgecolor="#173B63", linewidth=1.8))
    if accepting:
        ax.add_patch(Circle(xy, radius - 0.06, fill=False, edgecolor="#173B63", linewidth=1.2))
    ax.text(xy[0], xy[1] + (0.06 if subtitle else 0), name, ha="center", va="center", fontsize=12, fontweight="bold")
    if subtitle:
        ax.text(xy[0], xy[1] - 0.13, subtitle, ha="center", va="center", fontsize=8)


def setup(width=10, height=4):
    fig, ax = plt.subplots(figsize=(width, height), dpi=180)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def identifiers():
    fig, ax = setup(10, 4.4)
    q0, qa, qv, qu = (1.4, 2.1), (4.7, 3.2), (7.7, 1.3), (4.5, 0.65)
    state(ax, q0, "q0")
    state(ax, qa, "qA", True, "ATOMO (*)")
    state(ax, qv, "qV", True, "VARIABLE")
    state(ax, qu, "q_", True, "ANONIMA")
    arrow(ax, (0.25, 2.1), q0, "inicio", offset=(0, 0.22))
    arrow(ax, q0, qa, "[a-z]", bend=-0.07, offset=(0, 0.24))
    arrow(ax, q0, qv, "[A-Z]", bend=0.06, offset=(0, -0.18))
    arrow(ax, q0, qu, "_", bend=0.08, offset=(0, -0.28))
    loop(ax, qa, "[A-Za-z0-9_]", above=True)
    loop(ax, qv, "[A-Za-z0-9_]", above=False)
    arrow(ax, qu, qv, "[A-Za-z0-9_]", bend=-0.08, offset=(0, 0.22), size=9)
    ax.set_xlim(-0.1, 9.2)
    ax.set_ylim(0.0, 4.2)
    ax.set_title("AFD para identificadores", fontsize=14, fontweight="bold", color="#173B63")
    fig.text(0.5, 0.01, "(*) is y mod se reclasifican como OPERADOR_ARITMETICO.",
             ha="center", fontsize=9, color="#25364A")
    fig.tight_layout()
    save(fig, "afd_identificadores.png")


def numbers():
    fig, ax = setup(12, 5)
    pts = {
        "q0": (0.9, 2.5), "qI": (3.0, 2.5), "qP": (5.1, 3.7),
        "qR": (7.2, 3.7), "qE": (5.1, 1.25), "qS": (7.2, 1.25), "qX": (9.4, 1.25)
    }
    state(ax, pts["q0"], "q0")
    state(ax, pts["qI"], "qI", True, "ENTERO")
    state(ax, pts["qP"], "q.")
    state(ax, pts["qR"], "qR", True, "REAL")
    state(ax, pts["qE"], "qE")
    state(ax, pts["qS"], "qS")
    state(ax, pts["qX"], "qExp", True, "REAL")
    arrow(ax, (-0.1, 2.5), pts["q0"], "inicio", offset=(0, 0.24))
    arrow(ax, pts["q0"], pts["qI"], "[0-9]", offset=(0, 0.22))
    loop(ax, pts["qI"], "[0-9]", above=True)
    arrow(ax, pts["qI"], pts["qP"], ".", bend=-0.08, offset=(0, 0.18))
    arrow(ax, pts["qP"], pts["qR"], "[0-9]", offset=(0, 0.22))
    loop(ax, pts["qR"], "[0-9]", above=True)
    arrow(ax, pts["qI"], pts["qE"], "e | E", bend=0.08, offset=(0, -0.18))
    arrow(ax, pts["qR"], pts["qE"], "e | E", bend=0.12, offset=(-0.1, -0.12))
    arrow(ax, pts["qE"], pts["qS"], "+ | -", offset=(0, 0.22))
    arrow(ax, pts["qE"], pts["qX"], "[0-9]", bend=-0.32, offset=(0.0, 0.92))
    arrow(ax, pts["qS"], pts["qX"], "[0-9]", offset=(0, 0.22))
    loop(ax, pts["qX"], "[0-9]", above=False)
    ax.set_xlim(-0.4, 11.0)
    ax.set_ylim(0.0, 4.8)
    ax.set_title("AFD para enteros y reales sin signo", fontsize=14, fontweight="bold", color="#173B63")
    fig.tight_layout()
    save(fig, "afd_numeros.png")


def operators():
    fig, ax = setup(11, 5.5)
    q0, qe, qbs = (1.0, 2.7), (3.4, 4.1), (3.4, 1.2)
    qeq, qdot, qddot = (6.0, 4.65), (6.0, 3.35), (8.7, 3.35)
    qbeq, qbplus = (6.0, 1.75), (6.0, 0.55)
    qbee = (8.7, 1.75)
    for xy, name, accept, sub in [
        (q0, "q0", False, None), (qe, "q=", True, "="), (qbs, "q\\", False, None),
        (qeq, "q==", True, "=="), (qdot, "q=.", False, None), (qddot, "q=..", True, "=.."),
        (qbeq, "q\\=", True, "\\="), (qbplus, "q\\+", True, "\\+"),
        (qbee, "q\\==", True, "\\=="),
    ]:
        state(ax, xy, name, accept, sub)
    arrow(ax, (-0.1, 2.7), q0, "inicio", offset=(0, 0.22))
    arrow(ax, q0, qe, "=", offset=(0, 0.22))
    arrow(ax, q0, qbs, "\\", offset=(0, -0.22))
    arrow(ax, qe, qeq, "=", bend=-0.08, offset=(0, 0.16))
    arrow(ax, qe, qdot, ".", bend=0.08, offset=(0, -0.16))
    arrow(ax, qdot, qddot, ".", offset=(0, 0.22), size=10)
    arrow(ax, qbs, qbeq, "=", bend=-0.08, offset=(0, 0.15))
    arrow(ax, qbs, qbplus, "+", bend=0.08, offset=(0, -0.18))
    arrow(ax, qbeq, qbee, "=", offset=(0, 0.23))
    ax.set_xlim(-0.4, 10.3)
    ax.set_ylim(0.0, 5.35)
    ax.set_title("Trie de operadores y máxima coincidencia", fontsize=14, fontweight="bold", color="#173B63")
    fig.tight_layout()
    save(fig, "afd_operadores.png")


if __name__ == "__main__":
    identifiers()
    numbers()
    operators()
