# Implementation and validation status

## Review commits

| Component | Public fork | Branch | Head | Status |
|---|---|---|---|---|
| ISA manual | https://github.com/cuiyunhui/riscv-isa-manual/tree/fast-track-svnapot-nk | `fast-track-svnapot-nk` | [`a6c3408143a8`](https://github.com/cuiyunhui/riscv-isa-manual/commit/a6c3408143a8f811a7990793fac4a66c2495f89a) | Normative text prepared |
| Linux | https://github.com/cuiyunhui/linux/tree/svnapot-nk-poc | `svnapot-nk-poc` | [`8b347c52a312`](https://github.com/cuiyunhui/linux/commit/8b347c52a31220c584806d90e3b28779761a06c4) | Four new commits over the tested PTE-folding series |
| QEMU | https://github.com/cuiyunhui/qemu/tree/svnapot-nk-poc | `svnapot-nk-poc` | [`e4e2c111c29f`](https://github.com/cuiyunhui/qemu/commit/e4e2c111c29f65648a2387c2c86c180919044b1f) | Replayed cleanly on QEMU v9.1.0 |
| gem5 | https://github.com/cuiyunhui/gem5/tree/svnapot-nk-poc | `svnapot-nk-poc` | [`d586f36a6fd5`](https://github.com/cuiyunhui/gem5/commit/d586f36a6fd503a884c5f88729638075ba605eb5) | Rebased onto the current stable branch |
| Sail | https://github.com/cuiyunhui/sail-riscv/tree/svnapot-nk-poc | `svnapot-nk-poc` | [`911587d3a42e`](https://github.com/cuiyunhui/sail-riscv/commit/911587d3a42ee8ac214c624d9e5e13e331a1b2f1) | Adapted to the current master branch |
| Architecture tests | https://github.com/cuiyunhui/riscv-arch-test/tree/svnapot-nk-poc | `svnapot-nk-poc` | [`c7f1a0bf994b`](https://github.com/cuiyunhui/riscv-arch-test/commit/c7f1a0bf994b8229d2260230c832f122bb497da3) | ACT4 generator, coverage, and four generated tests |

All six branches above have been published to the listed forks.

## Validation status

| Component | Validation | Result |
|---|---|---|
| QEMU review source | Native RISC-V build and S-stage/G-stage A-D encoding matrix | Build pass; 24/24 pass |
| Linux review source | Native RISC-V `vmlinux` and KVM `get-reg-list.o` builds | Pass |
| Linux PoC runtime | A-D boot/folding and lifecycle tests | Pass |
| Sail PoC source | Type check, build, A-D first-party tests | 4/4 pass |
| gem5 PoC source | Encoding matrix and full-system workloads | Pass |
| gem5 review source | Native RISC-V build | Not rerun: validation host lacks `Python.h`; stable patch ID matches the tested PoC |
| Architecture tests | ruff, pyright, deterministic generation, A-D selection | Pass |
| Architecture-test assembly/runtime | ACT4/UDB environment | Pending; generated configuration header is unavailable on the validation host |
| Linux review commits | `diff --check`, `checkpatch.pl --strict` | Pass |
| ISA manual review commit | `diff --check` | Pass |
| ISA manual HTML | Local build | Not run: `asciidoctor` unavailable |

The QEMU review source was exported from commit `e4e2c111c29f`, built on a
native RISC-V host, and used to rerun the 24-case matrix. The new result file
and the original archived result are byte-identical:

```text
qemu-encoding-matrix.txt
SHA256 2463f686814f1c4fb0c9d5acd65822eb05106afbb70e12e3aaa8c857f7bf41f1
```

The Linux review source was reconstructed from `9aa5b2886bb6` plus the exact
public branch diff. Native RISC-V builds produced:

```text
vmlinux SHA256
72e928d57abb66470c0a22a5035a23b4b7374526a4a75ea28ed945fc2c6c013f

KVM get-reg-list.o SHA256
2a1d90313c99c7915a4b0451bb8853666c5e8703654833f4ebf33d82c384f188
```

Stable patch IDs were compared between each original validated PoC patch and
its review branch. Linux and QEMU matched exactly. The gem5 implementation
diff also remained identical after rebasing to the current stable branch. Sail
required a three-file context adaptation to preserve newer master-branch
features while adding the same model behavior and tests.

The QEMU and Linux public review source was rebuilt directly. The QEMU 24-case
matrix was also rerun and produced a byte-identical result file. Sail and gem5
runtime results were produced from the original validated PoC source trees.

## Linux dependency chain

The Linux branch includes the existing Svnapot PTE-folding series. The
public base is linux-next tag `next-20260715` (`b8809969e1d7`). The
SvnapotNk-specific portion starts with:

1. `5bf90c77e3b5` — Device Tree bindings.
2. `e6248d34ea34` — ISA discovery.
3. `a75d8782eb38` — MM capability policy.
4. `8b347c52a312` — KVM capability exposure.

The immediately preceding commit is `9aa5b2886bb6`, which generalizes the
PTE-folding lifecycle from fixed order 4 to multiple NAPOT orders.

## Publication checklist

- Rebuild the public QEMU, Linux, Sail, and gem5 branches.
- Re-run the functional matrices against those public commit IDs.
- Push all six implementation/specification branches.
- Push this evidence repository.
- Replace abbreviated commit IDs with permanent GitHub links.
- Add the links to RVS-5078 and the Ratification Plan.
- Notify the Privileged ISA Committee and request the next Fast-Track review
  checkpoint.
