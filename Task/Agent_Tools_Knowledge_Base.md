# Agent Tools Knowledge Base

## 1. Introduction
_Brief overview of the knowledge base and its purpose for AI agents._

## 2. Knowledge Base Schema Definition
_Details on the structure and fields used to define tools._

*   **2.1. Core Tool Attributes:**
    *   `tool_id`: (String, Mandatory) Unique identifier for the tool. Format: `namespace.tool_name` (e.g., `system.file_writer`, `custom.image_analyzer`).
    *   `tool_name`: (String, Mandatory) Human-readable name for the tool.
    *   `description`: (String, Mandatory) Detailed explanation of what the tool does, its purpose, and use cases.
    *   `version`: (String, Mandatory) Semantic versioning (e.g., `1.0.2`).
    *   `author`: (String, Optional) Creator of the tool definition.
    *   `creation_date`: (Date, Optional) Date of tool definition creation.
    *   `status`: (Enum, Optional) Current status of the tool (e.g., `development`, `active`, `deprecated`, `experimental`). Default: `experimental`.

*   **2.2. Input Parameters:** (Array of Objects, Optional)
    *   Each object represents an input parameter with the following fields:
        *   `name`: (String, Mandatory) Parameter name.
        *   `description`: (String, Mandatory) What this parameter is for.
        *   `type`: (Enum, Mandatory) Data type (e.g., `string`, `integer`, `float`, `boolean`, `array`, `object`, `file_path`).
        *   `format`: (String, Optional) Specific format if applicable (e.g., date format `YYYY-MM-DD`, regex pattern for string).
        *   `required`: (Boolean, Mandatory) Is this parameter mandatory?
        *   `default_value`: (Any, Optional) Default value if not provided.
        *   `options`: (Array, Optional) For `enum`-like behavior, provide a list of possible values.
        *   `validation_rules`: (Array of Objects, Optional) Rules for validating the parameter (e.g., min/max length for string, range for number). Each rule object:
            *   `rule_type`: (String, Mandatory) e.g., `minLength`, `maxLength`, `minValue`, `maxValue`, `pattern`.
            *   `value`: (Any, Mandatory) The value associated with the rule type.
            *   `error_message`: (String, Optional) Custom error message if validation fails.

*   **2.3. Output Parameters:** (Array of Objects, Optional)
    *   Each object represents an output value with the following fields:
        *   `name`: (String, Mandatory) Output value name.
        *   `description`: (String, Mandatory) What this output value represents.
        *   `type`: (Enum, Mandatory) Data type (e.g., `string`, `integer`, `json_object`, `file_path`, `status_code`).
        *   `format`: (String, Optional) Specific format if applicable.
        *   `example`: (Any, Optional) An example of what this output might look like.

*   **2.4. Dependencies:** (Object, Optional)
    *   `required_tools`: (Array of Strings, Optional) List of `tool_id`s that this tool depends on.
    *   `libraries`: (Array of Objects, Optional) External libraries needed. Each object:
        *   `name`: (String, Mandatory) Library name.
        *   `version`: (String, Optional) Required version.
        *   `language`: (String, Optional) e.g., `python`, `javascript`.
        *   `install_command`: (String, Optional) Command to install the library.
    *   `environment_variables`: (Array of Strings, Optional) List of environment variable names required by the tool.
    *   `os_compatibility`: (Array of Strings, Optional) Compatible operating systems (e.g., `windows`, `linux`, `macos`).

