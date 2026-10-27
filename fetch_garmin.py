import json, math, os, shutil, subprocess, sys
from pathlib import Path

RUNNERS = ("Halvor", "Tore", "Kjetil")

def fail(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)

def positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"Invalid {name}")
    return value

def normalize(item, runner):
    kind = item.get("activityType", {})
    kind = kind.get("typeKey", "") if isinstance(kind, dict) else kind
    if not isinstance(kind, str):
        raise ValueError("Invalid activity type")
    if "running" not in kind.lower():
        return None
    km = positive(item["distance"], "distance") / 1000
    minutes = positive(item["duration"], "duration") / 60
    day = str(item["startTimeLocal"])[:10]
    title = str(item.get("activityName") or "Løpeøkt")[:100]
    if km > 500 or minutes > 10080:
        raise ValueError("Activity outside dashboard range")
    hr = item.get("averageHR")
    if not isinstance(hr, (int, float)) or isinstance(hr, bool) or not 30 <= hr <= 240:
        hr = None
    elev = item.get("elevationGain")
    if not isinstance(elev, (int, float)) or isinstance(elev, bool) or not 0 <= elev <= 20000:
        elev = None
    return {"id": f"{runner}:{item['activityId']}", "person": runner, "date": day,
            "title": title, "km": km, "minutes": minutes, "hr": hr, "elevation": elev}

def fetch_runner(cli, runner):
    secret = os.getenv("GARMIN_" + runner.upper(), "").strip()
    if not secret:
        return [], {"status": "not_configured"}
    key_file = Path(f".{runner.lower()}.key")
    token_file = Path(f".{runner.lower()}-token.json")
    key_file.write_text(secret, encoding="utf-8")
    os.chmod(key_file, 0o600)
    rows = []
    try:
        for page in range(100):
            cmd = [cli, "--api-key-file", str(key_file), "--bearer-token-cache-file", str(token_file),
                   "--timeout", "30", "--quiet", "activities", "--start", str(page * 100), "--limit", "100"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if result.returncode:
                error = result.stderr.lower()
                reason = "AUTH_401" if "401" in error else "ACCESS_403" if "403" in error else "RATE_429" if "429" in error else "GARMIN_REQUEST"
                raise RuntimeError(reason)
            if len(result.stdout) > 10_000_000:
                raise ValueError("Response too large")
            data = json.loads(result.stdout)
            if not isinstance(data, list):
                raise ValueError("Unexpected response")
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("Unexpected activity")
                row = normalize(item, runner)
                if row:
                    rows.append(row)
            if len(data) < 100:
                break
        else:
            raise ValueError("Pagination limit")
        unique = list({a["id"]: a for a in rows}.values())
        return unique, {"status": "ok", "count": len(unique)}
    finally:
        key_file.unlink(missing_ok=True)
        token_file.unlink(missing_ok=True)

def main():
    cli = shutil.which("gc-personal")
    if not cli:
        fail("gc-personal was not installed")
    activities, sync = [], {}
    errors = []
    for runner in RUNNERS:
        try:
            rows, status = fetch_runner(cli, runner)
            activities.extend(rows)
            sync[runner] = status
        except Exception as exc:
            reason = str(exc) if str(exc) in {"AUTH_401", "ACCESS_403", "RATE_429", "GARMIN_REQUEST"} else type(exc).__name__
            sync[runner] = {"status": "error", "reason": reason}
            errors.append(runner)
    if errors:
        fail("Garmin update failed for: " + ", ".join(errors) + ". Existing deployed data is not overwritten.")
    output = {"activities": activities, "records": [], "profiles": {}, "sync": sync}
    Path("site/data.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Prepared {len(activities)} running activities")

if __name__ == "__main__":
    main()
