import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration profiles and workflows."""

    def __init__(self, config_path: str = "config/profiles.yaml"):
        self.config_path = Path(config_path)
        self.profiles = {}
        self.workflows = {}
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return

            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            self.profiles = config.get("profiles", {})
            self.workflows = config.get("workflows", {})

            logger.info(
                f"Loaded {len(self.profiles)} profiles and {len(self.workflows)} workflows"
            )

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def get_profile(self, profile_name: str) -> Optional[Dict]:
        """Get a processing profile by name."""
        profile = self.profiles.get(profile_name)
        if not profile:
            logger.warning(f"Profile not found: {profile_name}")
        return profile

    def get_workflow(self, workflow_name: str) -> Optional[Dict]:
        """Get a workflow by name."""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_name}")
        return workflow

    def list_profiles(self) -> List[Dict]:
        """List all available profiles."""
        return [
            {
                "name": name,
                "operation": profile.get("operation"),
                "description": profile.get("description", "")
            }
            for name, profile in self.profiles.items()
        ]

    def list_workflows(self) -> List[Dict]:
        """List all available workflows."""
        return [
            {
                "name": name,
                "description": workflow.get("description", ""),
                "jobs": len(workflow.get("jobs", []))
            }
            for name, workflow in self.workflows.items()
        ]

    def validate_profile(self, profile_name: str) -> bool:
        """Validate that a profile exists and has required fields."""
        profile = self.get_profile(profile_name)
        if not profile:
            return False

        required_fields = ["operation", "parameters"]
        return all(field in profile for field in required_fields)

    def create_custom_profile(
        self,
        name: str,
        operation: str,
        parameters: Dict,
        description: str = ""
    ) -> bool:
        """Create a custom profile."""
        try:
            self.profiles[name] = {
                "operation": operation,
                "parameters": parameters,
                "description": description
            }

            logger.info(f"Created custom profile: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create profile: {e}")
            return False

    def save_config(self):
        """Save current configuration to file."""
        try:
            config = {
                "profiles": self.profiles,
                "workflows": self.workflows
            }

            with open(self.config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
