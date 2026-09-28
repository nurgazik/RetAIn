"""Speed watch (2026-09-28, founder: speed first; the model market moves weekly). Reads the
`calls` table: per purpose and per host, how many calls, median / p90 seconds, output speed,
and how often the Flash-Lite fallback answered instead of Gemma.

  python -m service.speed [days=7]"""
import sys

from . import db


def pct(xs: list, q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def report(days: int = 7) -> None:
    con = db.connect()
    rows = [dict(r) for r in con.execute(
        "SELECT purpose, model, host, ms, tokens_out FROM calls WHERE ms IS NOT NULL AND at >= datetime('now', ?)",
        (f"-{days} days",))]
    print(f"last {days} days: {len(rows)} calls")
    if not rows:
        return
    print(f"\n{'purpose':<10}{'calls':>6}{'p50 s':>8}{'p90 s':>8}{'fallback':>10}")
    for purpose in sorted({r["purpose"] for r in rows}):
        rs = [r for r in rows if r["purpose"] == purpose]
        ms = [r["ms"] for r in rs]
        fb = sum(1 for r in rs if "gemini" in r["model"])
        print(f"{purpose:<10}{len(rs):>6}{pct(ms, .5) / 1000:>8.1f}{pct(ms, .9) / 1000:>8.1f}{fb / len(rs):>10.0%}")
    print(f"\n{'host':<14}{'calls':>6}{'p50 s':>8}{'p90 s':>8}{'tok/s p50':>11}")
    for host in sorted({r["host"] or "unknown" for r in rows}):
        rs = [r for r in rows if (r["host"] or "unknown") == host]
        ms = [r["ms"] for r in rs]
        tps = [r["tokens_out"] / (r["ms"] / 1000) for r in rs if r["ms"] and r["tokens_out"]]
        print(f"{host:<14}{len(rs):>6}{pct(ms, .5) / 1000:>8.1f}{pct(ms, .9) / 1000:>8.1f}{pct(tps, .5):>11.0f}")
    con.close()


if __name__ == "__main__":
    report(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
