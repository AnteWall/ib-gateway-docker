import select
import subprocess
import os
import json
import time
from datetime import datetime, timedelta

import psutil

# /var/log/socat.log
LOGMONITOR_LOGFILE = os.getenv("LOGMONITOR_LOGFILE", "/var/log/socat.log")

# list of keywords that will be treated as errors
LOGMONITOR_ERRORS = json.loads(os.getenv("LOGMONITOR_ERRORS", '["Connection refused"]'))

# max lookback period in seconds (anything prior is ignored)
LOGMONITOR_MAX_LOOKBACK = int(os.getenv("LOGMONITOR_MAX_LOOKBACK", "60"))

# max number of errors allowed to occur
LOGMONITOR_MAX_ERRORS = int(os.getenv("LOGMONITOR_MAX_ERRORS", "5"))

# period in seconds max error refers to
LOGMONITOR_MAX_ERRORS_LOOKBACK = int(os.getenv("LOGMONITOR_MAX_ERRORS_LOOKBACK", "60"))


def tail(file):
    f = subprocess.Popen(
        ["tail", "-F", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    p = select.poll()
    p.register(f.stdout)
    return p, f


def main():
    i = 0
    previous_timestamp = None
    print(f"[logmonitor] Monitoring logs: {LOGMONITOR_LOGFILE}")
    p, f = tail(LOGMONITOR_LOGFILE)
    while True:
        if not p.poll(1):
            time.sleep(1)
            continue

        line = f.stdout.readline().decode("utf-8")
        timestamp = datetime.strptime(line[:19], "%Y/%m/%d %H:%M:%S")
        # continue if timestamp is older than MAX_LOOKBACK
        if datetime.utcnow() - timestamp > timedelta(seconds=LOGMONITOR_MAX_LOOKBACK):
            i = 0
            continue

        # reset counter if previous timestamp is older than MAX_LOOKBACK seconds
        if previous_timestamp and timestamp - previous_timestamp > timedelta(
            seconds=LOGMONITOR_MAX_ERRORS_LOOKBACK
        ):
            i = 0
        print(f"[logmonitor] {line.strip()}")
        if any(err.lower() in line.lower() for err in LOGMONITOR_ERRORS):
            previous_timestamp = timestamp
            i += 1
            print(f"[logmonitor] Error detected ({i}/{LOGMONITOR_MAX_ERRORS})")

        if i >= LOGMONITOR_MAX_ERRORS:
            print(
                f"[logmonitor] Maximum number of errors occurred: {i}, shut down supervisord process"
            )
            found = False
            for proc in psutil.process_iter():
                if proc.name() == "supervisord":
                    found = True
                    print(f"[logmonitor] Shut down supervisord process: {proc}")
                    os.system(f"kill {proc.pid} -9")
            if not found:
                print("[logmonitor] Could not find supervisord process")


if __name__ == "__main__":
    print(
        f"[logmonitor] Start logmonitor:\n   MAX_LOOKBACK={LOGMONITOR_MAX_LOOKBACK}\n   MAX_ERRORS={LOGMONITOR_MAX_ERRORS}\n   MAX_ERRORS_LOOKBACK={LOGMONITOR_MAX_ERRORS_LOOKBACK}\n   ERRORS={LOGMONITOR_ERRORS}"
    )
    main()
