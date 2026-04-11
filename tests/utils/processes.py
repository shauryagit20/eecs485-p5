"""Process utilities."""
import subprocess
import time

# Time to wait for server to start
TIMEOUT = 10


def pgrep(pattern):
    """Return list of matching processes."""
    completed_process = subprocess.run(
        ["pgrep", "-f", pattern],
        check=False,  # We'll check the return code manually
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    if completed_process.returncode == 0:
        return completed_process.stdout.strip().split("\n")
    return []


def pkill(pattern):
    """Issue a "pkill -f pattern" command, ignoring the exit code."""
    subprocess.run(["pkill", "-f", pattern], check=False)


def wait_for_flask_start(nprocs):
    """Wait for nprocs Flask processes to start running."""
    # Need to check for processes twice to make sure that
    # the flask processes doesn't error out but get marked correct
    count = 0
    for _ in range(TIMEOUT):
        if len(pgrep("flask")) == nprocs:
            count += 1
        if count >= 2:
            return True
        time.sleep(1)
    return False


def wait_for_flask_stop():
    """Wait for Flask servers to stop running."""
    for _ in range(TIMEOUT):
        if not pgrep("flask"):
            return True
        time.sleep(1)
    return False
