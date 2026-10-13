# Superseded per-run Qwen3.6 fallback (2026-10-13)

The runner sent these 4 Ornith cells to Qwen3.6 after Ornith failed twice. Owner rule: Qwen3.6 replaces the whole
Ornith column or none of it, so these records are invalid. Ornith's failures were GpuBroker HTTP 503
("cache budget too small ... free GPU memory", retry-after-ms=120000), an infrastructure denial.
The runner now backs off on 503 and has no per-run fallback; the cells were rerun on Ornith.
