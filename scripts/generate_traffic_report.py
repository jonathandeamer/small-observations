#!/usr/bin/env python3
import os
import sys
import json
import datetime
import subprocess
import gzip
import shutil

CF_LOG_FORMAT = '%d\t%t\t%^\t%b\t%h\t%m\t%^\t%U\t%s\t%R\t%u\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^\t%^'

def format_bytes(b):
    if b >= 1024**3:
        return f"{b / (1024**3):.2f} GiB"
    elif b >= 1024**2:
        return f"{b / (1024**2):.2f} MiB"
    elif b >= 1024:
        return f"{b / 1024:.2f} KiB"
    return f"{b} B"

def main():
    # 1. Check if aws-cli and goaccess are installed
    if not shutil.which("aws"):
        print("Error: 'aws' CLI is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("goaccess"):
        print("Error: 'goaccess' is not installed or not in PATH. Please install it using 'sudo apt install goaccess'.", file=sys.stderr)
        sys.exit(1)

    # 2. Ensure directories exist
    os.makedirs("tmp/goaccess/logs", exist_ok=True)
    os.makedirs("tmp/goaccess/reports", exist_ok=True)

    # 3. Sync logs from S3
    print("Syncing CloudFront access logs from S3...")
    sync_cmd = [
        "aws", "s3", "sync",
        "s3://smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/",
        "tmp/goaccess/logs/",
        "--profile", "smallobservations-analytics"
    ]
    try:
        subprocess.run(sync_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error syncing logs: {e}", file=sys.stderr)
        print("Please check your AWS credentials or profile setup.", file=sys.stderr)
        sys.exit(1)

    # 4. Determine dates for the last 8 days (including today)
    today = datetime.date.today()
    days_to_include = 8
    target_dates = [today - datetime.timedelta(days=i) for i in range(days_to_include)]
    date_strings = [d.strftime("%Y-%m-%d") for d in target_dates]
    
    start_date_str = target_dates[-1].strftime("%d/%b/%Y")
    end_date_str = target_dates[0].strftime("%d/%b/%Y")

    print(f"Filtering logs for period: {start_date_str} to {end_date_str}")

    # 5. Find matching log files
    log_dir = "tmp/goaccess/logs"
    all_files = os.listdir(log_dir)
    matching_files = []
    for f in all_files:
        if f.endswith(".gz") and any(d_str in f for d_str in date_strings):
            matching_files.append(os.path.join(log_dir, f))

    if not matching_files:
        print("No log files matched the target dates.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(matching_files)} log files to parse.")

    # 6. Run goaccess
    print("Parsing logs with GoAccess...")
    json_report_path = "tmp/goaccess/reports/this_week.json"
    goaccess_cmd = [
        "goaccess",
        "-",
        "--no-global-config",
        "--date-format=%Y-%m-%d",
        "--time-format=%H:%M:%S",
        f"--log-format={CF_LOG_FORMAT}",
        "-o", json_report_path
    ]

    try:
        proc = subprocess.Popen(goaccess_cmd, stdin=subprocess.PIPE, text=True)
        for file_path in sorted(matching_files):
            with gzip.open(file_path, "rt", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.startswith("#"):
                        proc.stdin.write(line)
        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            print(f"GoAccess failed with exit code {proc.returncode}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error running GoAccess: {e}", file=sys.stderr)
        sys.exit(1)

    # 7. Parse generated JSON
    if not os.path.exists(json_report_path):
        print(f"GoAccess report was not generated at {json_report_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_report_path) as f:
        data = json.load(f)

    # Extract general summary
    gen = data.get("general", {})
    total_hits = gen.get("total_requests", 0)
    unique_visitors = gen.get("unique_visitors", 0)
    total_bytes = gen.get("bandwidth", 0)
    gen_time = gen.get("date_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %z"))

    # Extract daily stats
    daily_rows = []
    daily_data = sorted(data.get("visitors", {}).get("data", []), key=lambda x: x["data"])
    today_str_yyyymmdd = today.strftime("%Y%m%d")

    for day in daily_data:
        dt = datetime.datetime.strptime(day["data"], "%Y%m%d")
        day_name = dt.strftime("%A, %b %d")
        hits = day["hits"]["count"]
        visitors = day["visitors"]["count"]
        bandwidth = format_bytes(day["bytes"]["count"])
        
        is_today_str = " *(partial)*" if day["data"] == today_str_yyyymmdd else ""
        daily_rows.append(f"| {day_name}{is_today_str} | {visitors:,} | {hits:,} | {bandwidth} |")

    # Extract pages and posts (split into posts/pages vs system files)
    top_posts = []
    top_system = []
    for req in data.get("requests", {}).get("data", []):
        url = req["data"]
        hits = req["hits"]["count"]
        visitors = req["visitors"]["count"]
        bandwidth = format_bytes(req["bytes"]["count"])
        
        if url in ["/", "/feed.xml", "/sitemap.xml"]:
            top_system.append((url, visitors, hits, bandwidth))
        else:
            top_posts.append((url, visitors, hits, bandwidth))

    top_posts.sort(key=lambda x: x[1], reverse=True)
    top_system.sort(key=lambda x: x[1], reverse=True)

    # Extract referring sites
    referrers = []
    for ref in data.get("referring_sites", {}).get("data", []):
        domain = ref["data"]
        hits = ref["hits"]["count"]
        visitors = ref["visitors"]["count"]
        referrers.append((domain, visitors, hits))
    referrers.sort(key=lambda x: x[1], reverse=True)

    # Extract static files (images, fonts)
    static_files = []
    for sf in data.get("static_requests", {}).get("data", []):
        file_path = sf["data"]
        hits = sf["hits"]["count"]
        visitors = sf["visitors"]["count"]
        bandwidth = format_bytes(sf["bytes"]["count"])
        static_files.append((file_path, visitors, hits, bandwidth))
    static_files.sort(key=lambda x: x[1], reverse=True)

    # Extract 404s
    not_founds = []
    for nf in data.get("not_found", {}).get("data", []):
        url = nf["data"]
        hits = nf["hits"]["count"]
        not_founds.append((url, hits))
    not_founds.sort(key=lambda x: x[1], reverse=True)

    # Extract OS and browsers
    os_list = []
    for o in data.get("os", {}).get("data", []):
        os_list.append((o["data"], o["visitors"]["count"], o["hits"]["count"]))
    os_list.sort(key=lambda x: x[1], reverse=True)

    browsers_list = []
    for b in data.get("browsers", {}).get("data", []):
        browsers_list.append((b["data"], b["visitors"]["count"], b["hits"]["count"]))
    browsers_list.sort(key=lambda x: x[1], reverse=True)

    # Generate Markdown Report
    md = []
    md.append("# Weekly Web Traffic Report")
    md.append(f"**Period:** {start_date_str} to {end_date_str} (Last 8 Days, including today)")
    md.append(f"**Report Generated at:** {gen_time}")
    md.append("")
    md.append("## Executive Summary")
    md.append("| Metric | Value |")
    md.append("| :--- | :--- |")
    md.append(f"| **Unique Visitors** | {unique_visitors:,} |")
    md.append(f"| **Total Hits (Requests)** | {total_hits:,} |")
    md.append(f"| **Total Bandwidth** | {format_bytes(total_bytes)} |")
    md.append("")
    md.append("## Daily Traffic Breakdown")
    md.append("| Date | Unique Visitors | Hits | Bandwidth |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.extend(daily_rows)
    md.append("")
    md.append("## Top Visited Pages & Posts")
    md.append("| URL | Unique Visitors | Hits | Bandwidth |")
    md.append("| :--- | :---: | :---: | :---: |")
    for url, visitors, hits, bw in top_posts[:15]:
        md.append(f"| `{url}` | {visitors:,} | {hits:,} | {bw} |")
    md.append("")
    md.append("## Top System / Feed Pages")
    md.append("| URL | Unique Visitors | Hits | Bandwidth |")
    md.append("| :--- | :---: | :---: | :---: |")
    for url, visitors, hits, bw in top_system:
        md.append(f"| `{url}` | {visitors:,} | {hits:,} | {bw} |")
    md.append("")
    md.append("## Top Traffic Referrers")
    md.append("| Referrer | Unique Visitors | Hits |")
    md.append("| :--- | :---: | :---: |")
    for domain, visitors, hits in referrers[:10]:
        md.append(f"| `{domain}` | {visitors:,} | {hits:,} |")
    md.append("")
    md.append("## Top Requested Photo Assets")
    md.append("| Photo Asset URL | Unique Visitors | Hits | Size / Bandwidth |")
    md.append("| :--- | :---: | :---: | :---: |")
    for file_path, visitors, hits, bw in static_files[:10]:
        short_name = file_path.replace('/img/', 'img/').replace('/static/', 'static/')
        md.append(f"| `{short_name}` | {visitors:,} | {hits:,} | {bw} |")
    md.append("")
    md.append("## Top 404 Not Found Requests")
    md.append("> [!NOTE]")
    md.append("> These are typically automated vulnerability scanners probing for standard paths (like WordPress or system endpoints).")
    md.append("")
    md.append("| Path | Hits |")
    md.append("| :--- | :---: |")
    for url, hits in not_founds[:10]:
        md.append(f"| `{url}` | {hits:,} |")
    md.append("")
    md.append("## Visitor Environment")
    md.append("### Operating Systems")
    md.append("| OS | Unique Visitors | Hits |")
    md.append("| :--- | :---: | :---: |")
    for name, visitors, hits in os_list[:5]:
        md.append(f"| {name} | {visitors:,} | {hits:,} |")
    md.append("")
    md.append("### Browsers")
    md.append("| Browser | Unique Visitors | Hits |")
    md.append("| :--- | :---: | :---: |")
    for name, visitors, hits in browsers_list[:5]:
        md.append(f"| {name} | {visitors:,} | {hits:,} |")

    # Save report
    report_filename = "traffic_report_this_week.md"
    with open(report_filename, 'w') as f:
        f.write('\n'.join(md))

    print(f"\nSuccess! Weekly traffic report generated at: {report_filename}")

if __name__ == "__main__":
    main()
