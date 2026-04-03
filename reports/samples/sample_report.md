# Network Qualification Suite — Run Report

**Run ID:** `sample_20260403_120000`  
**Generated:** 2026-04-03 12:00:00 UTC  
**Duration:** 0.52s

## Summary

| Metric | Value |
|--------|-------|
| Total | 3 |
| Passed | 3 |
| Failed | 0 |
| Skipped | 0 |

## Environment snapshot

```json
{
  "python_version": "3.13.x",
  "platform": "Windows-11",
  "system": "Windows",
  "machine": "AMD64",
  "processor": "x86_64",
  "hostname": "example-workstation",
  "cpu_count_logical": 16,
  "cpu_count_physical": 8,
  "ram_total_mb": 32768.0,
  "ram_available_mb": 16384.0
}
```

## Results

| Test ID | Name | Protocol | Status | ms | Retries | Notes |
|---------|------|----------|--------|-----|---------|-------|
| `TCP-BASE-001` | TCP echo connectivity | TCP | **passed** | 4.2 | 1 | TCP echo OK |
| `TCP-BASE-002` | TCP connection stability (short burst) | TCP | **passed** | 4.6 | 1 | Stability: 8/8 OK |
| `UDP-BASE-001` | UDP echo round-trip | UDP | **passed** | 4.0 | 1 | UDP echo 12/12 (est. loss 0.0%) |

## Metrics (per test)

### `TCP-BASE-001`

```json
{
  "rtt_ms": 4.1,
  "bytes_sent": 128,
  "bytes_recv": 128,
  "test_type_resolved": "connectivity"
}
```

---

*Example report for portfolio screenshots — generate your own with `python main.py run --plan testplans/basic_connectivity.yaml --simulate normal`.*
