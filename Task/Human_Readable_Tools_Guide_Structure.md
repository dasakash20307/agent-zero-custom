# Human-Readable Tools and Instruments Guide

## Table of Contents
1.  [Introduction](#10-introduction)
    1.1. [What are Tools and Instruments?](#11-what-are-tools-and-instruments)
    1.2. [Target Audience](#12-target-audience)
    1.3. [How to Use This Guide](#13-how-to-use-this-guide)
2.  [Getting Started](#20-getting-started)
    2.1. [Prerequisites](#21-prerequisites)
    2.2. [Installation and Setup](#22-installation-and-setup)
    2.3. [Core Concepts](#23-core-concepts)
3.  [Creating Your First Tool](#30-creating-your-first-tool)
    3.1. [Tool Definition](#31-tool-definition)
    3.2. [Step-by-Step: Simple Tool Example](#32-step-by-step-simple-tool-example)
    3.3. [Best Practices for Tool Creation](#33-best-practices-for-tool-creation)
4.  [Tool Configuration](#40-tool-configuration)
    4.1. [Configuration Parameters](#41-configuration-parameters)
    4.2. [How to Configure Tools](#42-how-to-configure-tools)
    4.3. [Environment Variables and Secrets Management](#43-environment-variables-and-secrets-management)
5.  [Enabling and Using Tools with AI Agents](#50-enabling-and-using-tools-with-ai-agents)
    5.1. [How Agents Discover and Select Tools](#51-how-agents-discover-and-select-tools)
    5.2. [Invoking Tools](#52-invoking-tools)
    5.3. [Handling Tool Outputs and Errors](#53-handling-tool-outputs-and-errors)
    5.4. [User Persona Examples](#54-user-persona-examples)
6.  [Tool Reference](#60-tool-reference)
    6.1. [`ls`](#61-ls)
    6.2. [`read_files`](#62-read_files)
    6.3. [`view_text_website`](#63-view_text_website)
    6.4. [`set_plan`](#64-set_plan)
    6.5. [`plan_step_complete`](#65-plan_step_complete)
    6.6. [`run_subtask`](#66-run_subtask)
    6.7. [`cancel_subtask`](#67-cancel_subtask)
    6.8. [`message_user`](#68-message_user)
    6.9. [`request_user_input`](#69-request_user_input)
    6.10. [`record_user_approval_for_plan`](#610-record_user_approval_for_plan)
    6.11. [`submit`](#611-submit)
    6.12. [Other Tools (from previous content if applicable)]
        *   `create_file_with_block`
        *   `overwrite_file_with_block`
        *   `delete_file`
        *   `rename_file`
        *   `grep`
        *   `replace_with_git_merge_diff`
        *   `run_in_bash_session`
        *   `reset_all`
        *   `restore_file`
        *   `submit_subtask_report`
7.  [Advanced Tool Development](#70-advanced-tool-development)
    7.1. [Creating Complex Tools](#71-creating-complex-tools)
    7.2. [Asynchronous Tools](#72-asynchronous-tools)
    7.3. [Tool Versioning and Maintenance](#73-tool-versioning-and-maintenance)
    7.4. [Security Considerations for Tools](#74-security-considerations-for-tools)
8.  [Examples of Different Tool Types](#80-examples-of-different-tool-types)
    8.1. [Data Processing Tools](#81-data-processing-tools)
    8.2. [API-Interfacing Tools](#82-api-interfacing-tools)
    8.3. [Hardware-Interacting Tools](#83-hardware-interacting-tools)
    8.4. [Custom Tool Showcase Template](#84-custom-tool-showcase-template)
9.  [Troubleshooting](#90-troubleshooting)
    9.1. [Common Issues and Solutions](#91-common-issues-and-solutions)
    9.2. [Debugging Tools](#92-debugging-tools)
    9.3. [Getting Help](#93-getting-help)
10. [Integration with README.md](#100-integration-with-readmemd)
    10.1. [Formatting Guidelines](#101-formatting-guidelines)
    10.2. [Cross-Referencing](#102-cross-referencing)
11. [Contributing to Tools](#110-contributing-to-tools)
    11.1. [Guidelines for Contribution](#111-guidelines-for-contribution)
    11.2. [Code Style and Documentation Standards](#112-code-style-and-documentation-standards)
12. [Appendix A: Glossary of Terms](#120-appendix-a-glossary-of-terms)
13. [Appendix B: Tool Manifest File Specification](#130-appendix-b-tool-manifest-file-specification)

---

## 1.0 Introduction
Content guidelines: Explain the fundamental role of tools and instruments in extending AI agent capabilities. Define what they are in the context of this specific repository/project.

### 1.1 What are Tools and Instruments?
Content guidelines:
*   Define "Tool" and "Instrument" clearly.
*   Explain their purpose: enabling agents to interact with environments, data, or APIs.
*   Highlight benefits: enhanced problem-solving, access to real-time information, ability to perform actions.

### 1.2 Target Audience
Content guidelines:
*   Specify who this guide is for (e.g., developers, advanced users, AI researchers).
*   Address different skill levels:
    *   **Beginner:** How to use existing tools.
    *   **Advanced:** How to create and configure new tools.

### 1.3 How to Use This Guide
Content guidelines:
*   Explain the guide's structure.
*   Suggest reading paths for different user goals (e.g., "If you want to create a new tool, start with Section 3").
*   Point to the Table of Contents for quick navigation.

## 2.0 Getting Started
Content guidelines: Provide essential information for users to begin working with tools.

### 2.1 Prerequisites
Content guidelines:
*   **System Requirements:** OS, memory, etc. (if specific).
*   **Software Dependencies:** Programming languages (e.g., Python version), libraries, Docker.
*   **Prior Knowledge:** Familiarity with AI concepts, command-line interfaces, programming (as applicable).

### 2.2 Installation and Setup
Content guidelines:
*   Instructions for installing any necessary software or configuring the environment for tool usage/development.
*   Link to general repository installation guide if prerequisites cover this.
*   Specific setup steps for the tool system itself (e.g., initializing a tool directory, environment variables).

### 2.3 Core Concepts
Content guidelines:
*   **Agent-Tool Interaction:** How the AI agent discovers, selects, and executes tools.
*   **Tool Lifecycle:** Registration, enabling/disabling, updating, deprecation.
*   **Tool Manifest/Definition File:** Briefly introduce its role (details in Section 3.1 and Appendix B).
*   **Permissions and Security:** Overview of how tool usage is controlled (if applicable).

## 3.0 Creating Your First Tool
Content guidelines: A beginner-friendly tutorial on creating a basic tool.

### 3.1 Tool Definition
Content guidelines:
*   Explain the structure of a tool (e.g., script file, manifest file).
*   **Manifest File (`tool.json` or similar):**
    *   Purpose: Declares tool properties, parameters, and entry points.
    *   Key fields: name, description, parameters (name, type, description, required), output type. (Refer to Appendix B for full spec).
*   Required components: e.g., main script, dependencies file.

### 3.2 Step-by-Step: Simple Tool Example
Content guidelines: Walk through creating a very simple tool (e.g., a "calculator" that adds two numbers, or a "date echo" tool).
*   **3.2.1 Defining Inputs and Outputs:** How to specify what the tool accepts and returns in its manifest.
*   **3.2.2 Writing the Tool Logic:** Show the actual code for the simple tool in the relevant language (e.g., Python).
    *   Include how to parse inputs and return outputs.
*   **3.2.3 Tool Registration/Enabling:** How the agent becomes aware of the new tool.
    *   Placement in a specific directory?
    *   A command to run?
    *   Updating a central registry file?

### 3.3 Best Practices for Tool Creation
Content guidelines:
*   Keep tools focused on a single task.
*   Write clear descriptions and parameter explanations.
*   Handle errors gracefully.
*   Include examples of usage.
*   Consider security implications from the start.
*   Make tools idempotent where possible.

## 4.0 Tool Configuration
Content guidelines: Explain how users can customize tool behavior.

### 4.1 Configuration Parameters
Content guidelines:
*   Distinguish between general (system-wide) and tool-specific configurations.
*   Examples: API keys, default paths, behavior flags.
*   Where these parameters are defined (e.g., in the tool's manifest, a separate config file).

### 4.2 How to Configure Tools
Content guidelines:
*   **Methods:**
    *   Using a User Interface (if available).
    *   Editing configuration files (e.g., JSON, YAML).
    *   Via API calls to the agent or tool management system.
    *   Environment variables.
*   Provide examples for each method.

### 4.3 Environment Variables and Secrets Management for Tools
Content guidelines:
*   Best practices for handling sensitive information like API keys (e.g., using `.env` files, platform-provided secrets management).
*   How tools should access these securely.

## 5.0 Enabling and Using Tools with AI Agents
Content guidelines: Focus on the agent's perspective and user interaction.

### 5.1 How Agents Discover and Select Tools
Content guidelines:
*   Explain the mechanism (e.g., scanning a directory, reading a registry).
*   How the agent decides which tool is appropriate for a given task (e.g., based on tool descriptions, user prompts).

### 5.2 Invoking Tools
Content guidelines:
*   **Syntax:** How the agent (or user through the agent) calls a tool.
    *   Command format, function call signature.
*   **Parameters:** How to pass arguments, data types, optional vs. required.
*   **Expected Responses:** Synchronous vs. asynchronous, data format of results.

### 5.3 Handling Tool Outputs and Errors in Agent Logic
Content guidelines:
*   How the agent consumes the data returned by a tool.
*   Common error types and how the agent should react or report them.
*   Retry mechanisms.

### 5.4 User Persona Examples
Content guidelines:
*   **5.4.1 Beginner: Using a Pre-built Tool**
    *   Scenario: A user wants the agent to summarize a webpage.
    *   Steps: How they would instruct the agent, how the agent uses a `view_text_website` and a hypothetical `summarize_text` tool.
*   **5.4.2 Advanced: Dynamically Enabling/Disabling Tools for a Session**
    *   Scenario: A developer wants to restrict the agent to a specific set of tools for a particular task.
    *   Steps: Commands or configurations to manage available tools at runtime.

## 6.0 Tool Reference
Content guidelines: Detailed documentation for each available tool. This section will integrate the tools already listed.

### 6.1 `ls`
*   **Description:** Lists files and directories in the repository.
*   **Usage:** `ls(directory_path: str = "") -> list[str]`
*   **Parameters:**
    *   `directory_path` (optional): The path to the directory to list. Defaults to the repository root.
*   **Returns:** A list of file and directory names.
*   **Examples:**
    *   `ls()`
    *   `ls(directory_path="Task/")`
*   **Content Guidelines:** Provide clear instructions and examples for each tool.

### 6.2 `read_files`
*   **Description:** Reads the content of specified files.
*   **Usage:** `read_files(filepaths: list[str]) -> list[str]`
*   **Parameters:**
    *   `filepaths`: A list of paths to the files to read.
*   **Returns:** A list of strings, where each string is the content of a file.
*   **Examples:** `read_files(["Task/Task1.txt", "README.md"])`
*   **Content Guidelines:** Explain potential errors like FileNotFoundError.

### 6.3 `view_text_website`
*   **Description:** Fetches the content of a website as plain text.
*   **Usage:** `view_text_website(url: str) -> str`
*   **Parameters:**
    *   `url`: The URL of the website to fetch.
*   **Returns:** The plain text content of the website.
*   **Examples:** `view_text_website(url="https://www.example.com")`
*   **Content Guidelines:** Mention internet access dependency.

### 6.4 `set_plan`
*   **Description:** Sets or updates the agent's current plan.
*   **Usage:** `set_plan(plan: str) -> None`
*   **Parameters:**
    *   `plan`: A string describing the plan, typically in markdown.
*   **Returns:** None.
*   **Examples:** `set_plan("1. Step A\n2. Step B")`
*   **Content Guidelines:** Explain when and how this tool is used by the agent.

### 6.5 `plan_step_complete`
*   **Description:** Marks the current step in the agent's plan as complete.
*   **Usage:** `plan_step_complete(message: str) -> None`
*   **Parameters:**
    *   `message`: A summary of what was done to complete the step.
*   **Returns:** None.
*   **Examples:** `plan_step_complete("Finished implementing feature X.")`
*   **Content Guidelines:** Explain its role in agent's task execution flow.

### 6.6 `run_subtask`
*   **Description:** Instructs the agent to execute a subtask.
*   **Usage:** `run_subtask(subtask: str) -> None`
*   **Parameters:**
    *   `subtask`: A detailed description of the subtask to be performed.
*   **Returns:** None. (The result comes asynchronously via a subtask report).
*   **Examples:** `run_subtask("Create a file named 'test.txt' with content 'Hello World'.")`
*   **Content Guidelines:** Explain subtask execution and reporting.

### 6.7 `cancel_subtask`
*   **Description:** Cancels an ongoing subtask.
*   **Usage:** `cancel_subtask() -> None`
*   **Parameters:** None.
*   **Returns:** None.
*   **Examples:** `cancel_subtask()`
*   **Content Guidelines:** Explain when this might be necessary.

### 6.8 `message_user`
*   **Description:** Sends a message to the user.
*   **Usage:** `message_user(message: str, continue_working: bool) -> None`
*   **Parameters:**
    *   `message`: The message to send.
    *   `continue_working`: Boolean indicating if the agent has more work after this message.
*   **Returns:** None.
*   **Examples:** `message_user("I have updated the file as requested.", continue_working=True)`
*   **Content Guidelines:** Differentiate from `request_user_input`.

### 6.9 `request_user_input`
*   **Description:** Asks the user for input and waits for a response.
*   **Usage:** `request_user_input(message: str) -> None`
*   **Parameters:**
    *   `message`: The question or prompt for the user.
*   **Returns:** None. (Input comes via user interaction).
*   **Examples:** `request_user_input("Do you want to proceed with deleting the file?")`
*   **Content Guidelines:** Explain this is for blocking requests.

### 6.10 `record_user_approval_for_plan`
*   **Description:** Records that the user has approved the current plan.
*   **Usage:** `record_user_approval_for_plan() -> None`
*   **Parameters:** None.
*   **Returns:** None.
*   **Examples:** `record_user_approval_for_plan()`
*   **Content Guidelines:** Explain its role in the planning process.

### 6.11 `submit`
*   **Description:** Commits the current changes to the repository.
*   **Usage:** `submit(branch_name: str, commit_message: str) -> None`
*   **Parameters:**
    *   `branch_name`: The name for the new git branch.
    *   `commit_message`: The commit message.
*   **Returns:** None.
*   **Examples:** `submit(branch_name="feature-xyz", commit_message="Implemented feature XYZ.")`
*   **Content Guidelines:** Mention commit message conventions.

### 6.12 Other Tools
Content guidelines: For each tool listed from the previous file content (e.g., `create_file_with_block`, `run_in_bash_session`), provide:
    *   **Description:** What the tool does.
    *   **Usage:** Syntax, including parameters (clearly define if it's a special DSL like `create_file_with_block` or a Python-like call).
    *   **Parameters:** Detailed explanation of each parameter.
    *   **Returns:** What the tool outputs or if it's `None`.
    *   **Examples:** Clear, practical examples.
    *   **Notes:** Any special considerations, error handling, or best practices.

    *   **`create_file_with_block`**
        *   Description: Creates a new file with the specified content using a special block format.
        *   Usage:
            ```
            create_file_with_block
            <filepath>
            <file_content_block>
            ```
        *   Parameters:
            *   `filepath`: The full path, including filename, where the new file will be created.
            *   `file_content_block`: The content to write to the new file. This starts on the line after the filepath and continues until the end of the tool call.
        *   Returns: Typically a confirmation message or error status from the subtask report.
        *   Examples:
            ```
            create_file_with_block
            Task/new_tool_readme.md
            # My New Tool
            This tool does X, Y, and Z.
            ```
        *   Notes: Useful for creating multi-line text files. Ensure the agent correctly escapes content if needed.

    *   **`overwrite_file_with_block`** (similar structure to `create_file_with_block`)
    *   **`delete_file(filepath: str)`**
    *   **`rename_file(filepath: str, new_filepath: str)`**
    *   **`grep(pattern: str, directory: str = ".", options: str = "")`** (assuming more params might be useful)
    *   **`replace_with_git_merge_diff`** (explain the diff format carefully)
    *   **`run_in_bash_session`** (explain session persistence, how to see output)
    *   **`reset_all()`**
    *   **`restore_file(filepath: str)`**
    *   **`submit_subtask_report(summary: str, succeeded: bool)`** (This is likely an agent-internal tool, clarify if it's for end-user documentation)


## 7.0 Advanced Tool Development
Content guidelines: For users looking to build more sophisticated tools.

### 7.1 Creating Complex Tools
Content guidelines:
*   **Multi-step Tools:** Tools that perform a sequence of actions or call other tools.
*   **Tools with External Dependencies:** Managing dependencies (e.g., Python libraries, external binaries).
*   **Stateful Tools:** Tools that maintain state across multiple invocations (use with caution, explain implications).

### 7.2 Asynchronous Tools
Content guidelines:
*   Defining and handling tools that don't return immediately (e.g., long-running processes).
*   How the agent manages async operations and callbacks.

### 7.3 Tool Versioning and Maintenance
Content guidelines:
*   Strategies for versioning tools (e.g., v1, v2) as they evolve.
*   Handling backward compatibility.
*   Best practices for updating and deprecating tools.

### 7.4 Security Considerations for Tools
Content guidelines:
*   **Permissions:** How to define what a tool can access/do (e.g., filesystem, network).
*   **Input Sanitization:** Preventing injection attacks or other vulnerabilities.
*   **Sandboxing:** Running tools in restricted environments (if applicable).
*   Principle of least privilege.

## 8.0 Examples of Different Tool Types
Content guidelines: Showcase the versatility of tools with concrete examples. For each, provide a brief description, potential use case, and key implementation considerations.

### 8.1 Data Processing Tools
Content guidelines:
*   Example: A tool that converts CSV files to JSON.
*   Use Case: Standardizing data formats for agent consumption.
*   Implementation: File I/O, data parsing libraries.

### 8.2 API-Interfacing Tools
Content guidelines:
*   Example: A tool that fetches weather information from an external API.
*   Use Case: Providing real-time data to the agent.
*   Implementation: HTTP requests, API key management, error handling for network issues.

### 8.3 Hardware-Interacting Tools (If applicable)
Content guidelines:
*   Example: A tool that controls a smart light (if the system supports IoT).
*   Use Case: Enabling agents to interact with the physical world.
*   Implementation: Specific SDKs or protocols for hardware communication.

### 8.4 Custom Tool Showcase Template
Content guidelines:
*   Provide a markdown template that users can copy to document their own custom tools if they wish to share them or for their own team's reference.
*   Template should include: Tool Name, Description, Usage, Parameters, Examples, Author, Version.

## 9.0 Troubleshooting
Content guidelines: Help users resolve common problems.

### 9.1 Common Issues and Solutions
Content guidelines:
*   Tool not found/recognized.
*   Incorrect parameters passed.
*   Permissions errors.
*   Tool crashes or hangs.
*   Unexpected output.

### 9.2 Debugging Tools
Content guidelines:
*   Logging: Where to find tool execution logs.
*   Verbose modes or debug flags for tools or the agent.
*   Any built-in debugging utilities.

### 9.3 Getting Help
Content guidelines:
*   Links to community forums, issue trackers.
*   Contact information for support (if applicable).
*   How to provide good bug reports (e.g., logs, steps to reproduce).

## 10.0 Integration with README.md
Content guidelines: Explain how this guide or parts of it will be referenced or integrated into the main project README.

### 10.1 Formatting Guidelines
Content guidelines:
*   Markdown standards to be used for consistency.
*   Use of callouts, code blocks, tables.
*   How to ensure the documentation is rendered correctly in the README.

### 10.2 Cross-Referencing
Content guidelines:
*   How to link from the main README to specific sections in this guide.
*   How to link between sections within this guide.
*   Linking to other relevant documentation (e.g., general API docs, contribution guide).

## 11.0 Contributing to Tools
Content guidelines: Encourage community contributions.

### 11.1 Guidelines for Contribution
Content guidelines:
*   Process for proposing new tools or improvements to existing ones.
*   Forking the repository, creating pull requests.
*   Code review process.

### 11.2 Code Style and Documentation Standards for Contributions
Content guidelines:
*   Required coding style (e.g., PEP 8 for Python).
*   Mandatory documentation for new tools (e.g., must include a section in this guide or a standalone README for the tool).
*   Testing requirements for new tools.

## 12.0 Appendix A: Glossary of Terms
Content guidelines: Define key terms used throughout the guide for clarity. Examples: Agent, Instrument, Manifest, API Key, Idempotent, etc.

## 13.0 Appendix B: Tool Manifest File Specification
Content guidelines: Provide a detailed specification of the `tool.json` (or equivalent) file.
*   List all possible fields.
*   For each field: name, data type, whether it's mandatory or optional, description, and example.
*   E.g., `name: string (required) - The unique name of the tool.`
*   `description: string (required) - A human-readable description of what the tool does.`
*   `parameters: array (optional) - A list of parameter objects.`
    *   `name: string (required)`
    *   `type: string (required) - e.g., string, integer, boolean, list, object`
    *   `description: string (required)`
    *   `required: boolean (optional, default: false)`
    *   `default: any (optional)`
    *   `enum: array (optional) - List of allowed values.`
*   `output_type: string (optional) - Expected data type of the tool's output.`
*   `entry_point: string (required) - e.g., script_name.py:function_name or command_to_execute.`