*   **2.5. Execution Commands/API Endpoints:** (Object, Mandatory)
    *   `type`: (Enum, Mandatory) How the tool is executed (e.g., `cli`, `api`, `python_script`, `bash_script`).
    *   **For `cli` type:**
        *   `command_template`: (String, Mandatory) The command line template with placeholders for input parameters (e.g., `python script.py --input {input_file} --option {value}`).
        *   `working_directory`: (String, Optional) Path to the directory where the command should be executed.
    *   **For `api` type:**
        *   `base_url`: (String, Mandatory) The base URL for the API.
        *   `endpoint`: (String, Mandatory) The specific API endpoint path.
        *   `method`: (Enum, Mandatory) HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`).
        *   `headers`: (Object, Optional) Key-value pairs for HTTP headers. Parameter placeholders can be used.
        *   `request_body_schema`: (Object, Optional) JSON schema definition for the request body, if applicable (for POST/PUT).
        *   `authentication`: (Object, Optional)
            *   `auth_type`: (Enum, Mandatory) e.g., `apiKey`, `oauth2`, `bearerToken`.
            *   `details`: (Object, Mandatory) Specific details for the auth type (e.g., key name and location for `apiKey`).
    *   **For `python_script`/`bash_script` type:**
        *   `script_path`: (String, Mandatory) Path to the script file within the repository or a predefined location.
        *   `interpreter`: (String, Optional) e.g., `python3`, `bash`. If not provided, system default is assumed or derived from shebang.
        *   `arguments_passing_method`: (Enum, Optional) How arguments are passed (e.g., `command_line_args`, `stdin_json`). Default: `command_line_args`.

*   **2.6. Configuration Options:** (Array of Objects, Optional)
    *   Tool-specific settings that are not direct input parameters but affect its behavior.
    *   Each object:
        *   `name`: (String, Mandatory) Configuration key.
        *   `description`: (String, Mandatory) Purpose of this configuration.
        *   `type`: (Enum, Mandatory) Data type.
        *   `default_value`: (Any, Optional).
        *   `environment_variable_override`: (String, Optional) Name of an environment variable that can override this setting.

*   **2.7. Versioning (for the KB Schema itself):**
    *   `schema_version`: (String, Mandatory) Version of this knowledge base schema itself (e.g., `1.0.0`).
    *   `changelog_pointer`: (String, Optional) Link or reference to a changelog for the schema.

## 3. Tool Definition Templates
_Standardized templates for defining various types of tools._

*   **3.1. Template for CLI Tools:**
    ```markdown
    ---
    tool_id: "namespace.cli_tool_example"
    tool_name: "Example CLI Tool"
    description: "This is an example template for a command-line interface tool."
    version: "1.0.0"
    author: "AI Agent KB Generator"
    status: "experimental"

    input_parameters:
      - name: "inputFile"
        description: "Path to the input file."
        type: "file_path"
        required: true
        validation_rules:
          - rule_type: "fileExists" # Custom rule, implies agent needs to check
            value: true
            error_message: "Input file must exist."
      - name: "logLevel"
        description: "Logging verbosity."
        type: "string"
        required: false
        default_value: "info"
        options: ["debug", "info", "warn", "error"]

    output_parameters:
      - name: "outputData"
        description: "Result from the CLI tool, typically captured from stdout."
        type: "string" # Or could be json_object if the CLI outputs structured data
      - name: "exitCode"
        description: "The exit code of the CLI command."
        type: "integer"

    dependencies:
      os_compatibility: ["linux", "macos"]
      libraries:
        - name: "jq" # Example if the script internally uses jq
          version: "1.6"
          install_command: "sudo apt-get install jq" # Example

    execution:
      type: "cli"
      command_template: "your_command --input {inputFile} --level {logLevel}"
      working_directory: "/path/to/tool/execution/context" # Optional

    configuration_options:
      - name: "MAX_RETRIES"
        description: "Maximum number of retries on failure."
        type: "integer"
        default_value: 3
        environment_variable_override: "TOOL_MAX_RETRIES"
    ---
    ```

*   **3.2. Template for API-Based Tools:**
    ```markdown
    ---
    tool_id: "namespace.api_tool_example"
    tool_name: "Example API Tool"
    description: "Template for a tool that interacts with an HTTP API."
    version: "1.0.0"
    status: "active"

    input_parameters:
      - name: "userId"
        description: "User ID to fetch data for."
        type: "string"
        required: true
        validation_rules:
          - rule_type: "pattern"
            value: "^[a-zA-Z0-9_-]+$"
            error_message: "User ID must be alphanumeric with hyphens/underscores."
      - name: "includeDetails"
        description: "Flag to include detailed information."
        type: "boolean"
        required: false
        default_value: false

    output_parameters:
      - name: "responseData"
        description: "JSON response from the API."
        type: "json_object"
      - name: "httpStatusCode"
        description: "HTTP status code of the API response."
        type: "integer"

    dependencies:
      required_tools: ["system.network_checker"] # Example dependency

    execution:
      type: "api"
      base_url: "https://api.example.com/v1"
      endpoint: "/users/{userId}" # Path parameter
      method: "GET"
      headers:
        Content-Type: "application/json"
        X-Custom-Header: "SomeValue"
      # request_body_schema: {} # Not needed for GET, but example for POST/PUT
      authentication:
        auth_type: "bearerToken"
        details:
          token_env_variable: "EXAMPLE_API_BEARER_TOKEN" # Agent needs to fetch this from env

    configuration_options:
      - name: "TIMEOUT_SECONDS"
        description: "API request timeout in seconds."
        type: "integer"
        default_value: 30
    ---
    ```

*   **3.3. Template for Script-Based Tools (Python Example):**
    ```markdown
    ---
    tool_id: "namespace.python_script_example"
    tool_name: "Example Python Script Tool"
    description: "Template for a tool executed via a Python script."
    version: "1.1.0"
    status: "development"

    input_parameters:
      - name: "config_json"
        description: "JSON string containing configuration for the script."
        type: "string" # Agent would pass a JSON string
        required: true
        validation_rules:
          - rule_type: "isJSON" # Custom rule, implies agent needs to validate
            value: true
      - name: "data_file"
        description: "Path to a data file the script will process."
        type: "file_path"
        required: true

    output_parameters:
      - name: "result_summary"
        description: "A summary of the script's execution, perhaps from its stdout."
        type: "string"
      - name: "processed_file_path"
        description: "Path to an output file generated by the script."
        type: "file_path"
        example: "/tmp/processed_output.csv"

    dependencies:
      libraries:
        - name: "pandas"
          version: ">=1.3.0"
          language: "python"
          install_command: "pip install pandas>=1.3.0"
      environment_variables: ["PYTHON_SCRIPT_VERBOSE_LOGGING"]

    execution:
      type: "python_script"
      script_path: "scripts/my_python_processor.py" # Relative to a defined base path
      interpreter: "python3"
      arguments_passing_method: "command_line_args" # e.g., script.py --config_json='{...}' --data_file=/path/to/file

    configuration_options:
      - name: "TEMP_DIRECTORY"
        description: "Temporary directory for script operations."
        type: "string"
        default_value: "/tmp"
    ---
    ```

## 4. User Query Templates & Interaction Patterns
_Specific questions and conversation flows for agents to gather user requirements for tools._

*   **4.1. Initial Requirement Gathering:**
    *   _Goal: To obtain a foundational understanding of the user's needs for a new tool or modification of an existing one._
    *   **4.1.1. Understanding Tool Purpose:**
        *   "What is the primary goal you want to achieve with this tool? What problem will it solve?"
        *   "Can you describe the main function or task this tool should perform?"
        *   "Are there any existing tools (even manual processes) that this new tool will replace or augment?"
        *   "Who are the primary users of this tool, and what is their technical proficiency?"
    *   **4.1.2. Defining Inputs:**
        *   "What information or data does this tool need to start its work? Please list all inputs."
        *   "For each input, can you tell me:
            *   What is its name or a short description? (e.g., 'source_file', 'search_query', 'api_key')"
            *   What type of data is it? (e.g., text, a number, a file path, a boolean true/false, a list of items)"
            *   Is this input always required, or is it optional?"
            *   If optional, does it have a default value we should use if it's not provided?"
            *   Are there any specific formats or constraints for this input? (e.g., 'must be a CSV file', 'must be a positive integer', 'text length less than 100 characters')"
            *   "Where will these inputs come from? (e.g., user provides it directly, from another tool's output, read from a file)"
    *   **4.1.3. Defining Outputs:**
        *   "What information or results should this tool produce after it runs successfully?"
        *   "For each output, can you tell me:
            *   What is its name or a short description? (e.g., 'summary_report', 'generated_image_path', 'status_message')"
            *   What type of data will it be? (e.g., text, a JSON object, a file, a boolean status)"
            *   Are there any specific formats for this output? (e.g., 'report should be in PDF format', 'date should be YYYY-MM-DD')"
        *   "How will these outputs be used? (e.g., displayed to the user, saved to a file, passed to another tool)"
    *   **4.1.4. Identifying Constraints and Edge Cases:**
        *   "Are there any limitations or constraints the tool needs to operate under? (e.g., maximum file size, specific operating system, network access required/not_allowed)"
        *   "What should happen if an error occurs? How should the tool report failures?"
        *   "Are there any specific performance requirements? (e.g., 'must complete within 5 seconds')"
        *   "How frequently will this tool be used? Is it for one-off tasks or continuous operation?"
        *   "Are there any security considerations or sensitive data involved?"

*   **4.2. Clarification Dialogues:**
    *   _Goal: To resolve ambiguities and ensure all details are captured accurately._
    *   **Pattern 1: Confirming Understanding**
        *   Agent: "Okay, so to summarize, you need a tool that [rephrases purpose]. It will take [lists inputs and types] and produce [lists outputs and types]. Is that correct?"
    *   **Pattern 2: Probing for Specificity**
        *   User: "I need it to process a file."
        *   Agent: "Understood. When you say 'process a file,' what specific actions should be taken on the file's content? For example, should it transform the data, extract information, or validate its format?"
        *   Agent: "You mentioned the input is a 'text string'. Are there any limitations on the length or character set for this string?"
    *   **Pattern 3: Handling Conflicting Information**
        *   Agent: "Earlier you mentioned the tool needs access to the internet, but later you said it should work offline. Could you clarify this requirement?"
    *   **Pattern 4: Offering Options/Suggesting Alternatives**
        *   Agent: "For the output format, you mentioned 'a report'. Would a plain text file be sufficient, or would you prefer something like a CSV, JSON, or PDF?"
        *   Agent: "There's an existing tool, `[tool_id]`, that performs a similar function. Would you like to see if it meets your needs, or perhaps we can adapt it?"

*   **4.3. Feedback Loops for Refinement:**
    *   _Goal: To allow users to review and iteratively improve the tool specification before and after generation._
    *   **Pre-Generation Review:**
        *   Agent: "Based on our conversation, I've drafted a specification for the tool. Please review it: [Presents structured specification based on KB schema]. Are there any changes or additions you'd like to make?"
    *   **Post-Generation/Testing Feedback:**
        *   Agent: "I've created a first version of the tool: `[new_tool_id]`. Would you like to test it with some sample inputs?"
        *   Agent (after test): "How did the tool perform? Did it meet your expectations? Were the outputs correct?"
        *   Agent: "If there are any issues or areas for improvement, please let me know so I can refine the tool."

## 5. Decision Trees & Logic Flows for Tool Handling
_Logic for agents to select, create, or configure tools based on user input and context._

*   **5.1. Tool Selection Logic (Based on keywords, required inputs/outputs):**
    *   _Agent's internal thought process for choosing an existing tool._
    *   **Phase 1: Keyword Matching & Semantic Search**
        1.  Analyze user request for keywords related to actions (e.g., "read," "write," "convert," "analyze," "download") and objects (e.g., "file," "image," "text," "URL," "data").
        2.  Query the KB: Search `tool_name` and `description` fields for these keywords and their synonyms.
        3.  Rank potential tools based on match relevance.
    *   **Phase 2: Input/Output Compatibility Check**
        1.  For each high-ranking tool from Phase 1:
            a.  Extract required input parameters (`input_parameters`) from its KB definition.
            b.  Compare with inputs provided by the user or available in the current context.
            c.  Check if data types are compatible or can be transformed.
            d.  Filter out tools with unmet mandatory input requirements.
        2.  Similarly, compare tool `output_parameters` with desired user outputs.
    *   **Phase 3: Constraint Verification**
        1.  Check `dependencies` (OS, libraries, other tools) against the current environment.
        2.  Verify `status` (prefer `active` tools over `experimental` or `deprecated` unless specified).
    *   **Phase 4: Recommendation/Clarification**
        1.  If one tool is a strong match: "I found a tool called `[tool_name]` that might be suitable. It [brief description]. Would you like to use it?"
        2.  If multiple tools are potential matches: "I found a few tools: `[tool1]`, `[tool2]`. `[Tool1]` does X, while `[Tool2]` does Y. Which one seems closer to your need?"
        3.  If no tool is a perfect match but some are close: "I don't have an exact match, but `[tool_name]` can do [partial function]. Could this be adapted?"
        4.  If no suitable tool: Proceed to Tool Creation Workflow (5.2).

*   **5.2. Tool Creation Workflow (Steps from requirements to definition):**
    *   _Agent's internal process if a new tool needs to be defined._
    1.  **Requirement Elicitation:** Execute User Query Templates (Section 4) to gather all necessary details (purpose, inputs, outputs, execution logic, dependencies).
    2.  **Schema Mapping:** Map gathered user requirements directly to the fields defined in the Knowledge Base Schema (Section 2).
        *   User says "It needs a file to read" -> `input_parameters: [{name: 'inputFile', type: 'file_path', required: true, ...}]`
        *   User says "It should be a Python script" -> `execution: {type: 'python_script', ...}`
    3.  **Identify Execution Type:** Determine if it's CLI, API, script-based from user description or by asking: "How will this tool be executed? Is it a command-line program, a script (Python, Bash, etc.), or does it call an API?"
    4.  **Select Template:** Choose the appropriate template from Section 3 (e.g., `Template for CLI Tools`).
    5.  **Populate Template:** Fill in the chosen template with the mapped schema information.
        *   If `execution.type` is `script`:
            *   Agent: "What is the name or path of the script?" (for `script_path`)
            *   Agent: "Are there specific command-line arguments this script expects, and how do they map to the inputs we defined?" (for `command_template` if arguments are complex, or to inform how the agent constructs the call)
        *   If `execution.type` is `api`:
            *   Agent: "What is the base URL for this API?"
            *   Agent: "What is the specific endpoint path?"
            *   Agent: "Which HTTP method should be used (GET, POST, etc.)?"
            *   Agent: "Does this API require authentication? If so, what type (API Key, OAuth, etc.) and what are the details?"
    6.  **Generate `tool_id`:** Create a unique `tool_id` (e.g., `user.custom_tool_timestamp`).
    7.  **Request User Review:** Present the generated tool definition (in the KB format) to the user for confirmation. "I've drafted the definition for your new tool. Please review it: [shows definition]. Does this look correct?"
    8.  **Store in KB:** Upon approval, save the new tool definition to the agent's local or a designated custom tool knowledge base.
    9.  **Offer to Test:** "Would you like to try running the new tool `[new_tool_id]` now?"

*   **5.3. Tool Configuration Logic (Adapting existing tools):**
    *   _Agent's process for modifying settings of an existing tool if it has `configuration_options`._
    1.  **Identify Configurable Tool:** User expresses a need that might be met by an existing tool with different settings (e.g., "Can `image_resizer_tool` output a PNG instead of JPG?").
    2.  **Check `configuration_options`:** Agent inspects the tool's definition in the KB for relevant `configuration_options` (e.g., `output_format`).
    3.  **Query User for Values:** If a relevant option exists: "The `image_resizer_tool` can be configured for different output formats. What format would you like (e.g., PNG, JPEG, GIF)?"
    4.  **Apply Configuration:** Agent internally notes the configuration change for the current task or session. This might involve:
        *   Temporarily overriding default values when executing the tool.
        *   If the KB allows for user-specific profiles, storing this preference.
        *   NOT modifying the base tool definition without explicit instruction and versioning.
    5.  **Inform User:** "Okay, I will configure `image_resizer_tool` to output as PNG for this task."
    6.  **If no direct configuration option:** "The `image_resizer_tool` doesn't directly support changing X. We might need to create a new tool or a wrapper script. Would you like to proceed with that?" (Links back to Tool Creation Workflow 5.2).

## 6. Validation and Testing Frameworks
_Protocols for agents to validate tool functionality and ensure reliability._

*   **6.1. Input Validation:**
    *   _Before executing a tool, the agent MUST validate inputs against the tool's `input_parameters` definition in the KB._
    *   **Checks to Perform:**
        *   **Required Fields:** Ensure all `required: true` parameters are present.
        *   **Data Types:** Verify if the provided input matches the defined `type` (e.g., integer, string, boolean). Attempt type coercion for minor mismatches if safe (e.g., "5" to 5).
        *   **Format:** If `format` is specified (e.g., regex for string, date format), validate against it.
        *   **Options:** If `options` are listed, ensure the input value is one of them.
        *   **Validation Rules:** For each rule in `validation_rules` (e.g., `minLength`, `maxValue`, `pattern`, custom rules like `fileExists`), execute the validation.
            *   Agent should have built-in handlers for common `rule_type`s.
            *   Custom rules might require specific agent logic or even calling a helper tool.
    *   **Failure Handling:** If validation fails, the agent should:
        *   NOT execute the tool.
        *   Inform the user about the specific validation error and which input was problematic (using `error_message` from `validation_rules` if available).
        *   Example: "Input 'port_number' must be between 1 and 65535, but you provided 0."
        *   Request corrected input.

*   **6.2. Output Verification:**
    *   _After a tool executes, the agent SHOULD verify the outputs against the tool's `output_parameters` definition if possible._
    *   **Checks to Perform:**
        *   **Presence:** Check if expected output names are present in the tool's result.
        *   **Data Types:** Roughly check if output types match (e.g., if `json_object` is expected, is the output parseable JSON?). Exact type validation might be complex for structured data.
        *   **Format:** If `format` is specified for an output, check if the output conforms.
    *   **Heuristics & Common Sense:**
        *   If an output `type` is `file_path`, check if the file exists.
        *   If an `exitCode` output is defined, a non-zero value usually indicates an error (though context matters).
    *   **Failure Handling:**
        *   If output seems incorrect or missing, flag it.
        *   Agent: "The tool `[tool_id]` ran, but the output `[output_name]` seems to be missing or in an unexpected format. Expected [expected type/format]."
        *   Consult Section 7 (Error Handling) for further steps.

*   **6.3. Automated Testing Scripts/Procedures (Agent Capability):**
    *   _For tools critical to agent operation or newly created tools, agents could be designed to run predefined test cases._
    *   **Test Case Definition (Hypothetical - could be part of a richer KB or separate system):**
        *   Associated with a `tool_id`.
        *   Includes:
            *   `test_case_id`
            *   `description`
            *   `sample_inputs` (conforming to `input_parameters`)
            *   `expected_outputs` (values or criteria for `output_parameters`)
            *   `expected_exit_code` (if applicable)
    *   **Execution by Agent:**
        1.  Agent retrieves test cases for a given tool.
        2.  Executes the tool with `sample_inputs`.
        3.  Compares actual outputs against `expected_outputs`.
        4.  Reports success/failure of test cases.
    *   **Triggering:** Can be triggered after tool creation, on agent startup for core tools, or periodically.

*   **6.4. Health Checks for Tools:**
    *   _For tools that depend on external services (APIs) or have specific environment needs._
    *   **Definition:** A `health_check` procedure could be an optional part of a tool's KB definition.
        *   Could be a simplified execution of the tool with non-destructive inputs.
        *   Example: For an API tool, a GET request to a status endpoint.
        *   Example: For a script tool, checking if its interpreter and dependencies are available.
    *   **Execution by Agent:**
        *   Periodically for critical tools.
        *   Before first use in a session if the tool is external.
        *   If a health check fails, the tool is marked as 'unavailable' or 'degraded', and the agent should inform the user or try an alternative.

## 7. Error Handling and Troubleshooting Automation
_Standardized error responses and automated recovery/suggestion mechanisms for agents._

*   **7.1. Common Error Codes and Meanings (Agent Interpreted):**
    *   _This section guides the agent on interpreting errors from tools, not just displaying raw errors to users._
    *   **Tool Execution Errors (General):**
        *   `TOOL_NOT_FOUND`: The specified `tool_id` does not exist in the KB.
            *   Agent Action: Verify `tool_id`, suggest alternatives, or offer to define it.
        *   `INPUT_VALIDATION_FAILED`: (As per 6.1)
            *   Agent Action: Report specific validation error to user.
        *   `EXECUTION_TIMEOUT`: Tool took too long to run.
            *   Agent Action: Inform user, ask if they want to retry with a longer timeout (if configurable).
        *   `PERMISSION_DENIED`: Agent lacks rights to execute the tool or access its resources.
            *   Agent Action: Inform user, may suggest admin intervention.
        *   `DEPENDENCY_MISSING`: A required library, tool, or environment variable is not available.
            *   Agent Action: Inform user. If an `install_command` is known for a library, offer to run it (with caution/confirmation).
    *   **CLI Tool Specific:**
        *   `NON_ZERO_EXIT_CODE`: The CLI command exited with an error status.
            *   Agent Action: Report exit code and any stderr output. Check tool's documentation (if linked in KB) for meaning.
    *   **API Tool Specific:**
        *   `HTTP_ERROR_4xx` (e.g., 400, 401, 403, 404): Client-side errors.
            *   Agent Action: Interpret common codes (401: auth error, 404: not found) and guide user.
        *   `HTTP_ERROR_5xx` (e.g., 500, 503): Server-side errors.
            *   Agent Action: Inform user, suggest retrying later.
        *   `NETWORK_ERROR`: Could not connect to API.
            *   Agent Action: Check network connectivity, suggest retry.
    *   **Script Tool Specific:**
        *   `SCRIPT_EXECUTION_ERROR`: Script ran but failed (e.g., Python exception).
            *   Agent Action: Report error output (stderr, exception trace).

*   **7.2. Automated Troubleshooting Steps (Agent Logic):**
    *   **Retry Mechanisms:**
        *   For transient errors (network issues, some 5xx API errors), agent can automatically retry 1-2 times with a short delay.
        *   Make retry attempts configurable (e.g., via `configuration_options` of the calling tool/agent).
    *   **Dependency Checks:**
        *   If `DEPENDENCY_MISSING` for a library with an `install_command`:
            1.  Agent: "Tool `[tool_id]` requires library `[library_name]`. I can try to install it using: `[install_command]`. Allow?"
            2.  If allowed and successful, retry tool.
    *   **Authentication Refresh (for APIs):**
        *   If an API call returns 401 (Unauthorized) and a token refresh mechanism is defined (e.g., OAuth2 refresh token flow), attempt refresh and retry the original call.
    *   **Fallback to Simpler Tool/Method:**
        *   If a complex tool fails, and a simpler or more robust alternative exists that achieves part of the goal, the agent could suggest it.
    *   **Parameter Adjustment:**
        *   If a tool fails with specific parameters, but is known to work with others, the agent might suggest trying a "safer" set of parameters for diagnosis.

*   **7.3. Escalation Paths for Unresolved Issues:**
    *   **Inform User Clearly:** "I've tried [steps taken] to run `[tool_id]`, but it's still failing with the error: `[concise error summary]`. I'm unable to resolve this automatically."
    *   **Provide Debug Information:** "Here's some information that might be helpful for troubleshooting: [relevant inputs, tool version, portion of error log if concise]."
    *   **Suggest Manual Intervention / Alternative Approaches:**
        *   "You might need to check [specific configuration, file permissions, API key validity] manually."
        *   "Would you like to try a different tool or approach to achieve your goal?"
        *   "Should I log this issue for a human developer/administrator to review?" (If agent has such capability).
    *   **Do NOT repeatedly try the same failing action without new information or user guidance.**

## 8. Integration Patterns
_Guidelines on how this knowledge base integrates with broader AI agent systems._

*   **8.1. API for KB Access (Conceptual):**
    *   _How other parts of an AI system or other agents might query this Knowledge Base._
    *   **Endpoints (Illustrative):**
        *   `GET /tools`: List all available tools (summary view).
        *   `GET /tools/{tool_id}`: Get detailed definition of a specific tool.
        *   `POST /tools/query`: Semantic search for tools based on natural language description or input/output requirements.
        *   `POST /tools`: Add a new tool definition (with proper validation against schema).
        *   `PUT /tools/{tool_id}`: Update an existing tool definition.
    *   **Authentication:** Access to modification endpoints should be restricted.

*   **8.2. Data Exchange Formats:**
    *   The primary format for tool definitions within this KB is **Markdown with YAML front matter** as demonstrated in Section 3 templates.
    *   For API access (8.1), requests and responses would typically be **JSON**, mirroring the structure of the YAML front matter.
    *   Agents should be capable of parsing the Markdown/YAML.

*   **8.3. Event Handling (Conceptual):**
    *   _How an agent system might react to changes in the KB._
    *   `KB_TOOL_ADDED`: Event triggered when a new tool is successfully added.
        *   Potential Action: Agent re-indexes its available tools.
    *   `KB_TOOL_UPDATED`: Event triggered when an existing tool definition changes.
        *   Potential Action: Agent clears any cached version of this tool; may need to re-validate workflows using it.
    *   `KB_TOOL_DEPRECATED`: Event triggered when a tool `status` changes to `deprecated`.
        *   Potential Action: Agent flags workflows using this tool, suggests alternatives to users.
    *   `KB_SCHEMA_UPDATED`: Event triggered if the KB schema itself (Section 2.7) changes.
        *   Potential Action: May require significant agent adaptation or data migration.

## 9. Extensibility Guidelines
_Instructions on how to add new tool types, update schemas, or modify existing definitions._

*   **9.1. Schema Extension Process:**
    1.  **Identify Need:** Determine why the current schema (Section 2) is insufficient.
    2.  **Propose Changes:** Define new fields or modifications to existing ones. Consider impact on existing tools and agent parsing logic.
    3.  **Update Schema Version:** Increment `schema_version` in Section 2.7.
    4.  **Document Changes:** Add details to `changelog_pointer` (or an inline changelog).
    5.  **Update Agent Logic:** The agent's parsing and interpretation logic MUST be updated to support the new schema version.
    6.  **Tool Migration (if necessary):** Existing tool definitions may need to be updated to conform to the new schema.

*   **9.2. Adding New Tool Templates:**
    1.  If a new category of tool execution (beyond CLI, API, script) becomes common, a new template can be added in Section 3.
    2.  The template should conform to the current KB schema.
    3.  The agent's "Tool Creation Workflow" (5.2) might need to be updated to recognize and use this new template.

*   **9.3. Version Control for KB Updates:**
    *   All changes to `Agent_Tools_Knowledge_Base.md` (and any associated tool script files) MUST be managed under a version control system (e.g., Git).
    *   **Branching Strategy:** Use feature branches for adding new tools or significant schema changes.
    *   **Commit Messages:** Should be clear and describe the changes made (e.g., "ADD: New tool `image_enhancer_v2`", "FIX: Corrected input parameter type for `text_analyzer`", "UPDATE: Schema v1.1.0 - added `tags` field to Core Attributes").
    *   **Review Process:** Ideally, changes should be reviewed before merging into a main/production version of the KB, especially for shared agent systems.

## 10. Appendix (Optional)
_Additional resources, glossaries, or examples._
