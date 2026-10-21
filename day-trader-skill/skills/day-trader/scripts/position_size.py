#!/usr/bin/env python3
"""Deterministic position-size calculator. Prints JSON to stdout."""

from __future__ import annotations

import argparse
import json
import math
import sys


def size_position(
    account: float,
    entry: float,
    stop: float,
    risk_pct: float | None = None,
    risk_dollars: float | None = None,
    target: float | None = None,
    buying_power: float | None = None,
) -> dict:
    if account <= 0:
        raise ValueError("account must be positive")
    if entry <= 0 or stop <= 0:
        raise ValueError("entry and stop must be positive")
    if entry == stop:
        raise ValueError("entry and stop must differ")
    if (risk_pct is None) == (risk_dollars is None):
        raise ValueError("give exactly one of risk_pct or risk_dollars")

    side = "long" if stop < entry else "short"
    budget = risk_dollars if risk_dollars is not None else account * risk_pct / 100
    if budget <= 0:
        raise ValueError("risk must be positive")

    per_share = abs(entry - stop)
    shares = math.floor(budget / per_share)
    warnings = []

    cap = buying_power if buying_power is not None else account
    if shares * entry > cap:
        shares = math.floor(cap / entry)
        warnings.append("size capped by buying power; actual risk is below budget")
    if shares == 0:
        warnings.append("stop too wide for the risk budget; no position")

    dollar_risk = round(shares * per_share, 2)
    result = {
        "side": side,
        "shares": shares,
        "risk_per_share": round(per_share, 4),
        "risk_budget": round(budget, 2),
        "dollar_risk": dollar_risk,
        "risk_pct_of_account": round(dollar_risk / account * 100, 3),
        "position_value": round(shares * entry, 2),
        "warnings": warnings,
    }

    if target is not None:
        reward = (target - entry) if side == "long" else (entry - target)
        if reward <= 0:
            warnings.append("target is on the wrong side of entry")
        result["target_r"] = round(reward / per_share, 2)
        result["dollar_reward"] = round(shares * reward, 2)
        if 0 < result["target_r"] < 2:
            warnings.append("target is under 2R")

    if risk_pct is not None and risk_pct > 2:
        warnings.append("risk above 2% of account per trade")
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--account", type=float, required=True, help="account equity")
    p.add_argument("--entry", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    risk = p.add_mutually_exclusive_group(required=True)
    risk.add_argument("--risk-pct", type=float, help="risk as percent of account")
    risk.add_argument("--risk-dollars", type=float, help="risk in dollars")
    p.add_argument("--target", type=float)
    p.add_argument("--buying-power", type=float, help="defaults to account")
    a = p.parse_args(argv)
    try:
        out = size_position(
            a.account, a.entry, a.stop, a.risk_pct, a.risk_dollars,
            a.target, a.buying_power,
        )
    except ValueError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
