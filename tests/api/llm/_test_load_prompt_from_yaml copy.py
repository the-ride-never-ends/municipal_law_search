#!/usr/bin/env python3

import pytest
import yaml


from app.api_.llm_.load_prompt_from_yaml import load_prompt_from_yaml, Prompt, PromptFields, Settings


from tests.api.llm.conftest import FixtureError

@pytest.fixture
def valid_system_prompt_string():
    return "You are a {title}. Provide accurate and concise information based on the American Law dataset."

@pytest.fixture
def valid_user_prompt_string():
    return "Please provide a concise summary of the case {case_name}. Do it in {summary_length} words."

@pytest.fixture
def valid_args():
    return ("legal_summary_prompt",)

@pytest.fixture
def prompt_dir(tmp_path):
    try:
        prompts_path = tmp_path / "prompts"
        prompts_path.mkdir()
    except Exception as e:
        raise FixtureError(f"Error creating prompt_dir fixture: {e}") from e
    yield prompts_path


@pytest.fixture
def valid_kwargs(prompt_dir):
    return {
        "prompt_dir": prompt_dir,
        "title": "legal expert",
        "case_name": "Roe v. Wade",
        "summary_length": 150
    }

@pytest.fixture
def valid_setting_kwargs():
    return {
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

@pytest.fixture
def valid_settings(valid_setting_kwargs):
    try:
        settings = Settings(**valid_setting_kwargs)
    except Exception as e:
        raise FixtureError(f"Error creating settings_fixture: {e}") from e
    return settings

@pytest.fixture
def expected_prompt(valid_system_prompt_string, valid_user_prompt_string, valid_kwargs):
    try:
        return {
            "system_prompt": valid_system_prompt_string.format(**valid_kwargs),
            "user_prompt": valid_user_prompt_string.format(**valid_kwargs)
        }
    except Exception as e:
        raise FixtureError(f"Error creating expected_prompt fixture: {e}") from e

def make_valid_yaml_data(
    system_prompt: str,
    user_prompt: str
) -> dict:
    return {
        "client": "openai",
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }


@pytest.fixture
def make_prompt_file(prompt_dir):
    def _make_prompt_file(filename, prompt_data):
        _prompt_date = {
            "client": "openai",
        }
        _prompt_date.update(prompt_data)
        try:
            yaml_file = prompt_dir / f"{filename}.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(prompt_data, f)
        except Exception as e:
            raise FixtureError(f"Error creating valid_prompt_yaml fixture: {e}") from e
    return _make_prompt_file


@pytest.fixture
def valid_prompt_yaml(make_prompt_file, valid_system_prompt_string, valid_user_prompt_string):
    """Create a valid prompt YAML file and return its path."""

    prompt_data = {
        "system_prompt": valid_system_prompt_string,
        "user_prompt": valid_user_prompt_string
    }
    yaml_file = make_prompt_file(
        filename="legal_summary_prompt",
        prompt_data=prompt_data,
    )
    return yaml_file

@pytest.fixture
def invalid_prompt_yaml(make_prompt_file, valid_system_prompt_string):
    """Create an invalid prompt YAML file (missing user_prompt) and return its path."""

    prompt_data = {
        "system_prompt": valid_system_prompt_string
        # Missing user_prompt
    }
    yaml_file = make_prompt_file(
        filename="invalid_prompt",
        prompt_data=prompt_data,
    )
    return yaml_file

def corrupted_yaml_file(prompt_dir):
    """Create a corrupted YAML file and return its path."""
    corrupted_content = """
    system_prompt: |
      You are a {title}. Provide accurate and concise information based on the American Law dataset.
    user_prompt: |
      Please provide a concise summary of the case {case_name}. Do it in {summary_length} words.
      - This line is not properly indented
     another_bad_line
    """
    yaml_file = prompt_dir / "corrupted_prompt.yaml"
    try:
        with open(yaml_file, 'w') as f:
            f.write(corrupted_content)
    except Exception as e:
        raise FixtureError(f"Error creating corrupted_yaml_file fixture: {e}") from e
    return yaml_file

@pytest.fixture
def constants(valid_system_prompt_string, valid_user_prompt_string, valid_kwargs):
    return {
        "valid_prompt_name": "legal_summary_prompt",
        "invalid_prompt_name": "non_existent_prompt",
        "valid_system_prompt_string": valid_system_prompt_string,
        "valid_user_prompt_string": valid_user_prompt_string,
        "valid_kwargs": valid_kwargs,
        "invalid_kwargs": {
            "case_title": "Brown v. Board of Education"  # incorrect key
        }
    }




class TestValidInputs:

    def test_when_called_with_valid_prompt_name_then_returns_prompt(
        self, prompt_dir, constants
    ):
        """
        GIVEN a valid prompt name
        WHEN load_prompt_from_yaml is called
        THEN expect a Prompt object to be returned.
        """
        # Arrange
        prompt_name = constants['valid_prompt_name']

        # Act
        prompt = load_prompt_from_yaml(prompt_name, prompt_dir)

        # Assert
        assert isinstance(prompt, Prompt), f"Expected return type to be Prompt, got {type(prompt).__name__} instead"

    def test_when_called_with_valid_prompt_name_then_prompt_fields_are_correct(
        self, prompt_dir, constants, valid_system_prompt_string, valid_user_prompt_string
    ):
        """
        GIVEN a valid prompt name
        WHEN load_prompt_from_yaml is called
        THEN expect the returned Prompt object to have correct system and user prompt content.
        """
        # Arrange
        prompt_name = constants['valid_prompt_name']

        # Act
        prompt = load_prompt_from_yaml(prompt_name, prompt_dir)

        # Assert
        assert prompt.system_prompt.content == valid_system_prompt_string

    def test_when_called_with_valid_kwargs_then_prompt_is_formatted(
        self, prompt_dir, constants, valid_system_prompt_string, valid_user_prompt_string
    ):
        """
        GIVEN valid formatting kwargs
        WHEN load_prompt_from_yaml is called with those kwargs
        THEN expect the information in those kwargs to be in the prompt string.
        """
        # Arrange
        prompt_name = constants['valid_prompt_name']
        kwargs = constants['valid_kwargs']

        # Act
        prompt = load_prompt_from_yaml(prompt_name, prompt_dir, **kwargs)

        # Assert
        expected_system_content = valid_system_prompt_string.format(**kwargs)
        expected_user_content = valid_user_prompt_string.format(**kwargs)

        assert prompt.system_prompt.content == expected_system_content, \
            "System prompt content was not formatted as expected."


class TestInvalidInputs:
    pass


class TestInvalidFiles:
    pass


class TestEdgeCases:
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



import pytest

from app.api_.llm_.load_prompt_from_yaml import load_prompt_from_yaml, Prompt, PromptFields, Settings

# ============================================================================
# Background Fixtures
# ============================================================================

@pytest.fixture
def prompts_directory_exists_with_valid_yaml_files():
    """
    Given a prompts directory exists with valid YAML files
    """
    pass


@pytest.fixture
def yaml_file_basic_prompt_yaml_contains_prompt_configurations():
    """
    And a YAML file "basic_prompt.yaml" contains prompt configurations
    """
    pass


@pytest.fixture
def yaml_file_placeholder_prompt_yaml_has_placeholders_for_formatting():
    """
    And a YAML file "placeholder_prompt.yaml" has placeholders for formatting
    """
    pass


@pytest.fixture
def yaml_file_custom_settings_yaml_has_custom_settings():
    """
    And a YAML file "custom_settings.yaml" has custom settings
    """
    pass


@pytest.fixture
def yaml_file_no_settings_yaml_has_no_settings_section():
    """
    And a YAML file "no_settings.yaml" has no settings section
    """
    pass


@pytest.fixture
def yaml_file_malformed_yaml_yaml_is_malformed():
    """
    And a YAML file "malformed_yaml.yaml" is malformed
    """
    pass


@pytest.fixture
def yaml_file_bad_settings_yaml_has_invalid_settings():
    """
    And a YAML file "bad_settings.yaml" has invalid settings
    """
    pass


@pytest.fixture
def yaml_file_missing_fields_yaml_is_missing_required_fields():
    """
    And a YAML file "missing_fields.yaml" is missing required fields
    """
    pass


@pytest.fixture
def yaml_file_invalid_values_yaml_has_invalid_values():
    """
    And a YAML file "invalid_values.yaml" has invalid values
    """
    pass


# ============================================================================
# Rule: Loads Prompts from YAML Files
# ============================================================================

class TestLoadsPromptsFromYAMLFiles:
    """
    Rule: Loads Prompts from YAML Files
    """

    def test_successfully_load_a_basic_prompt(self):
        """
        Scenario: Successfully load a basic prompt
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then a 'Prompt' object should be returned
        """
        pass

    def test_loaded_prompt_has_correct_client_type(self):
        """
        Scenario: Loaded prompt has correct client type
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'Prompt' should have the client type specified in the file
        """
        pass

    def test_loaded_prompt_has_configured_settings(self):
        """
        Scenario: Loaded prompt has configured Settings
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'Settings' should have the values specified in the file
        """
        pass

    def test_loaded_prompt_has_system_prompt_role_and_content(self):
        """
        Scenario: Loaded prompt has system_prompt role and content
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'system_prompt' should have 'role' and 'content'
        """
        pass

    def test_loaded_prompt_has_user_prompt_role_and_content(self):
        """
        Scenario: Loaded prompt has user_prompt role and content
            Given a YAML file "basic_prompt.yaml" exists
            When I load the prompt named "basic_prompt"
            Then the 'user_prompt' should have 'role' and 'content'
        """
        pass


# ============================================================================
# Rule: Prompt Formatting with Placeholders
# ============================================================================

class TestPromptFormattingWithPlaceholders:
    """
    Rule: Prompt Formatting with Placeholders
    """

    def test_load_and_format_templated_prompt(self):
        """
        Scenario: Load and format templated prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load "templated_prompt" with case_name="Roe v. Wade" and summary_length=150
            Then a 'Prompt' object should be returned
        """
        pass

    def test_placeholder_formatting_updates_system_prompt(self):
        """
        Scenario: Placeholder formatting updates system_prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load "templated_prompt" with summary_length=150
            Then the 'system_prompt' should contain "150"
        """
        pass

    def test_unused_formatting_arguments_raise_valueerror(self):
        """
        Scenario: Unused formatting arguments raise ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with extra unused keyword arguments
            Then a ValueError should be raised
        """
        pass


# ============================================================================
# Rule: Prompt contains custom settings if provided
# ============================================================================

class TestPromptContainsCustomSettingsIfProvided:
    """
    Rule: Prompt contains custom settings if provided
    """

    def test_load_prompt_with_custom_settings(self):
        """
        Scenario: Load prompt with custom settings
            Given a YAML file 'custom_settings.yaml' with temperature=0.7
            When I load the prompt
            Then the Settings should have temperature 0.7
        """
        pass

    def test_custom_settings_include_max_tokens(self):
        """
        Scenario: Custom settings include max_tokens
            Given a YAML file 'custom_settings.yaml' with max_tokens=500
            When I load the prompt
            Then Settings should have max_tokens 500
        """
        pass

    def test_custom_settings_include_top_p(self):
        """
        Scenario: Custom settings include top_p
            Given a YAML file 'custom_settings.yaml' with top_p=0.9
            When I load the prompt
            Then Settings should have top_p 0.9
        """
        pass

    def test_custom_settings_use_default_frequency_penalty(self):
        """
        Scenario: Custom settings use default frequency_penalty
            Given a YAML file 'custom_settings.yaml' with custom settings
            When I load the prompt
            Then frequency_penalty should default to 0.0
        """
        pass

    def test_custom_settings_use_default_presence_penalty(self):
        """
        Scenario: Custom settings use default presence_penalty
            Given a YAML file 'custom_settings.yaml' with custom settings
            When I load the prompt
            Then presence_penalty should default to 0.0
        """
        pass


# ============================================================================
# Rule: Prompt contains default settings when none are provided
# ============================================================================

class TestPromptContainsDefaultSettingsWhenNoneAreProvided:
    """
    Rule: Prompt contains default settings when none are provided
    """

    def test_default_settings_include_temperatures(self):
        """
        Scenario: Default settings include temperatures
            Given a YAML file without settings
            When I load the prompt
            Then Settings should use default temperature 0.0
        """
        pass

    def test_default_settings_include_max_tokens(self):
        """
        Scenario: Default settings include max_tokens
            Given a YAML file without settings
            When I load the prompt
            Then max_tokens should default to 4096
        """
        pass

    def test_default_settings_include_top_p(self):
        """
        Scenario: Default settings include top_p
            Given a YAML file without settings
            When I load the prompt
            Then top_p should default to 1.0
        """
        pass

    def test_default_settings_include_frequency_penalty(self):
        """
        Scenario: Default settings include frequency_penalty
            Given a YAML file without settings
            When I load the prompt
            Then frequency_penalty should default to 0.0
        """
        pass

    def test_default_settings_include_presence_penalty(self):
        """
        Scenario: Default settings include presence_penalty
            Given a YAML file without settings
            When I load the prompt
            Then presence_penalty should default to 0.0
        """
        pass


# ============================================================================
# Rule: Error Handling for Invalid Required Arguments
# ============================================================================

class TestErrorHandlingForInvalidRequiredArguments:
    """
    Rule: Error Handling for Invalid Required Arguments
    """

    def test_non_string_prompt_name_raises_typeerror(self):
        """
        Scenario: Non-string prompt name raises TypeError
            Given a prompt name that is not a string
            When I attempt to load the prompt with that name
            Then a TypeError should be raised
        """
        pass

    def test_empty_name_raises_valueerror(self):
        """
        Scenario: Empty name raises ValueError
            Given a prompt name that is empty or whitespace
            When I attempt to load the prompt with that name
            Then a ValueError should be raised
        """
        pass

    def test_non_path_prompt_dir_raises_typeerror(self):
        """
        Scenario: Non-Path prompt_dir raises TypeError
            Given a prompt_dir that is not a Path
            When I attempt to load the prompt from that directory
            Then a TypeError should be raised
        """
        pass

    def test_non_existent_prompt_dir_raises_ioerror(self):
        """
        Scenario: Non-existent prompt_dir raises IOError
            Given a prompt_dir that does not exist
            When I attempt to load a prompt from that directory
            Then an IOError should be raised
        """
        pass


# ============================================================================
# Rule: YAML File Validation Errors
# ============================================================================

class TestYAMLFileValidationErrors:
    """
    Rule: YAML File Validation Errors
    """

    def test_non_existent_yaml_raises_ioerror(self):
        """
        Scenario: Non-existent YAML raises IOError
            Given a prompt name with no matching YAML file
            When I attempt to load the prompt
            Then an IOError should be raised
        """
        pass

    def test_malformed_yaml_raises_ioerror(self):
        """
        Scenario: Malformed YAML raises IOError
            Given a prompt name that points to a malformed YAML file
            When I attempt to load the prompt
            Then an IOError should be raised
        """
        pass

    def test_missing_required_fields_raises_valueerror(self):
        """
        Scenario: Missing required fields raises ValueError
            Given a YAML file missing field "client", or "system_prompt", or "user_prompt"
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_invalid_client_raises_valueerror(self):
        """
        Scenario: Invalid client raises ValueError
            Given a YAML file 'bad_settings.yaml' with client="invalid_client"
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_invalid_system_prompt_role_raises_valueerror(self):
        """
        Scenario: Invalid system_prompt role raises ValueError
            Given a YAML file 'bad_settings.yaml' with system_prompt role="assistant"
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_invalid_user_prompt_role_raises_valueerror(self):
        """
        Scenario: Invalid user_prompt role raises ValueError
            Given a YAML file 'bad_settings.yaml' with user_prompt role="not_a_role"
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_empty_prompt_content_raises_valueerror(self):
        """
        Scenario: Empty prompt content raises ValueError
            Given a YAML file 'bad_settings.yaml' with empty system_prompt content
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_negative_temperature_raises_valueerror(self):
        """
        Scenario: Negative temperature raises ValueError
            Given a YAML file 'bad_settings.yaml' with temperature -0.5
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_zero_max_tokens_raises_valueerror(self):
        """
        Scenario: Zero max_tokens raises ValueError
            Given a YAML file 'bad_settings.yaml' with max_tokens set to 0
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_negative_top_p_raises_valueerror(self):
        """
        Scenario: Negative top_p raises ValueError
            Given a YAML file 'bad_settings.yaml' with top_p < 0
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_non_unicode_prompts_raise_valueerror(self):
        """
        Scenario: Non-unicode Prompts raise ValueError
            Given a YAML file 'invalid_values.yaml' with non-unicode system_prompt content
            When I attempt to load the prompt
            Then a ValueError should be raised
        """
        pass


# ============================================================================
# Rule: safe_format Method Behavior
# ============================================================================

class TestSafeFormatMethodBehavior:
    """
    Rule: safe_format Method Behavior
    """

    def test_safe_format_with_no_arguments_does_not_error(self):
        """
        Scenario: safe_format with no arguments does not error
            Given a loaded Prompt object
            When 'safe_format' is called without kwargs
            Then a Prompt object should be returned
        """
        pass

    def test_safe_format_keeps_content_unchanged_with_no_kwargs(self):
        """
        Scenario: safe_format keeps content unchanged with no kwargs
            Given a loaded Prompt object
            When 'safe_format' is called with no arguments
            Then the content should remain unchanged
        """
        pass

    def test_safe_format_that_produces_invalid_content_raises_valueerror(self):
        """
        Scenario: safe_format that produces invalid content raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When formatting arguments produce various invalid content
            Then a ValueError should be raised
        """
        pass

    def test_safe_format_with_valid_placeholders(self):
        """
        Scenario: safe_format with valid placeholders
            Given prompts with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with case_name="Brown v. Board" summary_length=200
            Then the placeholder values should be replaced in the prompt content
        """
        pass

    def test_safe_format_with_non_existing_placeholders_raises_valueerror(self):
        """
        Scenario: safe_format with non-existing placeholders raises ValueError
            Given prompts with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with non_existing="value"
            Then a ValueError should be raised
        """
        pass

    def test_safe_format_uses_matching_kwargs_per_prompt(self):
        """
        Scenario: safe_format uses matching kwargs per prompt
            Given a system_prompt with placeholder "{topic}" 
            And a user_prompt with placeholder "{length}"
            When 'safe_format' is called with topic="law" and length=100
            Then the system_prompt should contain "law"
            And the user_prompt should contain "100"
        """
        pass

    def test_safe_format_with_the_same_placeholder_in_both_prompts(self):
        """
        Scenario: safe_format with the same placeholder in both prompts
            Given a system_prompt and user_prompt both with placeholder "{case_name}"
            When 'safe_format' is called with case_name="Marbury v. Madison"
            Then both prompts should contain "Marbury v. Madison"
        """
        pass

    def test_safe_format_with_missing_kwargs_leaves_missing_placeholders_unchanged(self):
        """
        Scenario: safe_format with missing kwargs leaves missing placeholders unchanged
            Given a Prompt with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with only case_name="Miranda v. Arizona"
            Then the placeholder "{case_name}" should be replaced
            And the placeholder "{summary_length}" should remain unchanged
        """
        pass

    def test_safe_format_with_extra_kwargs_raises_valueerror(self):
        """
        Scenario: safe_format with extra kwargs raises ValueError
            Given a Prompt with placeholders "{case_name}" and "{summary_length}"
            When 'safe_format' is called with case_name="Miranda v. Arizona", summary_length=150, extra_arg="extra"
            Then a ValueError should be raised
        """
        pass

    def test_safe_format_with_invalid_formatted_content_raises_valueerror(self):
        """
        Scenario: safe_format with invalid formatted content raises ValueError
            Given a Prompt object
            When 'safe_format' produces prompts that violate validation constraints
            Then a ValueError should be raised
        """
        pass

    def test_safe_format_with_malformed_placeholders_raises_valueerror(self):
        """
        Scenario: safe_format with malformed placeholders raises ValueError
            Given a Prompt with malformed placeholder "{case_name"
            When 'safe_format' is called
            Then a ValueError should be raised
        """
        pass


# ============================================================================
# Rule: Edge Cases for YAML files
# ============================================================================

class TestEdgeCasesForYAMLFiles:
    """
    Rule: Edge Cases for YAML files
    """

    def test_yaml_with_extra_fields_raises_valueerror(self):
        """
        Scenario: YAML with extra fields raises ValueError
            Given a YAML file with extra irrelevant fields "min_p", "max_p", "random_field"
            When I load the prompt
            Then an ValueError should be raised
        """
        pass

    def test_yaml_with_different_field_loads_successfully(self):
        """
        Scenario: YAML with different field loads successfully
            Given a YAML file with fields in a different order
            When I load the prompt
            Then an ValueError should be raised
        """
        pass

    def test_large_prompt_content_loads_successfully(self):
        """
        Scenario: Large prompt content loads successfully
            Given a YAML file with very large prompt content
            When I load the prompt
            Then a Prompt object should be returned
        """
        pass


# ============================================================================
# Rule: Edge Cases for Settings
# ============================================================================

class TestEdgeCasesForSettings:
    """
    Rule: Edge Cases for Settings
    """

    def test_settings_match_placeholders_in_prompts_raises_valueerror(self):
        """
        Scenario: Settings match placeholders in prompts raises ValueError
            Given a YAML file where settings fields match prompt placeholders
            When I load the prompt
            Then a ValueError should be raised
        """
        pass


# ============================================================================
# Rule: Edge Cases for load_prompt_from_yaml function
# ============================================================================

class TestEdgeCasesForLoadPromptFromYamlFunction:
    """
    Rule: Edge Cases for load_prompt_from_yaml function
    """

    def test_yaml_with_null_values_raises_valueerror(self):
        """
        Scenario: YAML with null values raises ValueError
            Given a YAML file with null values for required fields
            When I load the prompt
            Then a ValueError should be raised
        """
        pass

    def test_kwargs_with_container_types_are_unpacked_in_prompt(self):
        """
        Scenario: kwargs with container types are unpacked in prompt
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs using container types "tuple", "set", "list", "dict"
            Then the containers values should be unpacked into the prompt content
        """
        pass

    def test_kwargs_with_unreasonable_types_raises_valueerror(self):
        """
        Scenario: kwargs with unreasonable types raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs of unreasonable types "bytes", "function", "class", "module", "file_object"
            Then a ValueError should be raised 
        """
        pass

    def test_kwargs_with_unreasonable_values_raises_valueerror(self):
        """
        Scenario: kwargs with unreasonable values raises ValueError
            Given a YAML file "templated_prompt.yaml" contains placeholders
            When I load the prompt with kwargs having unreasonable values "super_big_string", "super_big_number", "nested_structure"
            Then a ValueError should be raised
        """
        pass
