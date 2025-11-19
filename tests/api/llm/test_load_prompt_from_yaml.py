"""
Test module for load_prompt_from_yaml functionality.

This module contains test stubs based on the Gherkin feature specification
for loading and validating prompt configurations from YAML files.
"""
import pytest
import logging
import yaml
from pathlib import Path
import copy

from app.api_.llm_.load_prompt_from_yaml import load_prompt_from_yaml, Prompt, PromptFields, Settings
from tests.api.llm.conftest import FixtureError

# ============================================================================
# Base Fixtures
# ============================================================================

@pytest.fixture
def base_prompt_content():
    """Provides a base dictionary for prompt content."""
    return {
        'client': 'openai',
        'system_prompt': {'role': 'system', 'content': 'System prompt'},
        'user_prompt': {'role': 'user', 'content': 'User prompt'}
    }


# Turn off faker logs
logging.getLogger("faker").setLevel(logging.CRITICAL)

# ============================================================================
# Background Fixtures
# ============================================================================

@pytest.fixture
def prompts_dir(tmp_path):
    """Create a temporary prompts directory."""
    return tmp_path

@pytest.fixture
def create_yaml_file(prompts_dir):
    """A factory for creating YAML files for tests."""
    def _create_yaml_file(filename, content):
        try:
            file_path = prompts_dir / f"{filename}.yaml"
            with open(file_path, 'w') as f:
                if isinstance(content, str):
                    f.write(content)
                else:
                    yaml.dump(content, f)
            if not file_path.exists():
                raise FixtureError(f"YAML file '{filename}' was not created.")
            return file_path
        except Exception as e:
            raise FixtureError(f"Error creating YAML file '{filename}': {e}") from e
    return _create_yaml_file


@pytest.fixture
def basic_prompt_yaml(create_yaml_file, base_prompt_content):
    """Create a basic_prompt.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = 'You are a helpful assistant.'
    content['user_prompt']['content'] = 'Hello, world!'
    return create_yaml_file("basic_prompt", content)

@pytest.fixture
def templated_prompt_yaml(create_yaml_file, base_prompt_content):
    """Create a templated_prompt.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = 'Summary length: {summary_length}'
    content['user_prompt']['content'] = 'Summarize: {case_name}'
    return create_yaml_file("templated_prompt", content)

@pytest.fixture
def custom_settings_yaml(create_yaml_file, base_prompt_content):
    """Create a custom_settings.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['settings'] = {'temperature': 0.7, 'max_tokens': 500, 'top_p': 0.9}
    return create_yaml_file("custom_settings", content)

@pytest.fixture
def no_settings_yaml(create_yaml_file, base_prompt_content):
    """Create a no_settings.yaml file."""
    return create_yaml_file("no_settings", base_prompt_content)

@pytest.fixture
def malformed_yaml(create_yaml_file):
    """Create a malformed_yaml.yaml file."""
    content = "client: \n openai\nsystem_prompt: content: 'bad indent'"
    return create_yaml_file("malformed_yaml", content)

@pytest.fixture
def invalid_client_yaml(create_yaml_file, base_prompt_content):
    """Create an invalid_client.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['client'] = 'invalid_client'
    return create_yaml_file("invalid_client", content)

@pytest.fixture
def invalid_system_prompt_role_yaml(create_yaml_file, base_prompt_content):
    """Create an invalid_system_prompt_role.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['role'] = 'assistant'
    return create_yaml_file("invalid_system_prompt_role", content)

@pytest.fixture
def invalid_user_prompt_role_yaml(create_yaml_file, base_prompt_content):
    """Create an invalid_user_prompt_role.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['user_prompt']['role'] = 'not_a_role'
    return create_yaml_file("invalid_user_prompt_role", content)

@pytest.fixture
def empty_prompt_content_yaml(create_yaml_file, base_prompt_content):
    """Create an empty_prompt_content.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = ''
    return create_yaml_file("empty_prompt_content", content)

@pytest.fixture
def negative_temperature_yaml(create_yaml_file, base_prompt_content):
    """Create a negative_temperature.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['settings'] = {'temperature': -0.5}
    return create_yaml_file("negative_temperature", content)

