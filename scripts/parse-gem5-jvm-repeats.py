#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import csv
import re
import statistics
from pathlib import Path


KEYS = {
    "simTicks": "ticks",
    "simInsts": "instructions",
    "board.processor.switch.core.numCycles": "cycles",
    "board.processor.switch.core.mmu.dtb.misses": "dtlb_misses",
    "board.processor.switch.core.mmu.itb.misses": "itlb_misses",
    "board.processor.switch.core.mmu.dtb.walker.num_4kb_walks": "dwalk_4k",
    "board.processor.switch.core.mmu.dtb.walker.num_16kb_walks": "dwalk_16k",
    "board.processor.switch.core.mmu.dtb.walker.num_32kb_walks": "dwalk_32k",
    "board.processor.switch.core.mmu.dtb.walker.num_64kb_walks": "dwalk_64k",
}


def roi_ticks(run_log):
    text = run_log.read_text(errors="replace")
    values = re.findall(r"Workload ROI ticks: \[([0-9]+)\]", text)
    exits = re.findall(r"Exiting .* code=([0-9]+)", text)
    if not values or not exits or exits[-1] != "0":
        raise ValueError(f"{run_log}: run is incomplete or failed")
    return int(values[-1])


def roi_stats(stats_file, expected_ticks):
    sections = stats_file.read_text(errors="replace").split(
        "---------- Begin Simulation Statistics ----------"
    )[1:]
    matches = []
    for section in sections:
        values = {name: 0 for name in KEYS.values()}
        for line in section.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] in KEYS:
                values[KEYS[fields[0]]] = int(float(fields[1]))
        if values["ticks"] == expected_ticks:
            matches.append(values)
    if len(matches) != 1:
        raise ValueError(
            f"{stats_file}: expected one ROI section, got {len(matches)}"
        )
    return matches[0]


parser = argparse.ArgumentParser()
parser.add_argument("first_root", type=Path)
parser.add_argument("repeat_root", type=Path)
args = parser.parse_args()

rows = []
for repeat in (1, 2, 3):
    for config in ("B", "D"):
        if repeat == 1:
            run_dir = args.first_root / f"renaissance-future-genetic-{config}"
        else:
            run_dir = (
                args.repeat_root
                / f"repeat{repeat}-renaissance-future-genetic-{config}"
            )
        ticks = roi_ticks(run_dir / "run.log")
        row = roi_stats(run_dir / "stats.txt", ticks)
        row["repeat"] = repeat
        row["config"] = config
        row["cpi"] = row["cycles"] / row["instructions"]
        rows.append(row)

comparisons = []
for repeat in (1, 2, 3):
    before = next(r for r in rows if r["repeat"] == repeat and r["config"] == "B")
    after = next(r for r in rows if r["repeat"] == repeat and r["config"] == "D")
    comparisons.append({
        "repeat": repeat,
        "tick_gain_pct": 100.0 * (before["ticks"] - after["ticks"]) / before["ticks"],
        "instruction_delta_pct": 100.0 * (after["instructions"] - before["instructions"]) / before["instructions"],
        "cpi_delta_pct": 100.0 * (after["cpi"] - before["cpi"]) / before["cpi"],
        "dtlb_reduction_pct": 100.0 * (before["dtlb_misses"] - after["dtlb_misses"]) / before["dtlb_misses"],
        "itlb_reduction_pct": 100.0 * (before["itlb_misses"] - after["itlb_misses"]) / before["itlb_misses"],
    })

row_columns = ["repeat", "config", *KEYS.values(), "cpi"]
with (args.repeat_root / "summary.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=row_columns)
    writer.writeheader()
    writer.writerows(rows)

comparison_columns = list(comparisons[0])
with (args.repeat_root / "comparison.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=comparison_columns)
    writer.writeheader()
    writer.writerows(comparisons)

for row in comparisons:
    print(
        f"repeat {row['repeat']}: ticks={row['tick_gain_pct']:.6f}% "
        f"instructions={row['instruction_delta_pct']:.6f}% "
        f"CPI={row['cpi_delta_pct']:.6f}% "
        f"DTLB={row['dtlb_reduction_pct']:.6f}% "
        f"iTLB={row['itlb_reduction_pct']:.6f}%"
    )
for key in comparison_columns[1:]:
    print(f"median {key}={statistics.median(r[key] for r in comparisons):.6f}%")
