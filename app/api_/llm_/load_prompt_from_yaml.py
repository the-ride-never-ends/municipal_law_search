from pathlib import Path
from typing import Literal, Any, Annotated as Ann, Iterable, Type
import re


from pydantic import (
    AfterValidator as AV,
    BaseModel, 
    Field,
    ValidationError,
    NonNegativeFloat,
    PositiveInt,
)
import yaml


from utils.common import safe_format


_THIS_DIR = Path(__file__).parent
_PROMPT_DIR = _THIS_DIR / "prompts"
assert _PROMPT_DIR.exists(), f"Prompts directory not found at {_PROMPT_DIR}"


# Check for nested structures
def _is_nested(obj: Any, containers: Iterable[Type]) -> bool:
    """Check if an object is a nested structure of specified container types"""
    for cont in containers:
        if isinstance(obj, cont):
            if isinstance(obj, dict):
                for item in obj.values():
                    if isinstance(item, containers):
                        return True
                    if _is_nested(item, containers):
                        return True
            else:
                for item in obj:
                    if isinstance(item, containers):
                        return True
                    if _is_nested(item, containers):
                        return True
    return False


def _validate_kwargs_values(kwargs: dict[str, Any]) -> None:
    """Check for unsupported values in kwargs"""
    containers = (list, dict, set, tuple,)
    unsupported_values = [
        # Empty lists, dicts, sets, tuples
        list(), dict(), set(), tuple(),
        # empty strings
        "",
        # None
        None,
    ]
    should_raise = False
    for v in kwargs.values():
        match v:
            case bool():
                should_raise = True
            # If it's a super large or small number, raise
            case int() | float() | complex() if abs(v) > 1e10 or (0 < abs(v) < 1e-10):
                should_raise = True
            case str():
                v = v.strip()
                if len(v) >= 100000:
                    should_raise = True
            case _: # if it's an iterable, check if it's nested.
                for cont in containers:
                    if isinstance(v, cont):
                        if _is_nested(v, containers):
                            should_raise = True
        if v in unsupported_values:
            should_raise = True
        if should_raise:
            raise ValueError(f"invalid kwarg value for formatting: {v}")

def _has_name_and_file(obj: Any) -> bool:
    return hasattr(obj, '__name__') and hasattr(obj, '__file__')

def _validate_kwargs_types(kwargs: dict[str, Any]) -> None:
    for key, v in kwargs.items():
        msg = f"Unsupported type for formatting: {type(v).__name__}"
        # Check for unsupported types
        if isinstance(v, (bytes, bytearray, type)):
            raise ValueError(msg)
        if callable(v) and not isinstance(v, type):
            raise ValueError(msg)
        # Check if it's a module
        if _has_name_and_file(v) and not isinstance(v, (str, int, float, bool, list, dict, tuple, set, type(None))):
            raise ValueError(msg)
        _validate_kwargs_values({key: v})


# Check for malformed placeholders
def _check_malformed_placeholders(content: str) -> str:
    # Count braces
    open_count = content.count('{')
    close_count = content.count('}')
    print(f"Checking content: {content}, open_count: {open_count}, close_count: {close_count}")
    if open_count != close_count:
        raise ValueError(f"Malformed placeholder found in content")
    return content



class Settings(BaseModel):
    """
    Settings for the LLM client.

    Attributes:
        temperature (NonNegativeFloat): Sampling temperature for the LLM.
        max_tokens (PositiveInt): Maximum number of tokens to generate.
        top_p (NonNegativeFloat): Nucleus sampling parameter.
        frequency_penalty (NonNegativeFloat): Frequency penalty for the LLM.
        presence_penalty (NonNegativeFloat): Presence penalty for the LLM.
    """
    temperature: NonNegativeFloat = 0.0
    max_tokens: PositiveInt = 4096
    top_p: NonNegativeFloat = 1.0
    frequency_penalty: NonNegativeFloat = 0.0
    presence_penalty: NonNegativeFloat = 0.0


class PromptFields(BaseModel):
    """
    Fields for a prompt template.

    Attributes:
        role (Literal['system', 'user']): The role of the prompt.
        content (str): The content of the prompt template.
    """
    role: Literal['system', 'user']
    content: Ann[str, AV(_check_malformed_placeholders)] = Field(..., min_length=1, max_length=50000)


def _format_content(prompt: PromptFields, **kwargs) -> str:
    # Extract all placeholders from both prompts
    content, role = prompt.content, prompt.role
    placeholders = set(re.findall(r'\{([^}]+)\}', content))

    # Format the prompts
    kwargs = {k: v for k, v in kwargs.items() if k in placeholders}
    formatted_content = safe_format(content, **kwargs)

    try:
        return PromptFields(role=role, content=formatted_content)
    except ValidationError as e:
        raise ValueError(f"Prompt validation error after formatting: {e.errors()}") from e