@pytest.fixture
def zero_max_tokens_yaml(create_yaml_file, base_prompt_content):
    """Create a zero_max_tokens.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['settings'] = {'max_tokens': 0}
    return create_yaml_file("zero_max_tokens", content)

@pytest.fixture
def negative_top_p_yaml(create_yaml_file, base_prompt_content):
    """Create a negative_top_p.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['settings'] = {'top_p': -1.0}
    return create_yaml_file("negative_top_p", content)

@pytest.fixture
def missing_fields_yaml(create_yaml_file):
    """Create a missing_fields.yaml file."""
    content = {'client': 'openai'}
    return create_yaml_file("missing_fields", content)

@pytest.fixture
def invalid_values_yaml(create_yaml_file, base_prompt_content):
    """Create an invalid_values.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = b'\x80'
    return create_yaml_file("invalid_values", content)

@pytest.fixture
def same_placeholder_yaml(create_yaml_file, base_prompt_content):
    """Create a same_placeholder.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = 'Case: {case_name}'
    content['user_prompt']['content'] = 'Details about {case_name}'
    return create_yaml_file("same_placeholder", content)

@pytest.fixture
def non_existent_prompt_yaml():
    """Non-existent prompt name."""
    return "non_existent_prompt"

@pytest.fixture
def malformed_placeholder_yaml(create_yaml_file, base_prompt_content):
    """Create a malformed_placeholder.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = 'Case: case_name}'
    content['user_prompt']['content'] = 'Malformed: {case_name'
    return create_yaml_file("malformed_placeholder", content)

@pytest.fixture
def extra_fields_yaml(create_yaml_file, base_prompt_content):
    """Create an extra_fields.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['extra_field'] = 'some_value'
    return create_yaml_file("extra_fields", content)

@pytest.fixture
def different_order_yaml(create_yaml_file):
    """Create a different_order.yaml file."""
    content = {
        'user_prompt': {'role': 'user', 'content': 'User'},
        'client': 'openai',
        'system_prompt': {'role': 'system', 'content': 'System'},
    }
    return create_yaml_file("different_order", content)

@pytest.fixture
def large_content_yaml(create_yaml_file, base_prompt_content):
    """Create a large_content.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['system_prompt']['content'] = "a" * 10000
    return create_yaml_file("large_content", content)

@pytest.fixture
def settings_placeholder_yaml(create_yaml_file, base_prompt_content):
    """Create a settings_placeholder.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['settings'] = {'temperature': 0.5}
    content['system_prompt']['content'] = 'Temp: {temperature}'
    return create_yaml_file("settings_placeholder", content)

@pytest.fixture
def null_values_yaml(create_yaml_file, base_prompt_content):
    """Create a null_values.yaml file."""
    content = copy.deepcopy(base_prompt_content)
    content['client'] = None
    return create_yaml_file("null_values", content)

# def missing_fields_yaml(create_yaml_file, base_prompt_content):
#     """Create a missing_fields.yaml file."""
#     content = copy.deepcopy(base_prompt_content)
#     del content['system_prompt']
#     return create_yaml_file("missing_fields", content)

@pytest.fixture
def loaded_prompt_from_yaml(prompts_dir, basic_prompt_yaml) -> Prompt:
    """
    Helper function to load a prompt from YAML for testing.
    """
    try:
        prompt = load_prompt_from_yaml("basic_prompt", prompt_dir=prompts_dir)
        return prompt
    except Exception as e:
        raise FixtureError(f"Failed to make loaded_prompt_from_yaml: {e}") from e

@pytest.fixture
def loaded_template_prompt_from_yaml(prompts_dir, templated_prompt_yaml) -> Prompt:
    """
    Helper function to load a templated prompt from YAML for testing.
    """
    try:
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir)
        return prompt
    except Exception as e:
        raise FixtureError(f"Failed to make loaded_template_prompt_from_yaml: {e}") from e


