Feature: Load Prompt from YAML
  As a system integrating with LLM services
  I want to have a wrapper client
  So that I can configure dependencies and manage LLM interactions.

    Background:
        Given an LLM client dependency is available 
        And the client dependency is properly initialized
        And a valid configuration for the LLM client
        And 

    Rule: LLM Client Initializes with Expected Parameters and Dependencies

        Scenario: LLM Client initializes successfully
            Given I have a valid configuration for the LLM client
            When I initialize the LLM client
            Then the client should be set up with the correct parameters

    Rule: LLM Client Interaction "stream_response"

    Rule: LLM Client Interaction "classify_intent"

    Rule: Error Handling in LLM Client

    Rule: Edge Cases in LLM Client