class Prompt(BaseModel):
    """
    Prompt configuration loaded from a YAML file.

    Attributes:
        client (Literal['openai', 'anthropic']): The LLM client to use.
        settings (Settings): Settings object for the LLM client.
        system_prompt (PromptFields): The system prompt template.
        user_prompt (PromptFields): The user prompt template.
    """
    model_config = {"extra": "forbid"}
    
    client: Literal['openai', 'anthropic']
    settings: Settings = Field(default_factory=Settings)
    system_prompt: PromptFields
    user_prompt: PromptFields

    def safe_format(self, **kwargs) -> 'Prompt':
        """
        Safely insert kwargs into the system and user prompts.
        Only keys that exist in the respective prompt templates will be used for formatting.
        Returns a new Prompt object with formatted content.
        """
        if not kwargs:
            return self

        _validate_kwargs_types(kwargs)

        new_sys_prompt = _format_content(self.system_prompt, **kwargs)
        new_user_prompt = _format_content(self.user_prompt, **kwargs)

        try:
            new_prompt = Prompt(
                client=self.client,
                settings=self.settings,
                system_prompt=new_sys_prompt,
                user_prompt=new_user_prompt
            )
        except ValidationError as e:
            raise ValueError(f"Prompt validation error after formatting: {e.errors()}") from e

        return new_prompt



def load_prompt_from_yaml(name: str, prompt_dir: Path = _PROMPT_DIR, **kwargs) -> Prompt:
    """Load a prompt configuration from a YAML file and format it with provided arguments.

    Args:
        name: Name of the YAML file (without extension) in the prompts directory.
        prompt_dir: Directory where prompt YAML files are stored.
        **kwargs: Keyword arguments to format placeholders in the prompt content.

    Returns:
        Prompt: An instance of the Prompt model with formatted content.

    Raises:
        TypeError: If the name argument is not a string, or if prompts_dir is not a string or Path if provided
        ValueError: If the name argument is an empty string, or if prompt or kwargs validation fails.
        IOError: If there is an error loading the YAML file.
        ValidationError: If the loaded prompt data fails validation.
        RuntimeError: For an unexpected errors during validation or formatting.
    
    Examples:
        >>> name = "legal_summary_prompt"
        >>> prompt_dir = Path("/path/to/prompts")
        >>> prompt = load_prompt_from_yaml(name, prompt_dir, case_name="Roe v. Wade", summary_length=150)
        >>> print(prompt.system_prompt.content)
        'You are a legal expert tasked with summarizing the case Roe v. Wade.'
        >>> print(prompt.user_prompt.content)
        'Please provide a summary of the case in approximately 150 words.'
        >>> print(prompt.settings.model_dump())
        {"temperature": 0.7, "max_tokens": 500, "top_p": 0.9, "frequency_penalty": 0, "presence_penalty": 0}
    """
    if not isinstance(name, str):
        raise TypeError("prompt_name must be a string")
    if not isinstance(prompt_dir, Path):
        raise TypeError("prompt_dir must be a Path object")
    name = name.strip()
    if not name:
        raise ValueError("prompt_name cannot be empty")

    if not prompt_dir.exists():
        raise IOError(f"Prompt directory not found: {prompt_dir}")

    prompt_path = prompt_dir / f"{name}.yaml"

    if not prompt_path.exists():
        raise IOError(f"Prompt yaml file not found: {prompt_path}")

    try:
        with open(prompt_path, 'r') as file:
            prompt_dict = yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise IOError(f"Error parsing YAML file: {e}") from e
    except Exception as e:
        raise IOError(f"Error loading prompt YAML file at {prompt_path}: {e}") from e
    
    if not isinstance(prompt_dict, dict):
        raise ValueError("YAML file must contain a dictionary")

    # Check for missing required fields
    required_fields = {'client', 'system_prompt', 'user_prompt'}
    missing_fields = required_fields - set(prompt_dict.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    if "settings" in prompt_dict:
        settings = prompt_dict["settings"]
        if not isinstance(settings, dict):
            raise ValueError(f"settings must be a dictionary if provided, got {type(settings).__name__}")
        else:
            try:
                _ = Settings(**settings)  # Validate settings
            except ValidationError as e:
                raise ValueError(f"Pydantic validation error for Settings: {e.errors()}") from e
            except Exception as e:
                raise ValueError(f"Pydantic validation error for Settings: {e}") from e

    try:
        prompt = Prompt(**prompt_dict)
    except ValidationError as e:
        raise ValueError(f"Pydantic validation error for Prompt: {e.errors()}") from e
    except Exception as e:
        raise ValueError(f"Pydantic validation error for Prompt: {e}") from e
    
    # Check for overlap between settings and prompt placeholders and unused kwargs
    if kwargs:
        sys_placeholders = set(re.findall(r'\{([^}]+)\}', prompt.system_prompt.content))
        user_placeholders = set(re.findall(r'\{([^}]+)\}', prompt.user_prompt.content))
        all_placeholders = sys_placeholders | user_placeholders

        settings_fields = {'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty'}
        overlap = all_placeholders & settings_fields & set(kwargs.keys())
        if overlap:
            raise ValueError(f"Detected overlap between settings and prompt placeholders: {overlap}")

        # Check for unused kwargs - only error if kwarg doesn't match ANY placeholder
        unused_keys = set(kwargs.keys()) - all_placeholders
        if unused_keys:
            raise ValueError(f"Unused formatting arguments: {unused_keys}")

        # Check for unsupported values in kwargs
        _validate_kwargs_values(kwargs)

    try:
        prompt = prompt.safe_format(**kwargs)
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Error formatting prompt: {e}") from e
    
    return prompt
