import subprocess
import sys
from pathlib import Path

BUCKET = "vibe-dating-code-dev-8e64f92e-580e-11f0-80ef-00155d453b17"
LAMBDA_DIR = Path("build/lambda")
FILES = [
    "vibe_base_layer.zip",
    "telegram_auth.zip",
    "jwt_authorizer.zip"
]

def main():
    for fname in FILES:
        src = LAMBDA_DIR / fname
        dest = f"s3://{BUCKET}/lambda/{fname}"
        if not src.exists():
            print(f"ERROR: {src} does not exist. Please build it first.")
            sys.exit(1)
        print(f"Uploading {src} to {dest}")
        subprocess.run(["aws", "s3", "cp", str(src), dest], check=True)
    print("All Lambda ZIPs uploaded to S3.")

if __name__ == "__main__":
    main() 