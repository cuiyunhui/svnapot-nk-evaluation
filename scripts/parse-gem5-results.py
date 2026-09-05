#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import csv
import re
import sys
from pathlib import Path

ROI_NAMES = ("data16", "code16", "data32", "code32", "data64", "code64")
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
    sections = path.read_text().split("---------- Begin Simulation Statistics ----------")[1:]
    rows = []
    for roi, section in zip(ROI_NAMES, sections):
        values = {name: 0 for name in KEYS.values()}
        for line in section.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] in KEYS:
                values[KEYS[fields[0]]] = int(float(fields[1]))
        values["roi"] = roi
        rows.append(values)
    return rows

root = Path(sys.argv[1])
run_prefix = sys.argv[2] if len(sys.argv) > 2 else "final2"
rows = []
for config in "ABCD":
    run_dir = root / f"{run_prefix}-{config}"
    log = (run_dir / "run.log").read_text()
    match = re.search(r"Exiting @ tick .* code=(\d+)", log)
    if not match or match.group(1) != "0":
        raise SystemExit(f"{config}: run did not complete successfully")
    parsed = parse_stats(run_dir / "stats.txt")
    if len(parsed) != len(ROI_NAMES):
        raise SystemExit(f"{config}: expected six ROI sections, got {len(parsed)}")
    for row in parsed:
        row["config"] = config
        rows.append(row)

columns = ["config", "roi", *KEYS.values()]
with (root / "summary.csv").open("w", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("config,roi,ticks,cycles,dtlb_misses,itlb_misses,dwalk_4k,dwalk_16k,dwalk_32k,dwalk_64k,iwalk_4k,iwalk_16k,iwalk_32k,iwalk_64k")
for row in rows:
    print(
        f"{row['config']},{row['roi']},{row['ticks']},{row['cycles']},"
        f"{row['dtlb_read_misses'] + row['dtlb_write_misses']},"
        f"{row['itlb_misses']},{row['dwalk_4k']},{row['dwalk_16k']},"
        f"{row['dwalk_32k']},{row['dwalk_64k']},{row['iwalk_4k']},"
        f"{row['iwalk_16k']},{row['iwalk_32k']},{row['iwalk_64k']}"
    )

print("\nIncremental D versus B for 32 KiB workloads:")
for roi in ("data32", "code32"):
    b = next(row for row in rows if row["config"] == "B" and row["roi"] == roi)
    d = next(row for row in rows if row["config"] == "D" and row["roi"] == roi)
    tick_gain = (b["ticks"] - d["ticks"]) * 100.0 / b["ticks"]
    if roi.startswith("data"):
        b_misses = b["dtlb_read_misses"] + b["dtlb_write_misses"]
        d_misses = d["dtlb_read_misses"] + d["dtlb_write_misses"]
        miss_name = "dtlb_misses"
    else:
        b_misses = b["itlb_misses"]
        d_misses = d["itlb_misses"]
        miss_name = "itlb_misses"
    miss_gain = (b_misses - d_misses) * 100.0 / b_misses
    print(f"{roi}: ticks {tick_gain:.3f}% faster, {miss_name} {miss_gain:.3f}% fewer")
