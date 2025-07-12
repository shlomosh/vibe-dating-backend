from pathlib import Path

class ServiceConstructor:
    def __init__(self, service: str):
        self.service = service
        self.config_dir = Path(__file__).parent.parent / "config"

    def get_lambda_code_bucket_name(self):
        import json
        """Get the Lambda code bucket name from core.json configuration"""
        config_path = self.config_dir / "core.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config["vibe-dating-core-s3-dev"]["LambdaCodeBucketName"]