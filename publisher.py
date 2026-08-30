from pathlib import Path
import subprocess, time, datetime, traceback

HERE = Path(__file__).resolve().parent
LOG = HERE / "publisher.log"
INTERVAL_SECONDS = 300

def log(msg):
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} {msg}\n")

def run(args, check=True):
    p = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"{args}: {p.stderr.strip() or p.stdout.strip()}")
    return p

def publish_once():
    run(["py", "-3.12", "export_status.py"])
    run(["git", "add", "data/status.json"])
    diff = run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        return "NO_CHANGE"
    run(["git", "commit", "-m", "Update live research status"])
    run(["git", "push", "origin", "main"])
    return "PUSHED"
def main():
    log("PUBLISHER_START")
    while True:
        try:
            result = publish_once()
            log(result)
        except Exception as exc:
            log("ERROR " + repr(exc))
            log(traceback.format_exc().replace("\n", " | "))
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
