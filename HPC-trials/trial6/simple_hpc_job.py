import os
import time
import json
import socket

def main():
    start_time = time.time()

    hostname = socket.gethostname()
    job_id = os.environ.get("SLURM_JOB_ID", "N/A")

    numbers = list(range(1, 100001))
    total = sum(numbers)

    result = {
        "hostname": hostname,
        "job_id": job_id,
        "sum": total,
        "runtime": round(time.time() - start_time, 4)
    }

    os.makedirs("outputs", exist_ok=True)

    with open("outputs/result.json", "w") as f:
        json.dump(result, f, indent=2)

    print("DONE:", result)

if __name__ == "__main__":
    main()