# ============================================================================
# Rule: Loads Prompts from YAML Files
# ============================================================================

class TestLoadsPromptsFromYAMLFiles:
    """
    Rule: Loads Prompts from YAML Files
    """

    def test_successfully_load_a_basic_prompt(self, basic_prompt_yaml, prompts_dir):
        """
        Scenario: Successfully load a basic prompt
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then a 'Prompt' object should be returned
        """
        prompt = load_prompt_from_yaml("basic_prompt", prompt_dir=prompts_dir)
        assert isinstance(prompt, Prompt), f"Expected a Prompt object, but got {type(prompt).__name__}"

    def test_loaded_prompt_has_correct_client_type(self, basic_prompt_yaml, prompts_dir):
        """
        Scenario: Loaded prompt has correct client type
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'Prompt' should have the client type specified in the file
        """
        expected_client = 'openai'
        prompt = load_prompt_from_yaml("basic_prompt", prompt_dir=prompts_dir)
        assert prompt.client == expected_client, f"Expected client to be 'openai', but got '{prompt.client}'"

    @pytest.mark.parametrize("setting_name, expected_value", [
        ("temperature", 0.7),
        ("max_tokens", 500),
        ("top_p", 0.9)
    ])
    def test_loaded_prompt_has_configured_settings(self, custom_settings_yaml, prompts_dir, setting_name, expected_value):
        """
        Scenario: Loaded prompt has configured Settings
            Given a YAML file "custom_settings.yaml" exists
            When I load the prompt named "custom_settings"
            Then the 'Settings' should have the values specified in the file
        """
        prompt = load_prompt_from_yaml("custom_settings", prompt_dir=prompts_dir)
        actual_value = getattr(prompt.settings, setting_name)
        assert actual_value == expected_value, f"Expected {setting_name} to be {expected_value}, but got {actual_value}"

    @pytest.mark.parametrize("attr,expected_value", [
        ("role", "system"),
        ("content", "You are a helpful assistant.")
    ])
    def test_loaded_prompt_has_system_prompt_role_and_content(self, attr, expected_value, basic_prompt_yaml, prompts_dir):
        """
        Scenario: Loaded prompt has system_prompt role and content
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'system_prompt' should have 'role' and 'content'
        """
        prompt = load_prompt_from_yaml("basic_prompt", prompt_dir=prompts_dir)
        assert getattr(prompt.system_prompt, attr) == expected_value

    @pytest.mark.parametrize("attr,expected_value", [
        ("role", "user"),
        ("content", "Hello, world!")
    ])
    def test_loaded_prompt_has_user_prompt_role_and_content(self, attr, expected_value, basic_prompt_yaml, prompts_dir):
        """
        Scenario: Loaded prompt has user_prompt role and content
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'user_prompt' should have 'role' and 'content'
        """
        prompt = load_prompt_from_yaml("basic_prompt", prompt_dir=prompts_dir)
        actual_value = getattr(prompt.user_prompt, attr)
        assert actual_value == expected_value, \
            f"Expected user_prompt.{attr} to be '{expected_value}', but got '{actual_value}'"


# ============================================================================
# Rule: Prompt Formatting with Placeholders
# ============================================================================

class TestPromptFormattingWithPlaceholders:
    """
    Rule: Prompt Formatting with Placeholders
    """

    def test_load_and_format_templated_prompt(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: Load and format templated prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load "templated_prompt" with case_name="Roe v. Wade" and summary_length=150
            Then a 'Prompt' object should be returned
        """
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, case_name="Roe v. Wade", summary_length=150)
        assert isinstance(prompt, Prompt), f"Expected a Prompt object, but got {type(prompt).__name__}"

    def test_placeholder_formatting_updates_system_prompt(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: Placeholder formatting updates system_prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load "templated_prompt" with summary_length=150
            Then the 'system_prompt' should contain "150"
        """
        expected_string = "150"
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=150)
        assert expected_string in prompt.system_prompt.content, \
            f"Expected '{expected_string}' in system_prompt.content, but it was not found in '{prompt.system_prompt.content}'"

    def test_unused_formatting_arguments_raise_valueerror(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: Unused formatting arguments raise ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with extra unused keyword arguments
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'Unused formatting arguments'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, extra_arg="unused")


