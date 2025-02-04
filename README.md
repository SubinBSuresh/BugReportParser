# Android CPU Usage Log Processor

## Overview
This project is designed to parse, process, and summarize CPU usage logs extracted from an **Android bugreport**. It processes raw log data, extracts CPU-related information for each process, and generates detailed CSV reports with averages, rankings, and summary statistics.

## Features
- **Parse CPU usage logs** from `dumpsys cpuinfo` and other system-level logs.
- **Compute averages** of CPU usage (user, kernel, and overall) for each process.
- **Generate detailed CSV outputs** for parsed CPU data, loop summaries, and global rank-based averages.
- **Rank processes** based on their CPU usage across multiple loops.

## Requirements
- **Python
- **Runs only in linux because of some file operations logic.
