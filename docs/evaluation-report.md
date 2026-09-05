# SvnapotNk functional and performance evaluation

## Conclusion

The functional PoC validates independent discovery and translation behavior
for the 16 KiB and 32 KiB NAPOT encodings. Unsupported encodings raise page
faults, and S-stage and G-stage behavior follows base Svnapot semantics.

The performance data supports the following position:

- retain `Svnapot16k`; its translation benefit appears across the JVM and
  both selected SPEC CPU workloads;
- retain `Svnapot32k` as an independent optional capability;
- do not require hardware or operating systems to implement or enable 32 KiB;
- describe 32 KiB benefit as workload-dependent, not universal.

## Functional validation

QEMU exercised order 2, 3, and 4 encodings under configurations A-D in both
S-stage and G-stage translation. All 24 cases matched the expected success or
page-fault result. The raw summary is in
`results/functional/qemu-encoding-matrix.txt`.

Sail modeled the two capabilities, their dependency on base Svnapot, level-0
PTE legality, and the A-D combinations. All four first-party tests passed.

Linux booted under all four QEMU configurations and advertised only the
configured ISA strings. Folding selected the largest supported suitable size.
Lifecycle testing covered protection changes, fork/COW, partial unmap/remap,
`MADV_DONTNEED`, refault, and concurrent 16 KiB/32 KiB mappings.

ACT4 tests are generated for four cases: 16 KiB supported, 16 KiB unsupported,
32 KiB supported, and 32 KiB unsupported. Required and forbidden extension
metadata selects the correct two tests for each A-D configuration.

## gem5 methodology

The measurements use a full-system RISC-V Linux model with:

- 4 KiB base pages;
- `TimingSimpleCPU` during each measured region of interest;
- separate configurable iTLB and dTLB capacities;
- 32 KiB, 8-way L1 instruction and data caches;
- 512 KiB, 4-way private L2 cache;
- separate 8 KiB instruction/data page-walk caches;
- 1 GiB or 2 GiB DDR3-1600 memory, as required by the workload;
- KASLR and userspace ASLR disabled;
- Linux mTHP policy fixed across each A-D comparison; and
- statistics reset at `WORKBEGIN` and collected at `WORKEND`.

Only the advertised NAPOT capabilities change within each comparison. QEMU
and Spike execution time is not used as performance evidence.

## Synthetic translation pressure

With 64-entry iTLB and dTLB structures:

| Comparison | Workload | Modeled ticks | Relevant TLB misses |
|---|---|---:|---:|
| A vs E | 64 KiB data | 2.872% faster | 93.744% fewer |
| A vs E | 64 KiB code | 2.744% faster | 93.749% fewer |
| B vs A | 16 KiB data | 1.762% faster | 74.995% fewer |
| B vs A | 16 KiB code | 1.600% faster | 74.999% fewer |
| C vs A | 32 KiB data | 1.800% faster | 87.493% fewer |
| C vs A | 32 KiB code | 1.908% faster | 87.499% fewer |
| D vs B | 32 KiB data | 0.096% faster | 49.982% fewer |
| D vs B | 32 KiB code | 0.222% faster | 49.997% fewer |

The D-versus-B comparison isolates the incremental translation reach of 32
KiB when 16 KiB and 64 KiB already exist. The TLB-capacity sweep covers 32,
64, 128, 256, 512, and 1024 entries and working sets from 1 MiB to 32 MiB.

## Workload results

### GAPBS PageRank

| Config | ROI ticks | DTLB misses | iTLB misses | 16K D-walks | 32K D-walks | 64K D-walks |
|---|---:|---:|---:|---:|---:|---:|
| A | 573507281000 | 2620 | 21 | 0 | 0 | 2562 |
| B | 573536924000 | 2620 | 21 | 2 | 0 | 2562 |
| C | 573526786500 | 2620 | 21 | 0 | 2 | 2562 |
| D | 573501164000 | 2620 | 21 | 0 | 2 | 2562 |

The largest tick difference is approximately 0.006%. This workload mostly
uses 64 KiB mappings, so it demonstrates no material regression but provides
little evidence for an intermediate page size.

### Renaissance future-genetic

| Config | ROI ticks | DTLB misses | iTLB misses |
|---|---:|---:|---:|
| A | 2523881290500 | 3689168 | 1164253 |
| B | 2474644592000 | 3283809 | 1124691 |
| C | 2556104660500 | 3617087 | 1169556 |
| D | 2442545842000 | 3138434 | 1107055 |

B versus A reduces modeled ticks by 1.951%, DTLB misses by 10.988%, and iTLB
misses by 3.398%. D versus B reduces modeled ticks by a further 1.297%, DTLB
misses by 4.427%, and iTLB misses by 1.568%.

The B/D pair was repeated three times and produced identical ROI statistics.
The D-versus-B instruction count also fell by 1.328%, while CPI increased by
0.031%. The result is therefore an end-to-end modeled workload effect, not a
pure page-walk-latency measurement.

### SPEC CPU 2017 selected workloads

An authorized SPEC CPU 2017 v1.1.0 installation was used privately. The two
selected workloads were built as static RV64GC/LP64D binaries and validated
against their expected output. Test inputs were used for the gem5 matrix.

| Workload | Comparison | Tick reduction | DTLB-miss reduction |
|---|---|---:|---:|
| 505.mcf_r | B vs A | 0.049% | 9.743% |
| 505.mcf_r | D vs B | 0.002% | 1.084% |
| 523.xalancbmk_r | B vs A | 0.123% | 27.972% |
| 523.xalancbmk_r | D vs B | 0.076% | 22.329% |

The two cases agree that 16 KiB reduces translation misses. They also show why
32 KiB should remain optional: its incremental D-versus-B value is meaningful
for Xalan but very small for mcf.

## Limitations

- gem5 is a model for early exploration, not a substitute for implementation-
  specific hardware measurements.
- The results do not establish a universal execution-time gain.
- KVM UAPI numbers remain provisional until allocated upstream.
- ACT4 does not yet include G-stage coverage for these encodings; QEMU and Sail
  provide the current G-stage functional evidence.
- Hardware validation should be added when a suitable implementation exists.
