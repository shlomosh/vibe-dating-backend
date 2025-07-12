from pathlib import Path
from typing import Dict, Any


class ServiceConstructor:
    def __init__(self, service: str, cfg: Dict[str, Any]):
        self.service = service
        self.cfg = cfg
        self.project_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.project_dir / "src" / "config"
        self.service_dir = self.project_dir / "src" / "services" / service
        self.build_dir = self.project_dir / "build" / service

    def get_lambda_code_bucket_name(self):
        import json
        """Get the Lambda code bucket name from core.json configuration"""
        config_path = self.config_dir / "core.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config["vibe-dating-core-s3-dev"]["LambdaCodeBucketName"]