import csv
import re
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_cpu_usage_log(input_file, output_file, summary_file, global_summary_file):
    logging.info(f"Processing file: {input_file}")

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    logging.info("File read successfully.")

    parsed_data = []
    summary_data = []
    ranked_processes = defaultdict(list)  # Store processes based on rank across loops

    current_loop = None
    current_date = None
    load_1m, load_5m, load_10m = None, None, None
    process_buffer = []  # Store processes for the current loop

    for line in lines:
        line = line.strip()

        # Match Loop and Date
        loop_match = re.search(r"=== Loop:(\d+), Cmd:dumpsys cpuinfo, Date:(.*)", line)
        if loop_match:
            # Store previous loop's data before resetting
            if current_loop:
                process_buffer.sort(key=lambda x: x[7], reverse=True)  # Sort by CPU usage (highest first)
                for i, proc in enumerate(process_buffer):
                    ranked_processes[i].append(proc)  # Store in rank-based dict
                
                parsed_data.extend(process_buffer)  # Add to full data list
                summary_data.append(compute_averages(current_loop, current_date, load_1m, load_5m, load_10m, process_buffer))

            # Start new loop
            current_loop = loop_match.group(1)
            current_date = loop_match.group(2)
            load_1m, load_5m, load_10m = None, None, None
            process_buffer = []
            logging.info(f"Found Loop: {current_loop}, Date: {current_date}")
            continue

        # Match Load values
        load_match = re.search(r"Load:\s+([\d.]+)\s+/\s+([\d.]+)\s+/\s+([\d.]+)", line)
        if load_match:
            load_1m, load_5m, load_10m = map(float, load_match.groups())
            logging.info(f"Extracted Load: {load_1m}, {load_5m}, {load_10m}")
            continue

        # Match multiple processes in the same loop
        process_match = re.search(r"(?P<cpu_usage>[\d.]+)%\s+(?P<pid>\d+)/(?P<process>\S+):\s+(?P<user_cpu>[\d.]+)% user \+ (?P<kernel_cpu>[\d.]+)% kernel", line)
        if process_match:
            data = process_match.groupdict()
            logging.info(f"Extracted Process: {data['process']}, PID: {data['pid']}, CPU: {data['cpu_usage']}%, User: {data['user_cpu']}%, Kernel: {data['kernel_cpu']}%")
            process_buffer.append([
                current_loop, current_date, load_1m, load_5m, load_10m,
                int(data["pid"]), data["process"], float(data["cpu_usage"]), float(data["user_cpu"]), float(data["kernel_cpu"])
            ])

    # Ensure last loop is recorded
    if current_loop:
        process_buffer.sort(key=lambda x: x[7], reverse=True)
        for i, proc in enumerate(process_buffer):
            ranked_processes[i].append(proc)

        parsed_data.extend(process_buffer)
        summary_data.append(compute_averages(current_loop, current_date, load_1m, load_5m, load_10m, process_buffer))

    # Writing detailed process data
    logging.info(f"Writing parsed process data to {output_file}")
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Loop", "Timestamp", "Load_1m", "Load_5m", "Load_10m", "PID", "Process", "CPU_Usage", "User_CPU", "Kernel_CPU"])
        writer.writerows(parsed_data)

    logging.info("Process data written successfully.")

    # Writing per-loop summary
    logging.info(f"Writing summary data to {summary_file}")
    with open(summary_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Loop", "Timestamp", "Load_1m", "Load_5m", "Load_10m", "Avg_CPU_Usage", "Avg_User_CPU", "Avg_Kernel_CPU", "Process_Count"])
        writer.writerows(summary_data)

    logging.info("Summary data written successfully.")

    # Compute and write global rank-based averages
    global_ranking_summary = compute_rank_based_averages(ranked_processes)
    logging.info(f"Writing global rank-based averages to {global_summary_file}")
    with open(global_summary_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Avg_CPU_Usage", "Avg_User_CPU", "Avg_Kernel_CPU", "Process_Count"])
        writer.writerows(global_ranking_summary)

    logging.info("Global ranking summary written successfully.")

def compute_averages(loop, timestamp, load_1m, load_5m, load_10m, process_list):
    """Compute average CPU usage, user CPU, kernel CPU for a loop."""
    if not process_list:
        return [loop, timestamp, load_1m, load_5m, load_10m, 0, 0, 0, 0]
    
    total_cpu = sum(proc[7] for proc in process_list)
    total_user_cpu = sum(proc[8] for proc in process_list)
    total_kernel_cpu = sum(proc[9] for proc in process_list)
    count = len(process_list)

    avg_cpu = total_cpu / count
    avg_user_cpu = total_user_cpu / count
    avg_kernel_cpu = total_kernel_cpu / count

    return [loop, timestamp, load_1m, load_5m, load_10m, round(avg_cpu, 2), round(avg_user_cpu, 2), round(avg_kernel_cpu, 2), count]

def compute_rank_based_averages(ranked_processes):
    """Compute the average CPU usage per rank across all loops."""
    rank_summary = []
    
    for rank, processes in sorted(ranked_processes.items()):
        total_cpu = sum(proc[7] for proc in processes)
        total_user_cpu = sum(proc[8] for proc in processes)
        total_kernel_cpu = sum(proc[9] for proc in processes)
        count = len(processes)

        avg_cpu = total_cpu / count
        avg_user_cpu = total_user_cpu / count
        avg_kernel_cpu = total_kernel_cpu / count

        rank_summary.append([rank + 1, round(avg_cpu, 2), round(avg_user_cpu, 2), round(avg_kernel_cpu, 2), count])
    
    return rank_summary

# Run the script
parse_cpu_usage_log("data.txt", "parsed.csv", "summary.csv", "global_summary.csv")

