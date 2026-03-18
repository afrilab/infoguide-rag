import os
import time
import json
import socket

print("Job başladı")

hostname = socket.gethostname()
job_id = os.environ.get("SLURM_JOB_ID", "N/A")

numbers = list(range(1, 10001))
total = sum(numbers)

result = {
    "hostname": hostname,
    "job_id": job_id,
    "sum": total
}

os.makedirs("outputs", exist_ok=True)

with open("outputs/result.json", "w") as f:
    json.dump(result, f, indent=2)

print("Job bitti")
print(result)
