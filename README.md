# SOURSOP

A lightweight Linux network usage monitor that runs as a background daemon and tracks per‑process and overall
incoming and outgoing traffic, stored locally and queried via a CLI.

Simple goal: know which one used your network, and when.

No cloud. No tracking. Your machine, your data.

---

## 🧩 Technical Overview

* **Daemon**: Runs in the background, samples network usage periodically
* **Collector**: Captures overall and per-process outgoing/incoming traffic
* **Storage**: SQLite database with time-bucketed records
* DB file located at `/var/lib/soursop/soursop.db`
* Log file located at `/var/log/soursop/soursop.log`
* **CLI**: Query, summarize, and inspect usage
* Provide **time-based aggregation** (hour/day/week/month)
* **Packaging**: Debian package installs daemon + CLI, distribute as a **.deb** package

---

## 📦 Installation

Download `soursop_0.1.deb` file, then run the following command in the downloaded location.

`sudo dpkg -i soursop_0.1.deb`

---

## 🧪 CLI Usage

### Total network usage

Trace total incoming and outgoing network usage through the Wi-Fi adapter.
Support for other network adapters is planned in future improvements.

`soursop network [options]`

#### Options

```commandline
-l, --level LEVEL           Aggregation level: hour|day|week|month (short forms: h|d|w|m supported)

# Date range selection (provide both start and end dates)
-f, --from DATE             Start date (YYYY-MM-DD)
-t, --to DATE               End date (YYYY-MM-DD)

# Relative time window (provide only one time window)
-d, --day N                 Look back N days
-w, --week N                Look back N weeks
-m, --month N               Look back N months
```

You must choose either a date range or a relative time window.

When using a date range, both `--from` and `--to` must be provided together.

When using a relative time window, only one of --day, --week, or --month may be specified at a time.

#### Examples

```commandline
# Usage for today, aggregated by hour
soursop network

# Usage for today, aggregated by day
soursop network --level day

# Last 7 days, aggregated by hour
soursop network --day 7

# Last 4 weeks, aggregated by week
soursop network --week 4 -l w

# Specific date range, aggregated by hour
soursop network --from 2025-01-01 --to 2025-01-07

# Specific date range, aggregated by month
soursop network --from 2025-01-01 --to 2024-01-01 --level month
```

---

### Process network usage

Trace per-process incoming and outgoing network usage.
Individual processes are uniquely identified using process name and executable path.

`soursop process [options]`

#### Options

```commandline
-l, --level LEVEL           Aggregation level: hour|day|week|month (short forms: h|d|w|m supported)

-n, --name NAME             Substring match against process name

# Date range selection (provide both start and end dates)
-f, --from DATE             Start date (YYYY-MM-DD)
-t, --to DATE               End date (YYYY-MM-DD)

# Relative time window (provide only one time window)
-d, --day N                 Look back N days
-w, --week N                Look back N weeks
-m, --month N               Look back N months
```

Optional flags are similar to `soursop network` command. Except for the `--name` flag to filter by process name.

#### Examples

```commandline
# Usage for today, aggregated by hour, for all the processes
soursop process

# Last 7 days, aggregated by hour, processes containing name `chrome`
soursop process --day 7 --name chrome
```

All example flag combinations shown for soursop process are valid here as well;
this command additionally supports the `--name` flag.
---

## 📜 License

MIT

