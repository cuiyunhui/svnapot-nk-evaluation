#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import csv
import re
from pathlib import Path


WORKLOADS = ("spec-mcf", "spec-xalanc")
CONFIGS = ("A", "B", "C", "D")
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
    "board.processor.switch.core.mmu.itb.walker.num_4kb_walks": "iwalk_4k",
    "board.processor.switch.core.mmu.itb.walker.num_16kb_walks": "iwalk_16k",
    "board.processor.switch.core.mmu.itb.walker.num_32kb_walks": "iwalk_32k",
    "board.processor.switch.core.mmu.itb.walker.num_64kb_walks": "iwalk_64k",
}


def parse_run(run_dir):
    log = (run_dir / "run.log").read_text(errors="replace")
    roi = re.findall(r"Workload ROI ticks: \[([0-9]+)\]", log)
    exits = re.findall(r"Exiting .* code=([0-9]+)", log)
    if not roi or not exits or exits[-1] != "0":
        raise ValueError(f"{run_dir}: incomplete or failed run")
    expected_ticks = int(roi[-1])

    sections = (run_dir / "stats.txt").read_text(errors="replace").split(
        "---------- Begin Simulation Statistics ----------"
    )[1:]
    matches = []
    for section in sections:
        row = {name: 0 for name in KEYS.values()}
        for line in section.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] in KEYS:
                row[KEYS[fields[0]]] = int(float(fields[1]))
        if row["ticks"] == expected_ticks:
            matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: ROI statistics section mismatch")
    return matches[0]


parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
parser.add_argument(
    "--workloads",
    default=",".join(WORKLOADS),
    help="comma-separated workload names",
)
args = parser.parse_args()
selected_workloads = tuple(args.workloads.split(","))
if not selected_workloads or any(w not in WORKLOADS for w in selected_workloads):
    parser.error(f"workloads must be selected from {','.join(WORKLOADS)}")

rows = []
for workload in selected_workloads:
    for config in CONFIGS:
        row = parse_run(args.root / f"{workload}-{config}")
        row["workload"] = workload
        row["config"] = config
        row["cpi"] = row["cycles"] / row["instructions"]
        rows.append(row)

columns = ["workload", "config", *KEYS.values(), "cpi"]
with (args.root / "summary.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

comparisons = []
for workload in selected_workloads:
    by_config = {r["config"]: r for r in rows if r["workload"] == workload}
    for before_name, after_name, purpose in (
        ("A", "B", "add_16k"),
        ("A", "C", "add_32k"),
        ("B", "D", "add_32k_with_16k"),
        ("A", "D", "add_16k_and_32k"),
    ):
        before = by_config[before_name]
        after = by_config[after_name]
        comparisons.append({
            "workload": workload,
            "comparison": f"{after_name}_vs_{before_name}",
            "purpose": purpose,
            "tick_gain_pct": 100.0 * (before["ticks"] - after["ticks"]) / before["ticks"],
            "instruction_delta_pct": 100.0 * (after["instructions"] - before["instructions"]) / before["instructions"],
            "cpi_delta_pct": 100.0 * (after["cpi"] - before["cpi"]) / before["cpi"],
            "dtlb_reduction_pct": 100.0 * (before["dtlb_misses"] - after["dtlb_misses"]) / before["dtlb_misses"],
            "itlb_reduction_pct": 100.0 * (before["itlb_misses"] - after["itlb_misses"]) / before["itlb_misses"],
        })

comparison_columns = list(comparisons[0])
with (args.root / "comparison.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=comparison_columns)
    writer.writeheader()
    writer.writerows(comparisons)

for row in comparisons:
    print(
        f"{row['workload']} {row['comparison']}: "
        f"ticks={row['tick_gain_pct']:.6f}% "
        f"instructions={row['instruction_delta_pct']:.6f}% "
        f"CPI={row['cpi_delta_pct']:.6f}% "
        f"DTLB={row['dtlb_reduction_pct']:.6f}% "
        f"iTLB={row['itlb_reduction_pct']:.6f}%"
    )
