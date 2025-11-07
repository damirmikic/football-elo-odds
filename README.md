# Football Elo Odds Data Notes

## League statistics data files

The app reads league-level stats from `data/` at startup. Each file should either be a JSON document with a top-level object mapping league names to their metrics, or a CSV file with one row per league.

### JSON format

```json
{
  "Country - League Name": {
    "GP": 0,
    "HomeW%": 0.00,
    "Draw%": 0.00,
    "AwayW%": 0.00,
    "AvgGoals": 0.00,
    "AvgHG": 0.00,
    "AvgAG": 0.00
  }
}
```

- League names are normalized automatically (trimmed and collapsed whitespace) when loaded.
- Additional metrics can be added alongside the existing keys; they will be available in the UI helpers.

### CSV format

If you prefer CSV, provide a header row and ensure there is a `League` column containing the display name used in the selectors. All other columns are treated as metrics.

```
League,GP,HomeW%,Draw%,AwayW%,AvgGoals,AvgHG,AvgAG
Country - League Name,0,0.00,0.00,0.00,0.00,0.00,0.00
```

Updating the statistics only requires editing the files in `data/`.