# ============================================================================
# Rule: Prompt contains custom settings if provided
# ============================================================================

class TestPromptContainsCustomSettingsIfProvided:
    """
    Rule: Prompt contains custom settings if provided
    """

    @pytest.mark.parametrize("setting_name, expected_value", [
        ("temperature", 0.7),
        ("max_tokens", 500),
        ("top_p", 0.9),
        ("frequency_penalty", 0.0),
        ("presence_penalty", 0.0)
    ])
    def test_custom_settings_have_correct_values(self, custom_settings_yaml, prompts_dir, setting_name, expected_value):
        """
        Scenario: Custom settings have correct values
            Given a YAML file 'custom_settings.yaml' with custom settings
            When I load the prompt
            Then the Settings should have the expected values for each setting
        """
        prompt = load_prompt_from_yaml("custom_settings", prompt_dir=prompts_dir)
        actual_value = getattr(prompt.settings, setting_name)
        assert actual_value == expected_value, \
            f"Expected {setting_name} to be {expected_value}, but got {actual_value}"


# ============================================================================
# Rule: Prompt contains default settings when none are provided
# ============================================================================

class TestPromptContainsDefaultSettingsWhenNoneAreProvided:
    """
    Rule: Prompt contains default settings when none are provided
    """

    @pytest.mark.parametrize("setting_name, expected_value", [
        ("temperature", 0.0),
        ("max_tokens", 4096),
        ("top_p", 1.0),
        ("frequency_penalty", 0.0),
        ("presence_penalty", 0.0)
    ])
    def test_default_settings_have_correct_values(self, no_settings_yaml, prompts_dir, setting_name, expected_value):
        """
        Scenario: Default settings have correct values
            Given a YAML file without settings
            When I load the prompt
            Then the Settings should have the expected default values for each setting
        """
        prompt = load_prompt_from_yaml("no_settings", prompt_dir=prompts_dir)
        actual_value = getattr(prompt.settings, setting_name)
        assert actual_value == expected_value, \
            f"Expected default {setting_name} to be {expected_value}, but got {actual_value}"


# ============================================================================
# Rule: Error Handling for Invalid Required Arguments
# ============================================================================

