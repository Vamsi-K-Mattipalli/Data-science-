import yaml
from typing import Dict, Any

class Config:
    """ Represents the configuration loaded from the YAML file. """
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r') as file:
            self._config = yaml.safe_load(file)

        prompt_files_config = self._config.get('prompt_files', {})
        instructions_file = prompt_files_config.get('instructions', 'instructions.yaml')
        examples_file = prompt_files_config.get('examples', 'examples.yaml')

        self._prompt_templates = self._load_and_combine_prompts(instructions_file, examples_file)

    def _load_yaml(self, filepath: str) -> Dict:
        """Loads a YAML file and returns its content as a dictionary."""
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f) or {} # Return empty dict if file is empty
        except FileNotFoundError:
            print(f"Warning: YAML file not found at path: {filepath}. Returning empty prompts.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading YAML file at {filepath}: {e}. Returning empty prompts.")
            return {}

    def _load_and_combine_prompts(self, instructions_file: str, examples_file: str) -> Dict[str, str]:
        """Loads instructions, examples, and combines them into full prompts."""
        instructions_yaml = self._load_yaml(instructions_file)
        examples_yaml = self._load_yaml(examples_file)

        combined_prompts: Dict[str, str] = {}

        instruction_prompts = instructions_yaml.get('prompts', {})
        footer_prompts = instructions_yaml.get('footer_prompts', {})
        example_prompts = examples_yaml.get('prompts', {})

        # Get all unique prompt keys from all files to ensure all are processed
        all_prompt_keys = set(instruction_prompts.keys()) | set(example_prompts.keys()) | set(footer_prompts.keys())

        for prompt_key in all_prompt_keys:
            instruction_prompt = instruction_prompts.get(prompt_key, "")
            example_prompt = example_prompts.get(prompt_key, "")
            footer_prompt = footer_prompts.get(prompt_key, "")

            combined_prompt = instruction_prompt + "\n" + example_prompt + "\n" + footer_prompt
            combined_prompts[prompt_key] = combined_prompt

        return combined_prompts

    @property
    def llm_config(self) -> Dict[str, Any]:
        """Returns the LLM configuration."""
        return self._config.get('LLM_config', {})

    @property
    def prompt_templates(self) -> Dict[str, str]:
        """Returns the combined prompt templates."""
        return self._prompt_templates