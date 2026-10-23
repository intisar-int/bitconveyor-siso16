"""
Regenerates the figures that can be rebuilt from this repo:
  results/figures/simulation_waveform.png  (from results/logs/siso_16.vcd)
  results/figures/ppa_comparison.png       (from synthesis/*.csv)
Run `make sim` first so the VCD exists.   Needs numpy + matplotlib.
"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

SLOW, FAST = "#2a78d6", "#eb6834"                 # validated categorical slots 1-2
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9.5, "legend.frameon": False,
})


# ------------------------------------------------------------------ VCD parsing
def read_vcd(path):
    ids, names, scope, t, sig = {}, {}, [], 0, {}
    for line in Path(path).read_text().splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "$scope":
            scope.append(p[2])
        elif p[0] == "$upscope":
            scope.pop()
        elif p[0] == "$var":
            if len(scope) == 1:                              # top-level testbench signals only
                ids[p[3]] = p[4]
                sig[p[4]] = []
        elif p[0].startswith("#"):
            t = int(p[0][1:])
        elif p[0][0] in "01xz" and len(p[0]) > 1 and p[0][1:] in ids:
            sig[ids[p[0][1:]]].append((t, p[0][0]))
        elif p[0][0] == "b" and len(p) == 2 and p[1] in ids:
            sig[ids[p[1]]].append((t, p[0][1:]))
    return sig


def sample(events, t):
    v = None
    for tt, val in events:
        if tt <= t:
            v = val
        else:
            break
    return v


# ------------------------------------------------------------------ Figure 1: waveform
def waveform():
    sig = read_vcd(ROOT / "results" / "logs" / "siso_16.vcd")
    T_END = 736_000                                           # ps
    rows = [("clk", 1), ("rst", 1), ("load", 1), ("left_right", 1), ("Din", 1),
            ("A", 16), ("shift_reg_out", 16), ("Dout", 1)]
    # test-case boundaries in clock cycles (edge k occurs at 5 + 10(k-1) ns)
    tcs = [("TC1", 1), ("TC2", 1), ("TC3", 8), ("TC4", 8), ("TC5", 5), ("TC6", 4), ("TC7", 2),
           ("TC8", 4), ("TC9", 1), ("TC10", 1), ("TC11", 34), ("TC12", 5)]
    starts, c = [], 0
    for name, n in tcs:
        starts.append((name, 10 * c, 10 * (c + n)))           # ns, test-case window
        c += n
    windows = [(0, 362), (362, 740)]
    fig, axes = plt.subplots(2, 1, figsize=(13, 8.6), constrained_layout=True)
    for ax, (x0, x1) in zip(axes, windows):
        n = len(rows)
        ax.set_xlim(x0, x1)
        ax.set_ylim(-0.4, n + 0.9)
        ax.set_yticks([n - 1 - i + 0.4 for i in range(n)], [r[0] for r in rows])
        ax.set_xlabel("Time (ns)")
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for k, (name, a, b) in enumerate(starts):             # test-case bands
            if b > x0 and a < x1:
                ax.add_patch(Rectangle((max(a, x0), n + 0.05), min(b, x1) - max(a, x0), 0.75,
                                       color=(SLOW if k % 2 == 0 else "#7fb0ec"), alpha=0.22, lw=0))
                ax.text((max(a, x0) + min(b, x1)) / 2, n + 0.42, name, ha="center", va="center",
                        fontsize=8.5, fontweight="bold", color=INK)
        for i, (name, width) in enumerate(rows):
            y0 = n - 1 - i
            ev = sig[name]
            times = [t for t, _ in ev] + [T_END]
            if width == 1:
                xs, ys = [], []
                for (t, v), tn in zip(ev, times[1:]):
                    lvl = 1 if v == "1" else 0
                    xs += [t / 1000, tn / 1000]
                    ys += [y0 + 0.1 + 0.6 * lvl] * 2
                ax.step(xs, ys, where="post", color=INK, lw=1.2)
            else:
                for (t, v), tn in zip(ev, times[1:]):
                    a, b = t / 1000, tn / 1000
                    if b < x0 or a > x1:
                        continue
                    ax.add_patch(Rectangle((a, y0 + 0.08), b - a, 0.64, fc="#eaf2fc", ec=SLOW, lw=0.9))
                    if "x" not in v and (min(b, x1) - max(a, x0)) > 8:
                        ax.text((max(a, x0) + min(b, x1)) / 2, y0 + 0.4, f"{int(v, 2):04X}",
                                ha="center", va="center", fontsize=7.2, color=INK)
    fig.suptitle("siso_16 self-checking testbench: 12 test cases, 75 checks, 0 errors (Icarus Verilog)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.savefig(FIG / "simulation_waveform.png", dpi=170)
    plt.close(fig)


# ------------------------------------------------------------------ Figure 2: PPA
def ppa():
    rows = {r["corner"]: r for r in csv.DictReader(open(ROOT / "synthesis" / "ppa_summary.csv"))}
    gates = {}
    for r in csv.DictReader(open(ROOT / "synthesis" / "mapped_gates.csv")):
        gates.setdefault(r["cell"], {})[r["corner"]] = float(r["area_um2"])
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.6), constrained_layout=True,
                            gridspec_kw={"width_ratios": [1.5, 0.7, 1.4]})
    s, f = rows["slow"], rows["fast"]
    ax = axs[0]
    labs = ["Internal", "Net", "Switching\n(total dynamic)"]
    sv = [float(s[k]) for k in ("internal_nW", "net_nW", "switching_nW")]
    fv = [float(f[k]) for k in ("internal_nW", "net_nW", "switching_nW")]
    xs = range(3)
    b1 = ax.bar([x - 0.2 for x in xs], sv, 0.38, color=SLOW, label="Slow  (0.9 V, 125 °C)")
    b2 = ax.bar([x + 0.2 for x in xs], fv, 0.38, color=FAST, label="Fast  (1.1 V, 0 °C)")
    for bs in (b1, b2):
        for b in bs:
            ax.annotate(f"{b.get_height():,.0f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=8.5)
    ax.set_xticks(list(xs), labs)
    ax.set(title="Dynamic power", ylabel="Power (nW)", ylim=(0, 9000))
    ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)
    ax.legend(loc="upper left")

    ax = axs[1]
    vals = [float(s["leakage_nW"]), float(f["leakage_nW"])]
    bars = ax.bar([0, 1], vals, 0.55, color=[SLOW, FAST])
    for b in bars:
        ax.annotate(f"{b.get_height():.2f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=8.5)
    ax.set_xticks([0, 1], ["Slow", "Fast"])
    ax.set(title="Leakage power", ylabel="Power (nW)", ylim=(0, 12))
    ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)

    ax = axs[2]
    cells = ["DFFQXL", "MX2XL", "AOI22X1", "NOR2X1", "AOI22XL", "INVX1 / INVXL"]
    def area(c, corner):
        if c.startswith("INV"):
            return gates["INVX1" if corner == "slow" else "INVXL"][corner]
        return gates.get(c, {}).get(corner, 0.0)
    ys = list(range(len(cells)))[::-1]
    ax.barh([y + 0.2 for y in ys], [area(c, "slow") for c in cells], 0.38, color=SLOW)
    ax.barh([y - 0.2 for y in ys], [area(c, "fast") for c in cells], 0.38, color=FAST)
    for y, c in zip(ys, cells):
        for dy, corner in ((0.2, "slow"), (-0.2, "fast")):
            v = area(c, corner)
            if v:
                ax.annotate(f"{v:.3f}", (v, y + dy), va="center", xytext=(3, 0), textcoords="offset points", fontsize=8)
    ax.set_yticks(ys, cells)
    ax.set(title="Cell area (total 178.182 µm² in both)", xlabel="Area (µm²)", xlim=(0, 105))
    ax.grid(axis="x", color=GRID, lw=0.7); ax.set_axisbelow(True)
    fig.suptitle("Same netlist area, very different power: slow vs. fast corner (66 cells each)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.savefig(FIG / "ppa_comparison.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    waveform()
    ppa()
    print("figures ->", FIG)
