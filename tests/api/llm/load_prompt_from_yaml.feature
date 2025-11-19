Feature: Load Prompt from YAML
  As a system integrating with LLM services
  I want to load prompt configurations from YAML files
  So that prompts can be dynamically configured and formatted

  Background:
    Given a prompts directory exists with valid YAML files
    And a YAML file "basic_prompt.yaml" contains prompt configurations
    And a YAML file "placeholder_prompt.yaml" has placeholders for formatting
    And a YAML file "custom_settings.yaml" has custom settings
    And a YAML file "no_settings.yaml" has no settings section
    And a YAML file "malformed_yaml.yaml" is malformed
    And a YAML file "bad_settings.yaml" has invalid settings
    And a YAML file "missing_fields.yaml" is missing required fields
    And a YAML file "invalid_values.yaml" has invalid values

  Rule: Loads Prompts from YAML Files

    Scenario: Successfully load a basic prompt
        Given a YAML file "basic_prompt.yaml" exists
        When I load the prompt named "basic_prompt"
        Then a 'Prompt' object should be returned

    Scenario: Loaded prompt has correct client type
        Given a YAML file "basic_prompt.yaml" exists
        When I load the prompt named "basic_prompt"
        Then the 'Prompt' should have the client type specified in the file

    Scenario: Loaded prompt has configured Settings
        Given a YAML file "basic_prompt.yaml" exists
        When I load the prompt named "basic_prompt"
        Then the 'Settings' should have the values specified in the file

    Scenario: Loaded prompt has system_prompt role and content
        Given a YAML file "basic_prompt.yaml" exists
        When I load the prompt named "basic_prompt"
        Then the 'system_prompt' should have 'role' and 'content'

    Scenario: Loaded prompt has user_prompt role and content
        Given a YAML file "basic_prompt.yaml" exists
        When I load the prompt named "basic_prompt"
        Then the 'user_prompt' should have 'role' and 'content'

  Rule: Prompt Formatting with Placeholders

    Scenario: Load and format templated prompt
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load "templated_prompt" with case_name="Roe v. Wade" and summary_length=150
        Then a 'Prompt' object should be returned

    Scenario: Placeholder formatting updates system_prompt
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load "templated_prompt" with summary_length=150
        Then the 'system_prompt' should contain "150"

    Scenario: Unused formatting arguments raise ValueError
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load the prompt with extra unused keyword arguments
        Then a ValueError should be raised

  Rule: Prompt contains custom settings if provided

    Scenario: Load prompt with custom settings
        Given a YAML file 'custom_settings.yaml' with temperature=0.7
        When I load the prompt
        Then the Settings should have temperature 0.7

    Scenario: Custom settings include max_tokens
        Given a YAML file 'custom_settings.yaml' with max_tokens=500
        When I load the prompt
        Then Settings should have max_tokens 500

    Scenario: Custom settings include top_p
        Given a YAML file 'custom_settings.yaml' with top_p=0.9
        When I load the prompt
        Then Settings should have top_p 0.9

    Scenario: Custom settings use default frequency_penalty
        Given a YAML file 'custom_settings.yaml' with custom settings
        When I load the prompt
        Then frequency_penalty should default to 0.0

    Scenario: Custom settings use default presence_penalty
        Given a YAML file 'custom_settings.yaml' with custom settings
        When I load the prompt
        Then presence_penalty should default to 0.0

  Rule: Prompt contains default settings when none are provided

    Scenario: Default settings include temperatures
        Given a YAML file without settings
        When I load the prompt
        Then Settings should use default temperature 0.0

    Scenario: Default settings include max_tokens
        Given a YAML file without settings
        When I load the prompt
        Then max_tokens should default to 4096

    Scenario: Default settings include top_p
        Given a YAML file without settings
        When I load the prompt
        Then top_p should default to 1.0

    Scenario: Default settings include frequency_penalty
        Given a YAML file without settings
        When I load the prompt
        Then frequency_penalty should default to 0.0

    Scenario: Default settings include presence_penalty
        Given a YAML file without settings
        When I load the prompt
        Then presence_penalty should default to 0.0

  Rule: Error Handling for Invalid Required Arguments

    Scenario: Non-string prompt name raises TypeError
        Given a prompt name that is not a string
        When I attempt to load the prompt with that name
        Then a TypeError should be raised

    Scenario: Empty name raises ValueError
        Given a prompt name that is empty or whitespace
        When I attempt to load the prompt with that name
        Then a ValueError should be raised

    Scenario: Non-Path prompt_dir raises TypeError
        Given a prompt_dir that is not a Path
        When I attempt to load the prompt from that directory
        Then a TypeError should be raised

    Scenario: Non-existent prompt_dir raises IOError
        Given a prompt_dir that does not exist
        When I attempt to load a prompt from that directory
        Then an IOError should be raised

  Rule: YAML File Validation Errors

    Scenario: Non-existent YAML raises IOError
        Given a prompt name with no matching YAML file
        When I attempt to load the prompt
        Then an IOError should be raised

    Scenario: Malformed YAML raises IOError
        Given a prompt name that points to a malformed YAML file
        When I attempt to load the prompt
        Then an IOError should be raised

    Scenario: Missing required fields raises ValueError
        Given a YAML file missing field "client", or "system_prompt", or "user_prompt"
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Invalid client raises ValueError
        Given a YAML file 'bad_settings.yaml' with client="invalid_client"
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Invalid system_prompt role raises ValueError
        Given a YAML file 'bad_settings.yaml' with system_prompt role="assistant"
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Invalid user_prompt role raises ValueError
        Given a YAML file 'bad_settings.yaml' with user_prompt role="not_a_role"
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Empty prompt content raises ValueError
        Given a YAML file 'bad_settings.yaml' with empty system_prompt content
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Negative temperature raises ValueError
        Given a YAML file 'bad_settings.yaml' with temperature -0.5
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Zero max_tokens raises ValueError
        Given a YAML file 'bad_settings.yaml' with max_tokens set to 0
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Negative top_p raises ValueError
        Given a YAML file 'bad_settings.yaml' with top_p < 0
        When I attempt to load the prompt
        Then a ValueError should be raised

    Scenario: Non-unicode Prompts raise ValueError
        Given a YAML file 'invalid_values.yaml' with non-unicode system_prompt content
        When I attempt to load the prompt
        Then a ValueError should be raised

  Rule: safe_format Method Behavior

    Scenario: safe_format with no arguments does not error
        Given a loaded Prompt object
        When 'safe_format' is called without kwargs
        Then a Prompt object should be returned

    Scenario: safe_format keeps content unchanged with no kwargs
        Given a loaded Prompt object
        When 'safe_format' is called with no arguments
        Then the content should remain unchanged

    Scenario: safe_format that produces invalid content raises ValueError
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When formatting arguments produce various invalid content
        Then a ValueError should be raised

    Scenario: safe_format with valid placeholders
        Given prompts with placeholders "{case_name}" and "{summary_length}"
        When 'safe_format' is called with case_name="Brown v. Board" summary_length=200
        Then the placeholder values should be replaced in the prompt content

    Scenario: safe_format with non-existing placeholders raises ValueError
        Given prompts with placeholders "{case_name}" and "{summary_length}"
        When 'safe_format' is called with non_existing="value"
        Then a ValueError should be raised

    Scenario: safe_format uses matching kwargs per prompt
        Given a system_prompt with placeholder "{topic}" 
        And a user_prompt with placeholder "{length}"
        When 'safe_format' is called with topic="law" and length=100
        Then the system_prompt should contain "law"
        And the user_prompt should contain "100"

    Scenario: safe_format with the same placeholder in both prompts
        Given a system_prompt and user_prompt both with placeholder "{case_name}"
        When 'safe_format' is called with case_name="Marbury v. Madison"
        Then both prompts should contain "Marbury v. Madison"

    Scenario: safe_format with missing kwargs leaves missing placeholders unchanged
        Given a Prompt with placeholders "{case_name}" and "{summary_length}"
        When 'safe_format' is called with only case_name="Miranda v. Arizona"
        Then the placeholder "{case_name}" should be replaced
        And the placeholder "{summary_length}" should remain unchanged

    Scenario: safe_format with extra kwargs raises ValueError
        Given a Prompt with placeholders "{case_name}" and "{summary_length}"
        When 'safe_format' is called with case_name="Miranda v. Arizona", summary_length=150, extra_arg="extra"
        Then a ValueError should be raised

    Scenario: safe_format with invalid formatted content raises ValueError
        Given a Prompt object
        When 'safe_format' produces prompts that violate validation constraints
        Then a ValueError should be raised

    Scenario: safe_format with malformed placeholders raises ValueError
        Given a Prompt with malformed placeholder "{case_name"
        When 'safe_format' is called
        Then a ValueError should be raised

  Rule: Edge Cases for YAML files

    Scenario: YAML with extra fields raises ValueError
        Given a YAML file with extra irrelevant fields "min_p", "max_p", "random_field"
        When I load the prompt
        Then an ValueError should be raised

    Scenario: YAML with different field loads successfully
        Given a YAML file with fields in a different order
        When I load the prompt
        Then an ValueError should be raised

    Scenario: Large prompt content loads successfully
        Given a YAML file with very large prompt content
        When I load the prompt
        Then a Prompt object should be returned

  Rule: Edge Cases for Settings

    Scenario: Settings match placeholders in prompts raises ValueError
        Given a YAML file where settings fields match prompt placeholders
        When I load the prompt
        Then a ValueError should be raised

  Rule: Edge Cases for load_prompt_from_yaml function

    Scenario: YAML with null values raises ValueError
        Given a YAML file with null values for required fields
        When I load the prompt
        Then a ValueError should be raised

    Scenario: kwargs with container types are unpacked in prompt
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load the prompt with kwargs using container types "tuple", "set", "list", "dict"
        Then the containers values should be unpacked into the prompt content

    Scenario: kwargs with unreasonable types raises ValueError
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load the prompt with kwargs of unreasonable types "bytes", "function", "class", "module", "file_object"
        Then a ValueError should be raised 

    Scenario: kwargs with unreasonable values raises ValueError
        Given a YAML file "templated_prompt.yaml" contains placeholders
        When I load the prompt with kwargs having unreasonable values "super_big_string", "super_big_number", "nested_structure"
        Then a ValueError should be raised