class TestErrorHandlingForInvalidRequiredArguments:
    """
    Rule: Error Handling for Invalid Required Arguments
    """

    @pytest.mark.parametrize("invalid_name", [
        123,           # integer
        12.5,          # float
        [],            # empty list
        {},            # empty dict
        None,          # None
        True,          # boolean
        object(),      # object instance
        lambda x: x,   # function
    ])
    def test_non_string_prompt_name_raises_typeerror(self, invalid_name, prompts_dir):
        """
        Scenario: Non-string prompt name raises TypeError
            Given a prompt name that is not a string
            When I attempt to load the prompt with that name
            Then a TypeError should be raised
        """
        with pytest.raises(TypeError, match=r'prompt_name must be a string'):
            load_prompt_from_yaml(invalid_name, prompt_dir=prompts_dir)

    def test_empty_name_raises_valueerror(self, prompts_dir):
        """
        Scenario: Empty name raises ValueError
            Given a prompt name that is empty or whitespace
            When I attempt to load the prompt with that name
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'prompt_name cannot be empty'):
            load_prompt_from_yaml(" ", prompt_dir=prompts_dir)

    @pytest.mark.parametrize("invalid_prompt_dir", [
        "/not/a/path/object",  # string
        123,                   # integer
        12.5,                  # float
        [],                    # list
        {},                    # dict
        None,                  # None
        True,                  # boolean
        object(),              # object instance
        lambda x: x,           # function
    ])
    def test_non_path_prompt_dir_raises_typeerror(self, invalid_prompt_dir):
        """
        Scenario: Non-Path prompt_dir raises TypeError
            Given a prompt_dir that is not a Path
            When I attempt to load the prompt from that directory
            Then a TypeError should be raised
        """
        with pytest.raises(TypeError, match=r'prompt_dir must be a Path object'):
            load_prompt_from_yaml("basic_prompt", prompt_dir=invalid_prompt_dir)

    def test_non_existent_prompt_dir_raises_ioerror(self):
        """
        Scenario: Non-existent prompt_dir raises IOError
            Given a prompt_dir that does not exist
            When I attempt to load a prompt from that directory
            Then an IOError should be raised
        """
        with pytest.raises(IOError, match=r'Prompt directory not found'):
            load_prompt_from_yaml("basic_prompt", prompt_dir=Path("/non/existent/dir"))


# ============================================================================
# Rule: YAML File Validation Errors
# ============================================================================

class TestYAMLFileValidationErrors:
    """
    Rule: YAML File Validation Errors
    """

    def test_non_existent_file_raises_ioerror(self, prompts_dir):
        """
        Scenario: Non-existent YAML file raises IOError
            Given a prompt name with no matching YAML file
            When I attempt to load the prompt
            Then an IOError should be raised
        """
        with pytest.raises(IOError, match=r'yaml file not found'):
            load_prompt_from_yaml("non_existent_prompt", prompt_dir=prompts_dir)

    def test_malformed_yaml_raises_ioerror(self, malformed_yaml, prompts_dir):
        """
        Scenario: Malformed YAML file raises IOError
            Given a malformed YAML file
            When I attempt to load the prompt
            Then an IOError should be raised
        """
        with pytest.raises(IOError, match=r'Error parsing YAML file'):
            load_prompt_from_yaml("malformed_yaml", prompt_dir=prompts_dir)

    @pytest.mark.parametrize("yaml_file,error_match", [
        ("missing_fields", r'Missing required fields'),
        ("invalid_client", r'validation error for Prompt'),
        ("invalid_system_prompt_role", r'validation error for Prompt'),
        ("invalid_user_prompt_role", r'validation error for Prompt'),
        ("empty_prompt_content", r'validation error for Prompt'),
        ("invalid_values", r'validation error for Prompt'),
        ("negative_temperature", r'validation error for Settings'),
        ("zero_max_tokens", r'validation error for Settings'),
        ("negative_top_p", r'validation error for Settings'),
    ])
    def test_validation_errors_raise_valueerror(self, yaml_file, error_match, prompts_dir, request):
        """
        Scenario: Various validation errors raise ValueError
            Given YAML files with invalid configurations
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        # Request the fixture to create the YAML file
        request.getfixturevalue(f"{yaml_file}_yaml")

        with pytest.raises(ValueError, match=error_match):
            load_prompt_from_yaml(yaml_file, prompt_dir=prompts_dir)


# ============================================================================
# Rule: safe_format Method Behavior
# ============================================================================



