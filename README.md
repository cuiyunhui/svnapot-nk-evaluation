# SvnapotNk evaluation

This repository contains the public functional and performance evidence for
the proposed `Svnapot16k` and `Svnapot32k` extensions. The extensions make
the 16 KiB and 32 KiB level-0 NAPOT PTE encodings independently discoverable.
The existing `Svnapot` extension continues to define the 64 KiB encoding.

## Capability matrix

| Configuration | 16 KiB | 32 KiB | 64 KiB |
|---|---:|---:|---:|
| A | No | No | Yes |
| B | Yes | No | Yes |
| C | No | Yes | Yes |
| D | Yes | Yes | Yes |

Configuration E, used only for the synthetic 4 KiB/64 KiB sanity check,
supports none of the three NAPOT sizes.

## Results

- QEMU S-stage and G-stage encoding matrix: 24/24 passed.
- Sail first-party capability matrix: 4/4 passed.
- gem5 encoding matrix: 12/12 passed.
- Linux A-D folding and lifecycle scenarios passed, including protection
  changes, fork/COW, partial unmap/remap, `MADV_DONTNEED`, and refault.
- Linux A-D boot and folding tests passed.
- GAPBS PageRank showed no meaningful intermediate-size use or performance
  change because almost all eligible mappings folded to 64 KiB.
- Renaissance `future-genetic` showed a 1.951% modeled tick reduction and a
  10.988% DTLB-miss reduction for B versus A. D versus B showed a further
  1.297% modeled tick reduction and a 4.427% DTLB-miss reduction.
- SPEC CPU 2017 `505.mcf_r` showed a 9.743% DTLB-miss reduction for B versus
  A, while D versus B reduced DTLB misses by 1.084%.
- SPEC CPU 2017 `523.xalancbmk_r` showed a 27.972% DTLB-miss reduction for B
  versus A, while D versus B reduced DTLB misses by 22.329%.

See [the evaluation report](docs/evaluation-report.md) for methodology, full
tables, limitations, and the 32 KiB assessment.

## Implementation references

The following public branches and commits contain the review material.

| Component | Branch | Commit | Purpose |
|---|---|---|---|
| ISA manual | `fast-track-svnapot-nk` | [`a6c3408143a8`](https://github.com/cuiyunhui/riscv-isa-manual/commit/a6c3408143a8f811a7990793fac4a66c2495f89a) | Normative encodings and discovery |
| Linux | `svnapot-nk-poc` | [`8b347c52a312`](https://github.com/cuiyunhui/linux/commit/8b347c52a31220c584806d90e3b28779761a06c4) | Discovery, MM policy, KVM |
| QEMU | `svnapot-nk-poc` | [`e4e2c111c29f`](https://github.com/cuiyunhui/qemu/commit/e4e2c111c29f65648a2387c2c86c180919044b1f) | Functional S/G-stage model |
| gem5 | `svnapot-nk-poc` | [`d586f36a6fd5`](https://github.com/cuiyunhui/gem5/commit/d586f36a6fd503a884c5f88729638075ba605eb5) | Performance exploration model |
| Sail | `svnapot-nk-poc` | [`911587d3a42e`](https://github.com/cuiyunhui/sail-riscv/commit/911587d3a42ee8ac214c624d9e5e13e331a1b2f1) | Executable semantics and tests |
| riscv-arch-test | `svnapot-nk-poc` | [`c7f1a0bf994b`](https://github.com/cuiyunhui/riscv-arch-test/commit/c7f1a0bf994b8229d2260230c832f122bb497da3) | Capability-aware architectural tests |

The exact commit list and validation state are recorded in
[`docs/implementation-status.md`](docs/implementation-status.md).

## Scope and licensing

QEMU and Sail are used for architectural behavior. gem5 is used for early
performance exploration; its timing is not a prediction for a specific
processor and is not equivalent to hardware or an FPGA/emulation platform.

SPEC CPU 2017 source, binaries, inputs, reference outputs, disk images, and
raw run directories are not included. Only aggregate measurements derived
from an authorized installation are published here. They are internal
workload/model measurements, not reportable SPEC scores.

The source parsers in `scripts/` are licensed under GPL-2.0-or-later. Result
tables and documentation are provided for review of the SvnapotNk proposal.
