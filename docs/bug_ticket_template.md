# Bug / failure ticket (qualification)

Use this template when a qualification run surfaces an issue worth tracking.

## Summary

- **Title:**
- **Severity:** Blocker / High / Medium / Low
- **Found in run ID:** `nqs_YYYYMMDD_HHMMSS`
- **Test ID(s):**
- **Environment:** (SKU, firmware/build, NIC/driver, OS)

## Observed behavior

- What failed (symptoms, error strings)?
- Reproducibility: always / intermittent / single occurrence

## Expected behavior

- What the test plan requires for PASS?

## Steps to reproduce

1. Start local targets: `python main.py serve --mode normal`
2. Run plan: `python main.py run --plan testplans/....yaml`
3. (Add lab-specific steps: cable, VLAN, power cycle, etc.)

## Logs & artifacts

- Attach: `logs/nqs_*.log`
- Attach: `reports/nqs_report_*.md` and `.json`

## Initial analysis

- Network layer hypothesis (L2/L3/firewall/port)
- Application/protocol hypothesis
- Next experiments (pcap, ping, iperf, vendor tools)

## Owner / status

- **Owner:**
- **Status:** New / Investigating / Fix in progress / Verified
