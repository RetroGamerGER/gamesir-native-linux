#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Plot saved target telemetry only; no device or application imports."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from project_paths import PROJECT, RESULTS, local_directory

CAPTURE = local_directory("capture_dir")
analysis = json.loads((PROJECT / "docs/imu-calibration-analysis.json").read_text())
rows = json.loads((CAPTURE / "derived/telemetry-raw.json").read_text())
assert analysis["wire_samples_verified"] == len(rows) == 12204
t = [r["seconds"] for r in rows]
accel = [math.sqrt(sum(v*v for v in r["accel_raw"])) for r in rows]
gyro = [math.sqrt(sum(v*v for v in r["gyro_raw"])) for r in rows]
quiet = analysis["global_statistics"]["quiet_windows"]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(3, 1, figsize=(11, 9), layout="constrained")
fig.suptitle("GameSir G7 Pro: 12.204 gespeicherte IMU-Pakete\nOffline-Auswertung; keine bestätigte physikalische Kalibrierung", fontsize=15)
axes[0].plot(t, accel, color="#2563a6", lw=.65)
axes[0].axhline(8192, color="#bd431d", ls="--", lw=1.3, label="Kandidat: 8.192 Zähler/g")
axes[0].set(title="Alle Beschleunigungswerte: Bewegung verändert auch die Vektorlänge", ylabel="Vektorlänge (Rohzähler)")
axes[0].legend(loc="upper right")
for q in quiet:
    s=q["summary"]["accel_norm_raw"]
    x=sum(q["relative_window_seconds"])/2
    axes[1].vlines(x,s["p05"],s["p95"],color="#a9bed4",lw=2)
    axes[1].plot(x,s["median"],"o",color="#2563a6",ms=3.5)
axes[1].axhline(8192,color="#bd431d",ls="--",lw=1.3)
lower=min(q["summary"]["accel_norm_raw"]["p05"] for q in quiet)-5
upper=max(q["summary"]["accel_norm_raw"]["p95"] for q in quiet)+5
axes[1].set(title="29 ruhige Zweiersekunden-Fenster (Heuristik): Median und 5.-95. Perzentil",ylabel="Vektorlänge (Rohzähler)",ylim=(lower,upper))
axes[1].text(.02,.05,"3.624 Samples; Schwerkraftrichtungen liegen weniger als 2° auseinander",transform=axes[1].transAxes,fontsize=9)
axes[2].plot(t,gyro,color="#23774e",lw=.65)
cue=analysis["phase_windows"]["gyro_yaw"]["cue_seconds"]
burst=cue+analysis["motion_timing"]["seconds_after_yaw_cue"]
axes[2].axvline(cue,color="#657485",ls="--",lw=1.2,label="Signal zur ersten Drehung")
axes[2].axvline(burst,color="#bd431d",ls=":",lw=1.5,label="Erster anhaltender Ausschlag danach")
axes[2].set(title="Gyro: Signalzeit ist kein bestätigter Bewegungsbeginn",ylabel="Vektorlänge (Rohzähler)",xlabel="Sekunden seit verifiziertem Recorder-Start (Host-Zeit)")
axes[2].legend(loc="upper right")
for ax in axes:
    ax.set_xlim(t[0]-1,t[-1]+1)
    ax.grid(alpha=.2)
RESULTS.mkdir(parents=True, exist_ok=True)
output=RESULTS/"imu-statistik.png"
fig.savefig(output,dpi=170)
plt.close(fig)
print(output)