@pytest.mark.parametrize("invalid_value", [
    "",          # empty string
    " ",         # whitespace string
    [],         # empty list
    {},           # empty dict
    set(),        # empty set
    None,        # None
])
class TestRejectsInvalidKwargs:
    """
    load_prompt_from_yaml and safe_format reject invalid kwarg values
    """

    def test_safe_format_with_invalid_kwargs_raises_valueerror(
        self, invalid_value, loaded_prompt_from_yaml
    ):
        """
        Scenario: safe_format that produces invalid content raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When formatting arguments produce various invalid content
            Then a ValueError should be raised
        """
        kwargs = {"case_name": invalid_value}
        with pytest.raises(ValueError, match=r'invalid kwarg value for formatting'):
            formatted_prompt_obj = loaded_prompt_from_yaml.safe_format(**kwargs)

    def test_load_yaml_with_invalid_kwarg_values_raises_valueerror(
        self, invalid_value, templated_prompt_yaml, prompts_dir
    ):
        """
        Scenario: safe_format with invalid formatted content raises ValueError
            Given a Prompt object
            When 'safe_format' produces prompts that violate validation constraints
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'invalid kwarg value for formatting'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=invalid_value)


class TestSafeFormatMethodBehavior:
    """
    Rule: safe_format Method Behavior
    """

    def test_safe_format_with_no_arguments_returns_prompt(self, loaded_prompt_from_yaml):
        """
        Scenario: safe_format with no arguments does not error
            Given a loaded Prompt object
            When 'safe_format' is called without kwargs
            Then formatted prompt should be a Prompt object
        """
        formatted_prompt = loaded_prompt_from_yaml.safe_format()
        assert isinstance(formatted_prompt, Prompt), f"Expected a Prompt object from safe_format, but got {type(formatted_prompt).__name__}"

    @pytest.mark.parametrize("prompt_type", ["user_prompt", "system_prompt"])
    def test_safe_format_keeps_content_unchanged_with_no_kwargs(self, loaded_prompt_from_yaml, prompt_type):
        """
        Scenario: safe_format with no arguments does not error
            Given a loaded Prompt object
            When 'safe_format' is called without kwargs
            Then the prompt should remain unchanged
        """
        original_prompt = getattr(loaded_prompt_from_yaml, prompt_type).content
        formatted_prompt_obj = loaded_prompt_from_yaml.safe_format()
        formatted_prompt = getattr(formatted_prompt_obj, prompt_type).content
        assert original_prompt == formatted_prompt, \
            f"Expected '{prompt_type}' to remain unchanged, got '{formatted_prompt}' and '{original_prompt}'"



    def test_safe_format_replaces_case_name_placeholder(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format replaces case_name placeholder
            Given prompts with placeholder "{case_name}"
            When 'safe_format' is called with case_name="Brown v. Board"
            Then the case_name value should be replaced in the user_prompt content
        """
        expected_case_name = "Brown v. Board"
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, case_name="Brown v. Board", summary_length=200)
        user_prompt = prompt.user_prompt.content
        assert expected_case_name in user_prompt, \
            f"Value for 'case_name' placeholder '{expected_case_name}' not in user_prompt '{user_prompt}'"

    def test_safe_format_replaces_summary_length_placeholder(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format replaces summary_length placeholder
            Given prompts with placeholder "{summary_length}"
            When 'safe_format' is called with summary_length=200
            Then the summary_length value should be replaced in the system_prompt content
        """
        expected_summary_length = "200"
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, case_name="Brown v. Board", summary_length=200)
        system_prompt = prompt.system_prompt.content
        assert expected_summary_length in system_prompt, \
            f"Value for 'summary_length' placeholder '{expected_summary_length}' not in system_prompt '{system_prompt}'"

    def test_safe_format_with_non_existing_placeholders_raises_valueerror(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format with non-existing placeholders raises ValueError
            Given prompts with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with non_existing="value"
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'Unused formatting arguments'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, non_existing="value")

    def test_safe_format_replaces_placeholder_in_system_prompt(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format replaces placeholder in system_prompt
            Given a system_prompt with placeholder "{summary_length}" 
            When 'safe_format' is called with summary_length=100
            Then the system_prompt should contain "100"
        """
        expected_system_string = "100"
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=100, case_name="law")
        assert expected_system_string in prompt.system_prompt.content, f"system_prompt should contain '{expected_system_string}'"

    def test_safe_format_replaces_placeholder_in_user_prompt(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format replaces placeholder in user_prompt
            Given a user_prompt with placeholder "{case_name}"
            When 'safe_format' is called with case_name="law"
            Then the user_prompt should contain "law"
        """
        expected_user_string = "law"
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=100, case_name="law")
        assert expected_user_string in prompt.user_prompt.content, f"user_prompt should contain '{expected_user_string}'"

    def test_safe_format_with_the_same_placeholder_in_both_prompts(self, same_placeholder_yaml, prompts_dir):
        """
        Scenario: safe_format with the same placeholder in both prompts
            Given a system_prompt and user_prompt both with placeholder "{case_name}"
            When 'safe_format' is called with case_name="Marbury v. Madison"
            Then both prompts should contain "Marbury v. Madison"
        """
        expected_string = "Marbury v. Madison"
        prompt = load_prompt_from_yaml("same_placeholder", prompt_dir=prompts_dir, case_name=expected_string)
        assert expected_string in prompt.system_prompt.content, f"system_prompt does not contain '{expected_string}'"
        assert expected_string in prompt.user_prompt.content, f"user_prompt does not contain '{expected_string}'"

    @pytest.mark.parametrize("expected_string,prompt_type", [
        ("Miranda v. Arizona", "user_prompt"),
        ("{summary_length}", "system_prompt")
    ])
    def test_safe_format_with_missing_kwargs_leaves_missing_placeholders_unchanged(
        self, prompt_type, templated_prompt_yaml, expected_string, prompts_dir
    ):
        """
        Scenario: safe_format with missing kwargs leaves missing placeholders unchanged
            Given a Prompt with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with only case_name="Miranda v. Arizona"
            Then the placeholder "{case_name}" should be replaced
            And the placeholder "{summary_length}" should remain unchanged
        """
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, case_name="Miranda v. Arizona")
        actual_content = getattr(prompt, prompt_type).content
        assert expected_string in actual_content, f"'{expected_string}' is not in user_prompt.content '{actual_content}'"


    def test_safe_format_with_extra_kwargs_raises_valueerror(self, templated_prompt_yaml, prompts_dir):
        """
        Scenario: safe_format with extra kwargs raises ValueError
            Given a Prompt with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with case_name="Miranda v. Arizona", summary_length=150, extra_arg="extra"
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'Unused formatting arguments'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, case_name="Miranda v. Arizona", summary_length=150, extra_arg="extra")

    def test_safe_format_with_malformed_placeholders_raises_valueerror(self, malformed_placeholder_yaml, prompts_dir):
        """
        Scenario: safe_format with malformed placeholders raises ValueError
            Given a Prompt with malformed placeholder "{case_name"
            When 'load_prompt_from_yaml' is called
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'Malformed placeholder'):
            load_prompt_from_yaml("malformed_placeholder", prompt_dir=prompts_dir, case_name="test")


# ============================================================================
# Rule: Edge Cases for YAML files
# ============================================================================

class TestEdgeCasesForYAMLFiles:
    """
    Rule: Edge Cases for YAML files
    """

    def test_yaml_with_extra_fields_raises_valueerror(self, extra_fields_yaml, prompts_dir):
        """
        Scenario: YAML with extra fields raises ValueError
            Given a YAML file with extra irrelevant fields "min_p", "max_p", "random_field"
            When I load the prompt
            Then an ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'Extra inputs are not permitted'):
            load_prompt_from_yaml("extra_fields", prompt_dir=prompts_dir)

    def test_yaml_with_different_field_loads_successfully(self, different_order_yaml, prompts_dir):
        """
        Scenario: YAML with different field loads successfully
            Given a YAML file with fields in a different order
            When I load the prompt
            Then an ValueError should be raised
        """
        prompt = load_prompt_from_yaml("different_order", prompt_dir=prompts_dir)
        assert isinstance(prompt, Prompt), f"Expected a Prompt object, but got {type(prompt).__name__}"

    def test_large_prompt_content_loads_successfully(self, large_content_yaml, prompts_dir):
        """
        Scenario: Large prompt content loads successfully
            Given a YAML file with very large prompt content
            When I load the prompt
            Then a Prompt object should be returned
        """
        expected_length = 10000
        prompt = load_prompt_from_yaml("large_content", prompt_dir=prompts_dir)
        assert len(prompt.system_prompt.content) == expected_length, \
            f"Expected content length '{expected_length}', but got {len(prompt.system_prompt.content)}"


