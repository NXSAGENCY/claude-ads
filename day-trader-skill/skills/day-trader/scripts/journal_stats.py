#!/usr/bin/env python3
"""Summarise a trade-journal CSV. Prints JSON to stdout.

Required columns: symbol, side (long/short), entry, exit, shares.
Optional columns: stop, setup, fees, date, notes.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict

REQUIRED = {"symbol", "side", "entry", "exit", "shares"}


def trade_pnl(row: dict) -> tuple[float, float | None]:
    side = row["side"].strip().lower()
    if side not in ("long", "short"):
        raise ValueError(f"side must be long or short, got {row['side']!r}")
    entry, exit_, shares = float(row["entry"]), float(row["exit"]), float(row["shares"])
    sign = 1 if side == "long" else -1
    fees = float(row.get("fees") or 0)
    pnl = sign * (exit_ - entry) * shares - fees
    r = None
    if row.get("stop"):
        risk = abs(entry - float(row["stop"])) * shares
        if risk > 0:
            r = pnl / risk
    return pnl, r


def summarise(pnls: list[float], rs: list[float]) -> dict:
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    n = len(pnls)
    out = {
        "trades": n,
        "net_pnl": round(sum(pnls), 2),
        "win_rate": round(len(wins) / n, 3) if n else None,
        "avg_win": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else None,
        "expectancy": round(sum(pnls) / n, 2) if n else None,
        "profit_factor": (
            round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) else None
        ),
    }
    if rs:
        out["avg_r"] = round(sum(rs) / len(rs), 2)
        out["trades_with_r"] = len(rs)
    return out


def analyse(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("journal has no trades")
    missing = REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")

    pnls, rs = [], []
    by_setup: dict[str, tuple[list, list]] = defaultdict(lambda: ([], []))
    for i, row in enumerate(rows, start=2):
        try:
            pnl, r = trade_pnl(row)
        except (ValueError, TypeError) as e:
            raise ValueError(f"row {i}: {e}") from None
        pnls.append(pnl)
        setup = (row.get("setup") or "unlabelled").strip() or "unlabelled"
        by_setup[setup][0].append(pnl)
        if r is not None:
            rs.append(r)
            by_setup[setup][1].append(r)

    result = summarise(pnls, rs)
    result["by_setup"] = {k: summarise(*v) for k, v in sorted(by_setup.items())}
    result["small_sample"] = len(pnls) < 20
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_path")
    a = p.parse_args(argv)
    try:
        with open(a.csv_path, newline="", encoding="utf-8-sig") as f:
            rows = [{k.strip().lower(): v for k, v in r.items()} for r in csv.DictReader(f)]
        out = analyse(rows)
    except (OSError, ValueError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
