import os
import signal
import subprocess

import sys

from supervisor import childutils


# This script will clear out temp and encrypted IB log locations before restarting the container, when Supervisor gets a stopped state from IB

# Taken from here: https://stackoverflow.com/questions/28175011/supervisor-docker-how-to-exit-supervisor-if-a-service-doesnt-start
def main2():
    while True:
        headers, _ = childutils.listener.wait()
        childutils.listener.ok()
        if headers["eventname"] != "PROCESS_STATE_FATAL":
            # write_stdout("Not a fatal error, continuing")
            # write_stdout(headers["eventname"])
            continue
        # write_stdout("Clearing out temp space")
        subprocess.run(
            ["tmpreaper", "--all", "--showdeleted", "--force", "1h", "/tmp"],
            capture_output=True,
        )
        # write_stdout("Emptying log directories")
        subprocess.run(
            [
                "find",
                "./myfolder",
                "-mindepth",
                "1",
                "!",
                "-regex",
                "'^/root/Jts/ibgateway\(/.*\)?'",
                "-delete",
            ],
            capture_output=True,
        )
        # write_stdout("Killing supervisor")
        os.kill(os.getppid(), signal.SIGTERM)


def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def main():
    while 1:
        write_stdout("READY\n")  # transition from ACKNOWLEDGED to READY
        line = sys.stdin.readline()  # read header line from stdin
        write_stderr(line)  # print it out to stderr
        headers = dict([x.split(":") for x in line.split()])
        data = sys.stdin.read(int(headers["len"]))  # read the event payload
        write_stderr(data)  # print the event payload to stderr
        write_stdout("RESULT 2\nOK")  # transition from READY to ACKNOWLEDGED


if __name__ == "__main__":
    main()