# ============================================================================
# Rule: Edge Cases for Settings
# ============================================================================

class TestEdgeCasesForSettings:
    """
    Rule: Edge Cases for Settings
    """

    def test_settings_match_placeholders_in_prompts_raises_valueerror(self, settings_placeholder_yaml, prompts_dir):
        """
        Scenario: Settings match placeholders in prompts raises ValueError
            Given a YAML file where settings fields match prompt placeholders
            When I load the prompt
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'overlap between settings and prompt placeholders'):
            load_prompt_from_yaml("settings_placeholder", prompt_dir=prompts_dir, temperature=0.9)


# ============================================================================
# Rule: Edge Cases for load_prompt_from_yaml function
# ============================================================================

class TestEdgeCasesForLoadPromptFromYamlFunction:
    """
    Rule: Edge Cases for load_prompt_from_yaml function
    """

    def test_yaml_with_null_values_raises_valueerror(self, null_values_yaml, prompts_dir):
        """
        Scenario: YAML with null values raises ValueError
            Given a YAML file with null values for required fields
            When I load the prompt
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'validation error'):
            load_prompt_from_yaml("null_values", prompt_dir=prompts_dir)

    @pytest.mark.parametrize("container_type, container_values", [
        ("tuple", (1, 2)),
        ("set", {1, 2}),
        ("list", [1, 2]),
        ("dict", {'a': 1, 'b': 2})
    ])
    def test_kwargs_with_container_types_are_unpacked_in_prompt(
        self,container_type, container_values, templated_prompt_yaml, prompts_dir
    ):
        """
        Scenario: kwargs with container types are unpacked in prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs using container types "tuple", "set", "list", "dict"
            Then the containers values should be unpacked into the prompt content
        """
        kwargs = {"summary_length": container_values}
        prompt = load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, **kwargs)
        content = getattr(prompt.system_prompt, 'content')
        assert str(container_values) in content, f"{container_type} not unpacked correctly in prompt content '{content}'"


    @pytest.mark.parametrize("unreasonable_type, value", [
        ("bytes", b"bytes"),
        ("function", lambda x: x),
        ("class", str),
        ("module", pytest),
    ])
    def test_kwargs_with_unreasonable_types_raises_valueerror(self, unreasonable_type, value, templated_prompt_yaml, prompts_dir):
        """
        Scenario: kwargs with unreasonable types raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs of unreasonable types "bytes", "function", "class", "module"
            Then a ValueError should be raised 
        """
        with pytest.raises(ValueError, match=r'Unsupported type for formatting'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=value)


