import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "day-trader" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from journal_stats import analyse  # noqa: E402
from position_size import size_position  # noqa: E402


def test_long_size_from_pct():
    r = size_position(30000, 52.40, 51.85, risk_pct=1, target=54.00)
    assert r["side"] == "long"
    assert r["shares"] == 545  # 300 / 0.55
    assert r["dollar_risk"] <= 300
    assert r["target_r"] == 2.91


def test_short_and_dollar_risk():
    r = size_position(10000, 20.0, 20.5, risk_dollars=100, target=19.0)
    assert r["side"] == "short"
    assert r["shares"] == 200
    assert r["target_r"] == 2.0


def test_buying_power_cap_warns():
    r = size_position(5000, 100.0, 99.9, risk_pct=1)
    assert r["shares"] == 50
    assert any("buying power" in w for w in r["warnings"])


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(account=1000, entry=10, stop=10, risk_pct=1),
        dict(account=1000, entry=10, stop=9, risk_pct=1, risk_dollars=5),
        dict(account=0, entry=10, stop=9, risk_pct=1),
    ],
)
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        size_position(**kwargs)


def test_journal_stats():
    rows = [
        dict(symbol="A", side="long", entry="10", exit="11", shares="100", stop="9.5", setup="orb"),
        dict(symbol="B", side="short", entry="20", exit="21", shares="50", stop="20.5", setup="fade"),
        dict(symbol="C", side="long", entry="5", exit="5.5", shares="200", stop="4.75", setup="orb"),
    ]
    r = analyse(rows)
    assert r["trades"] == 3
    assert r["net_pnl"] == 150.0
    assert r["avg_r"] == 0.67  # 2R, -2R, 2R
    assert r["by_setup"]["orb"]["trades"] == 2
    assert r["small_sample"] is True


def test_journal_missing_column():
    with pytest.raises(ValueError, match="missing columns"):
        analyse([dict(symbol="A", side="long", entry="1", exit="2")])


def test_cli_error_exit_code():
    p = subprocess.run(
        [sys.executable, str(SCRIPTS / "position_size.py"),
         "--account", "1000", "--entry", "10", "--stop", "10", "--risk-pct", "1"],
        capture_output=True, text=True,
    )
    assert p.returncode == 2
    assert "error" in json.loads(p.stderr)
