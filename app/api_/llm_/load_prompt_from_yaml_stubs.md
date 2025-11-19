# Function and Class stubs from '/home/kylerose1946/american_law_search/app/api_/llm_/load_prompt_from_yaml.py'

Files last updated: 1763269774.8156564

Stub file last updated: 2025-11-15 21:10:17

## Prompt

```python
class Prompt(BaseModel):
    """
    Prompt configuration loaded from a YAML file.

Attributes:
    client (Literal['openai', 'anthropic']): The LLM client to use.
    settings (Settings): Settings object for the LLM client.
    system_prompt (PromptFields): The system prompt template.
    user_prompt (PromptFields): The user prompt template.
    """
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## PromptFields

```python
class PromptFields(BaseModel):
    """
    Fields for a prompt template.

Attributes:
    role (Literal['system', 'user']): The role of the prompt.
    content (str): The content of the prompt template.
    """
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## Settings

```python
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
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## load_prompt_from_yaml

```python
def load_prompt_from_yaml(name: str, prompt_dir: Path = _PROMPT_DIR, **kwargs) -> Prompt:
    """
    Load a prompt configuration from a YAML file and format it with provided arguments.

Args:
    name: Name of the YAML file (without extension) in the prompts directory.
    prompt_dir: Directory where prompt YAML files are stored.
    **kwargs: Keyword arguments to format placeholders in the prompt content.

Returns:
    Prompt: An instance of the Prompt model with formatted content.

Raises:
    TypeError: If the name argument is not a string, or if prompts_dir is not a string or Path if provided
    ValueError: If the name argument is an empty string, or if prompt validation fails.
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
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## safe_format

```python
def safe_format(self, **kwargs) -> None:
    """
    Safely insert kwargs into the system and user prompts.
Only keys that exist in the respective prompt templates will be used for formatting.
    """
```
* **Async:** False
* **Method:** True
* **Class:** Prompt