@pytest.mark.parametrize("unreasonable_value", [
    pytest.param("a" * 100000, id="super_big_string"),
    pytest.param(10**100, id="super_big_number"),
    pytest.param({"nested": {"very": {"deep": {"structure": "value"}}}}, id="nested_structure")
])
class TestKwargsWithUnreasonableValuesRaisesValueError:

    def test_load_yaml_kwargs_with_unreasonable_values_raises_valueerror(
            self, templated_prompt_yaml, prompts_dir, unreasonable_value
        ):
        """
        Scenario: kwargs with unreasonable values raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs having unreasonable values "super_big_string", "super_big_number", "nested_structure"
            Then a ValueError should be raised
        """
        with pytest.raises(ValueError, match=r'invalid kwarg value for formatting'):
            load_prompt_from_yaml("templated_prompt", prompt_dir=prompts_dir, summary_length=unreasonable_value)

    def test_safe_format_kwargs_with_unreasonable_values_raises_valueerror(
            self, loaded_template_prompt_from_yaml, prompts_dir, unreasonable_value
        ):
        """
        Scenario: kwargs with unreasonable values raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I call safe_format with kwargs having unreasonable values "super_big_string", "super_big_number", "nested_structure"
            Then a ValueError should be raised
        """
        kwargs = {"summary_length": unreasonable_value}
        with pytest.raises(ValueError, match=r'invalid kwarg value for formatting'):
            loaded_template_prompt_from_yaml.safe_format(**kwargs)
