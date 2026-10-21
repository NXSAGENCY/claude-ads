# day-trader-skill

A Claude Code plugin for intraday traders: pre-market plans, setup checklists,
deterministic position sizing, and trade-journal reviews.

> Analysis and education only. This plugin never places, modifies, or cancels
> orders, and nothing it produces is financial advice.

## Install

```
/plugin marketplace add Jakeschincariol/day-trader-skill
/plugin install day-trader-skill@day-trader-skill
```

## What you get

| Piece | Use |
| --- | --- |
| `day-trader` skill | Loads automatically for trade planning, sizing, setup checks, and journal reviews |
| `/day-trader-skill:premarket NVDA AMD` | Pre-market game plan for your tickers |
| `/day-trader-skill:size 30000 1 52.40 51.85 54` | Position size from account, risk %, entry, stop, target |
| `/day-trader-skill:journal trades.csv` | Expectancy, win rate, R-multiples, per-setup results |

Journal CSV columns: `symbol,side,entry,exit,shares` required;
`stop,setup,fees,date,notes` optional. Include `stop` to get R-multiples.

## Layout

```
.claude-plugin/
  marketplace.json   # makes this repo installable as a marketplace
  plugin.json        # plugin manifest
skills/day-trader/
  SKILL.md           # skill entrypoint
  references/        # setup checklist, risk rules
  scripts/           # position_size.py, journal_stats.py (stdlib only)
commands/            # premarket, size, journal slash commands
tests/               # pytest for the scripts
```

## Develop

```
python3 -m pytest tests
claude plugin validate .
claude --plugin-dir .    # try it locally without installing
```

## License

MIT
