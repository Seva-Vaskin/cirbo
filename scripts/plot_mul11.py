import csv
import matplotlib.pyplot as plt
from collections import defaultdict

data = defaultdict(lambda: {"depth": [], "total": [], "cube": [], "conquer": [], "cubes": []})

with open("reports/miter_mul11_cnc.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row["file"].replace("mul_11_", "").replace(".aig", "")
        d = int(row["depth"])
        data[name]["depth"].append(d)
        data[name]["total"].append(float(row["total_time"]))
        data[name]["cube"].append(float(row["cube_time"]))
        data[name]["conquer"].append(float(row["conquer_time"]))
        data[name]["cubes"].append(int(row["cubes"]))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for name, vals in sorted(data.items()):
    axes[0].plot(vals["depth"], vals["total"], marker="o", label=name)
    axes[1].plot(vals["depth"], vals["conquer"], marker="s", label=name)
    axes[2].plot(vals["depth"], vals["cube"], marker="^", label=name)
    axes[3].plot(vals["depth"], vals["cubes"], marker="D", label=name)

panels = [
    ("Total Time vs Depth", "Time (s)"),
    ("Conquer Time vs Depth", "Time (s)"),
    ("Cube Time vs Depth", "Time (s)"),
    ("Number of Cubes vs Depth", "Cubes"),
]
for ax, (title, ylabel) in zip(axes, panels):
    ax.set_xlabel("Depth")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    all_depths = sorted({d for vals in data.values() for d in vals["depth"]})
    ax.set_xticks(all_depths)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

fig.suptitle("CnCv2 + Kissat on mul_11 miters", fontsize=14)
plt.tight_layout()
plt.savefig("reports/miter_mul11_cnc_plot.png", dpi=150, bbox_inches="tight")
print("Saved to reports/miter_mul11_cnc_plot.png")
