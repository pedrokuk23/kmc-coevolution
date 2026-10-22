# Figures S2-1 and S2-2 of Supplementary Material S2 (X-43A documentary record). Values and dates as reported in
# the cited public documents; they are engineering predictions and calendar dates, not KMC scores.
import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})

# S2-1: roll-axis gain margin before and after nominal model correction (mishap report [14], pp. 6-7)
fig, ax = plt.subplots(figsize=(6.5, 3.25))
ax.axvline(6, color="#333333", ls="--", lw=1.4)
ax.text(6.1, 0.62, "Requirement\n6 dB", va="center")
ax.plot(8, 1, "o", ms=10, color="#0072B2"); ax.text(8.2, 1, "8 dB", va="center")
ax.annotate("", xy=(0.9, 0), xytext=(1.85, 0), arrowprops=dict(arrowstyle="->", color="#D55E00", lw=2))
ax.plot(2, 0, marker="<", ms=12, mfc="white", mec="#D55E00", mew=2)
ax.text(2.35, 0, "<2 dB (exact value\nnot reported)", va="center", fontsize=9.5)
ax.set_yticks([0, 1]); ax.set_yticklabels(["Corrected nominal\nprediction", "Preflight prediction\nreported retrospectively"])
ax.set_ylim(-0.6, 1.5); ax.set_xlim(0, 9.4); ax.set_xlabel("Roll-axis gain margin (dB)")
for x in (2, 4, 6, 8): ax.axvline(x, color="#E6E6E6", lw=0.8, zorder=0)
fig.tight_layout(); fig.savefig("S2_Fig1.png"); plt.close(fig)

# S2-2: event dates and selected documents ([14], [61], [57])
rows = [("First-flight mishap", dt.date(2001, 6, 2), dt.date(2003, 5, 8)),
        ("Actuator test-setup incident", dt.date(2004, 2, 11), dt.date(2004, 2, 17)),
        ("Return-to-flight mission", dt.date(2004, 3, 27), dt.date(2004, 4, 7))]
fig, ax = plt.subplots(figsize=(6.5, 3.7))
for i, (lab, ev, doc) in enumerate(rows):
    y = len(rows) - i
    ax.plot([ev, doc], [y, y], color="#777777", lw=1.2)
    ax.plot(ev, y, "o", ms=8, color="#0072B2"); ax.plot(doc, y, "s", ms=8, mfc="white", mec="#222222")
    ax.text(dt.date(2001, 5, 15), y + 0.28, f"{lab}: {ev.isoformat()} / {doc.isoformat()}", fontsize=9.5)
ax.plot([], [], "o", color="#0072B2", label="Event"); ax.plot([], [], "s", mfc="white", mec="#222222", label="Selected document")
ax.legend(frameon=False, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.08))
ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.set_ylim(0.5, 3.8)
ax.set_xlim(dt.date(2001, 5, 1), dt.date(2004, 7, 1)); ax.set_xlabel("Calendar date")
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7))); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(ax.get_xticklabels(), fontsize=9)
fig.tight_layout(); fig.savefig("S2_Fig2.png"); plt.close(fig)
