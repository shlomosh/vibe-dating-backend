import yaml
from pathlib import Path
from typing import Any, Dict


class ServiceConstructor:
    def __init__(self, service: str, cfg: Dict[str, Any]):
        self.service = service
        self.cfg = cfg
        self.project_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.project_dir / "src" / "config"
        self.service_dir = self.project_dir / "src" / "services" / service
        self.build_dir = self.project_dir / "build" / service

        # Load parameters from parameters.yaml
        with open(self.config_dir / "parameters.yaml") as f:
            self.parameters = yaml.safe_load(f)

        # Override parameters if provided
        self.region = self.parameters["Region"]
        self.environment = self.parameters["Environment"]

    def get_lambda_code_bucket_name(self):
        from core.config_utils import ServiceConfigUtils

        # Get core-stack parameters from AWS CloudFormation outputs
        config = ServiceConfigUtils("core", region=self.region, environment=self.environment).get_stacks_outputs()

        return config[f"s3"]["LambdaCodeBucketName"]
