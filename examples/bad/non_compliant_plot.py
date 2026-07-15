from __future__ import annotations

import matplotlib.pyplot as plt


fig, ax = plt.subplots()
ax.plot([1, 2, 3], [0.7, 0.8, 0.9], color="red", linewidth=3, marker="o")
ax.minorticks_on()
ax.set_title("A long explanatory title that should be a caption")
ax.set_xlabel("step1", fontsize=5)
ax.set_ylabel("Length 10mm")
fig.savefig("non_compliant_plot.png", dpi=150)
