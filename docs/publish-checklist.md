# Publication record

The specification, implementation, model, and architecture-test branches have
been published. This evaluation repository is published after this record is
updated.

## Branches

| Repository | Local path | Branch | Head |
|---|---|---|---|
| ISA manual | `/Users/bytedance/Downloads/riscv-isa-manual` | `fast-track-svnapot-nk` | `a6c3408143a8f811a7990793fac4a66c2495f89a` |
| Linux | `/Users/bytedance/Downloads/svnapot-public/linux-poc` | `svnapot-nk-poc` | `8b347c52a31220c584806d90e3b28779761a06c4` |
| QEMU | `/Users/bytedance/Downloads/svnapot-public/qemu` | `svnapot-nk-poc` | `e4e2c111c29f65648a2387c2c86c180919044b1f` |
| gem5 | `/Users/bytedance/Downloads/svnapot-public/gem5` | `svnapot-nk-poc` | `d586f36a6fd503a884c5f88729638075ba605eb5` |
| Sail | `/Users/bytedance/Downloads/svnapot-public/sail-riscv` | `svnapot-nk-poc` | `911587d3a42ee8ac214c624d9e5e13e331a1b2f1` |
| Architecture tests | `/Users/bytedance/Downloads/svnapot-public/riscv-arch-test` | `svnapot-nk-poc` | `c7f1a0bf994b8229d2260230c832f122bb497da3` |
| Evaluation | `/Users/bytedance/Downloads/svnapot-public/svnapot-nk-evaluation` | `main` | Published after final verification |

## Published branches

- https://github.com/cuiyunhui/riscv-isa-manual/tree/fast-track-svnapot-nk
- https://github.com/cuiyunhui/linux/tree/svnapot-nk-poc
- https://github.com/cuiyunhui/qemu/tree/svnapot-nk-poc
- https://github.com/cuiyunhui/gem5/tree/svnapot-nk-poc
- https://github.com/cuiyunhui/sail-riscv/tree/svnapot-nk-poc
- https://github.com/cuiyunhui/riscv-arch-test/tree/svnapot-nk-poc

## RISC-V process update

Add the final specification, implementation, test, and evidence links to:

- Jira RVS-5078; and
- the NAPOT Page Sizes (SvnapotNk) Ratification Plan.

The update should state that 16 KiB has consistent workload evidence, while
32 KiB has real but workload-dependent incremental value and remains an
independent optional capability. It should also distinguish completed PoC work
from remaining hardware validation and formal Architecture Review milestones.
