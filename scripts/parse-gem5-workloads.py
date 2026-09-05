#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import csv
import re
from pathlib import Path


CONFIGS = ("A", "B", "C", "D")
WORKLOADS = (
    "gapbs-pr",
    "renaissance-page-rank",
    "renaissance-future-genetic",
)
KEYS = {
    "simTicks": "ticks",
    "simInsts": "instructions",
    "board.processor.switch.core.numCycles": "cycles",
    "board.processor.switch.core.mmu.dtb.readMisses": "dtlb_read_misses",
    "board.processor.switch.core.mmu.dtb.writeMisses": "dtlb_write_misses",
    "board.processor.switch.core.mmu.itb.readMisses": "itlb_misses",
    "board.processor.switch.core.mmu.dtb.walker.num_4kb_walks": "dwalk_4k",
    "board.processor.switch.core.mmu.dtb.walker.num_16kb_walks": "dwalk_16k",
    "board.processor.switch.core.mmu.dtb.walker.num_32kb_walks": "dwalk_32k",
    "board.processor.switch.core.mmu.dtb.walker.num_64kb_walks": "dwalk_64k",
    "board.processor.switch.core.mmu.dtb.walker.num_2mb_walks": "dwalk_2m",
    "board.processor.switch.core.mmu.itb.walker.num_4kb_walks": "iwalk_4k",
    "board.processor.switch.core.mmu.itb.walker.num_16kb_walks": "iwalk_16k",
    "board.processor.switch.core.mmu.itb.walker.num_32kb_walks": "iwalk_32k",
    "board.processor.switch.core.mmu.itb.walker.num_64kb_walks": "iwalk_64k",
    "board.processor.switch.core.mmu.itb.walker.num_2mb_walks": "iwalk_2m",
}


def parse_stats(path, roi_ticks):
    sections = path.read_text(errors="replace").split(
        "---------- Begin Simulation Statistics ----------"
    )[1:]
    if not sections:
        raise ValueError("no statistics sections")

    candidates = []
    for section in sections:
        values = {name: 0 for name in KEYS.values()}
        found = set()
        for line in section.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] in KEYS:
                name = KEYS[fields[0]]
                values[name] = int(float(fields[1]))
                found.add(name)
        if "ticks" in found:
            candidates.append(values)
    if not candidates:
        raise ValueError("no complete ROI statistics section")
    matches = [row for row in candidates if row["ticks"] == roi_ticks]
    if len(matches) != 1:
        raise ValueError(
            f"expected one stats section with simTicks={roi_ticks}, "
            f"found {len(matches)}"
        )
    return matches[0]


def parse_run_log(path):
    text = path.read_text(errors="replace")
    roi = re.findall(r"Workload ROI ticks: \[([0-9]+)\]", text)
    exit_match = re.findall(r"Exiting .* code=([0-9]+)", text)
    if not roi or not exit_match or exit_match[-1] != "0":
        raise ValueError("run did not finish successfully")
    return int(roi[-1])


parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
args = parser.parse_args()

rows = []
for workload in WORKLOADS:
    for config in CONFIGS:
        run_dir = args.root / f"{workload}-{config}"
        try:
            roi_ticks = parse_run_log(run_dir / "run.log")
            row = parse_stats(run_dir / "stats.txt", roi_ticks)
            row["roi_ticks"] = roi_ticks
            row["status"] = "pass"
        except (FileNotFoundError, ValueError) as error:
            row = {name: 0 for name in KEYS.values()}
            row["roi_ticks"] = 0
            row["status"] = f"incomplete: {error}"
        row["workload"] = workload
        row["config"] = config
        row["dtlb_misses"] = (
            row["dtlb_read_misses"] + row["dtlb_write_misses"]
        )
        rows.append(row)

columns = [
    "workload", "config", "status", "roi_ticks",
    *KEYS.values(), "dtlb_misses",
]
with (args.root / "summary.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

comparisons = []
for workload in WORKLOADS:
    selected = {
        row["config"]: row
        for row in rows
        if row["workload"] == workload and row["status"] == "pass"
    }
    for before_name, after_name, purpose in (
        ("A", "B", "add_16k"),
        ("A", "C", "add_32k"),
        ("B", "D", "add_32k_with_16k"),
        ("A", "D", "add_16k_and_32k"),
    ):
        if before_name not in selected or after_name not in selected:
            continue
        before = selected[before_name]
        after = selected[after_name]
        comparisons.append({
            "workload": workload,
            "comparison": f"{after_name}_vs_{before_name}",
            "purpose": purpose,
            "tick_gain_pct": 100.0 * (
                before["roi_ticks"] - after["roi_ticks"]
            ) / before["roi_ticks"],
            "dtlb_miss_reduction_pct": 100.0 * (
                before["dtlb_misses"] - after["dtlb_misses"]
            ) / before["dtlb_misses"] if before["dtlb_misses"] else 0.0,
            "itlb_miss_reduction_pct": 100.0 * (
                before["itlb_misses"] - after["itlb_misses"]
            ) / before["itlb_misses"] if before["itlb_misses"] else 0.0,
        })

comparison_columns = [
    "workload", "comparison", "purpose", "tick_gain_pct",
    "dtlb_miss_reduction_pct", "itlb_miss_reduction_pct",
]
with (args.root / "comparison.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=comparison_columns)
    writer.writeheader()
    writer.writerows(comparisons)

for row in rows:
    print(
        f"{row['workload']} {row['config']}: {row['status']} "
        f"ticks={row['roi_ticks']} dtlb={row['dtlb_misses']} "
        f"itlb={row['itlb_misses']}"
    )
for row in comparisons:
    print(
        f"{row['workload']} {row['comparison']}: "
        f"ticks={row['tick_gain_pct']:.3f}% "
        f"dtlb={row['dtlb_miss_reduction_pct']:.3f}% "
        f"itlb={row['itlb_miss_reduction_pct']:.3f}%"
    )
