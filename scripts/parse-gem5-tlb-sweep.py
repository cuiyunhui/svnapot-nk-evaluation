#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import csv
from pathlib import Path


WORKING_SETS = (1, 2, 4, 8, 16, 32)
CONFIGS = ("B", "D")
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
    "board.processor.switch.core.mmu.itb.walker.num_4kb_walks": "iwalk_4k",
    "board.processor.switch.core.mmu.itb.walker.num_16kb_walks": "iwalk_16k",
    "board.processor.switch.core.mmu.itb.walker.num_32kb_walks": "iwalk_32k",
    "board.processor.switch.core.mmu.itb.walker.num_64kb_walks": "iwalk_64k",
}


def parse_stats(path):
    sections = path.read_text().split(
        "---------- Begin Simulation Statistics ----------"
    )[1:]
    if len(sections) != 13:
        raise SystemExit(f"{path}: expected 13 sections, got {len(sections)}")

    rows = []
    roi_names = [
        (working_set, kind)
        for working_set in WORKING_SETS
        for kind in ("data32", "code32")
    ]
    for (working_set, kind), section in zip(roi_names, sections):
        values = {name: 0 for name in KEYS.values()}
        for line in section.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] in KEYS:
                values[KEYS[fields[0]]] = int(float(fields[1]))
        values["working_set_mib"] = working_set
        values["roi"] = kind
        rows.append(values)
    return rows


parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
parser.add_argument(
    "--entries", default="32,64,128,256,512,1024",
    help="comma-separated TLB entry counts",
)
args = parser.parse_args()
entries_values = tuple(int(value) for value in args.entries.split(","))

rows = []
for entries in entries_values:
    for config in CONFIGS:
        run_dir = args.root / f"e{entries}-{config}"
        for row in parse_stats(run_dir / "stats.txt"):
            row["entries"] = entries
            row["config"] = config
            rows.append(row)

columns = ["entries", "config", "working_set_mib", "roi", *KEYS.values()]
with (args.root / "summary.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

comparison_columns = (
    "entries",
    "working_set_mib",
    "roi",
    "tick_gain_pct",
    "miss_reduction_pct",
    "b_misses",
    "d_misses",
)
comparisons = []
for entries in entries_values:
    for working_set in WORKING_SETS:
        for roi in ("data32", "code32"):
            before = next(
                row
                for row in rows
                if row["entries"] == entries
                and row["config"] == "B"
                and row["working_set_mib"] == working_set
                and row["roi"] == roi
            )
            after = next(
                row
                for row in rows
                if row["entries"] == entries
                and row["config"] == "D"
                and row["working_set_mib"] == working_set
                and row["roi"] == roi
            )
            if roi.startswith("data"):
                b_misses = before["dtlb_read_misses"] + before["dtlb_write_misses"]
                d_misses = after["dtlb_read_misses"] + after["dtlb_write_misses"]
            else:
                b_misses = before["itlb_misses"]
                d_misses = after["itlb_misses"]
            tick_gain = 100.0 * (before["ticks"] - after["ticks"]) / before["ticks"]
            miss_gain = 0.0
            if b_misses:
                miss_gain = 100.0 * (b_misses - d_misses) / b_misses
            comparisons.append(
                {
                    "entries": entries,
                    "working_set_mib": working_set,
                    "roi": roi,
                    "tick_gain_pct": f"{tick_gain:.6f}",
                    "miss_reduction_pct": f"{miss_gain:.6f}",
                    "b_misses": b_misses,
                    "d_misses": d_misses,
                }
            )

with (args.root / "comparison.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=comparison_columns)
    writer.writeheader()
    writer.writerows(comparisons)

print(
    "entries,working_set_mib,roi,tick_gain_pct,"
    "miss_reduction_pct,b_misses,d_misses"
)
for row in comparisons:
    print(
        f"{row['entries']},{row['working_set_mib']},{row['roi']},"
        f"{row['tick_gain_pct']},{row['miss_reduction_pct']},"
        f"{row['b_misses']},{row['d_misses']}"
    )
