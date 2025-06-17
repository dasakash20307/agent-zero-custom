import argparse
import json
import asyncio
import logging
import sys
from pathlib import Path
from dataclasses import asdict, is_dataclass # For converting dataclass instances to dict

# Assuming mcp is a library available in the environment
# These imports might need adjustment based on the actual mcp library structure
try:
    from mcp import ToolDefinition, ToolParameter, ToolInputSchema, run_stdio_server_async
except ImportError:
    # Mocking for environments where mcp might not be installed
    # This allows the script to be syntactically correct and testable in isolation
    logging.warning("MCP library not found. Using mock definitions. Functionality will be limited.")
    class ToolParameter:
        def __init__(self, name: str, type: str, description: str, required: bool = False):
            self.name = name
            self.type = type
            self.description = description
            self.required = required

    class ToolInputSchema:
        def __init__(self, parameters: list[ToolParameter]):
            self.parameters = parameters

    class ToolDefinition:
        def __init__(self, name: str, description: str, input_schema: ToolInputSchema, execute_async):
            self.name = name
            self.description = description
            self.input_schema = input_schema
            self.execute_async = execute_async

    async def run_stdio_server_async(tools: list, name: str, version: str):
        logging.info(f"Mock MCP Server '{name}' v{version} started with {len(tools)} tools.")
        # In a real server, this would loop indefinitely, processing requests
        # For this mock, it will just log and exit.
        await asyncio.sleep(1) # Keep alive for a moment
        logging.info(f"Mock MCP Server '{name}' v{version} stopping.")

    # Mock asdict if dataclasses module isn't fully available (e.g. very old Python or minimal env)
    try:
        from dataclasses import asdict as _asdict, is_dataclass as _is_dataclass
        asdict = _asdict
        is_dataclass = _is_dataclass
    except ImportError:
        logging.warning("dataclasses.asdict not found. Using mock version. Dataclass conversion will be basic.")
        def asdict(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return {"error": "asdict mock failed, object has no __dict__"}
        def is_dataclass(obj):
            return hasattr(obj, '__dataclass_fields__')


# Assuming the instruments directory is structured as described
# Adjust these imports if the actual Saadhan instrument structure differs
try:
    from instruments.custom.saadhan.orchestrator import Orchestrator, WorkspaceConfig
    # Import other managers or dataclasses if they are directly used by tools
    # e.g., from instruments.custom.saadhan.file_manager import FileManager
    from instruments.custom.saadhan.data_model import Template, Project # Assuming these exist for type hinting
except ImportError: # Catches if 'instruments' or submodules are not found
    logging.warning(f"Could not import Saadhan specific models (Template, Project). Type hints may be affected but runtime conversion will be attempted.")
    # Define dummy classes for type hinting if not available
    class Template: pass
    class Project: pass


# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("SaadhanMCPServer")

async def main_async():
    parser = argparse.ArgumentParser(description="Saadhan MCP Server")
    parser.add_argument(
        "--workspace-root",
        type=str,
        default="saadhan_workspace",
        help="Root directory for the Saadhan workspace (default: saadhan_workspace in current dir)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )
    args = parser.parse_args()

    # Apply log level from arguments
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.getLogger().setLevel(numeric_level) # Set root logger level
    logger.info(f"Log level set to {args.log_level.upper()}")

    workspace_root_path = Path(args.workspace_root).resolve()
    logger.info(f"Saadhan Workspace Root: {workspace_root_path}")

    try:
        # Ensure workspace directory exists
        workspace_root_path.mkdir(parents=True, exist_ok=True)
        workspace_config = WorkspaceConfig(workspace_root=workspace_root_path)
        orchestrator = Orchestrator(config=workspace_config)
        logger.info("Orchestrator instantiated.")
    except ImportError: # Specifically catch ImportErrors if Saadhan instruments are not found
        logger.error("Failed to import or initialize Saadhan Orchestrator. Saadhan tools will not be available.")
        orchestrator = None
    except Exception as e:
        logger.error(f"Failed to initialize Orchestrator: {e}")
        # Depending on mcp behavior, we might want to exit or let the server start with no tools
        orchestrator = None # Ensure orchestrator is None if init fails

    tools = []

    if orchestrator: # Only define tools if orchestrator is available
        # Tool 1: saadhan.file_manager.read_file
        async def execute_read_file(inputs: dict):
            file_path_str = inputs.get("file_path")
            if not file_path_str:
                return {"error": "Missing required parameter: file_path"}

            try:
                # Ensure orchestrator.file_manager is available and has read_file
                if not hasattr(orchestrator, 'file_manager') or not callable(getattr(orchestrator.file_manager, 'read_file', None)):
                    logger.error("Orchestrator's file_manager or read_file method is not available.")
                    return {"error": "File reading functionality is currently unavailable."}

                # The file_path is relative to the workspace root.
                # The Orchestrator/FileManager should handle resolving this.
                content = await orchestrator.file_manager.read_file(Path(file_path_str))

                # Ensure content is JSON serializable (string is fine)
                if not isinstance(content, str):
                    logger.warning(f"File content for {file_path_str} is not a string, attempting conversion.")
                    try:
                        content = str(content) # Basic conversion
                    except Exception as conv_e:
                        logger.error(f"Could not convert file content to string for {file_path_str}: {conv_e}")
                        return {"error": f"Failed to serialize file content for {file_path_str}."}

                logger.info(f"Successfully read file: {file_path_str}")
                return {"content": content}
            except FileNotFoundError:
                logger.warning(f"File not found: {file_path_str}")
                return {"error": f"File not found: {file_path_str}"}
            except Exception as e:
                logger.error(f"Error reading file {file_path_str}: {e}")
                return {"error": str(e)}

        read_file_tool = ToolDefinition(
            name="saadhan.file_manager.read_file",
            description="Reads the content of a specified file from the Saadhan workspace.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="file_path", type="string", description="The path to the file relative to the workspace root.", required=True)
            ]),
            execute_async=execute_read_file
        )
        tools.append(read_file_tool)

        # Tool 2: saadhan.user_pattern_analyzer.log_interaction
        async def execute_log_interaction(inputs: dict):
            user_id = inputs.get("user_id")
            task_type = inputs.get("task_type")
            task_content = inputs.get("task_content")

            if not all([user_id, task_type, task_content]):
                missing_params = [
                    p for p, v in {"user_id": user_id, "task_type": task_type, "task_content": task_content}.items() if not v
                ]
                return {"error": f"Missing required parameters: {', '.join(missing_params)}"}

            try:
                # Assuming orchestrator.pattern_analyzer.analyze_task exists
            try:
                # Ensure orchestrator.pattern_analyzer is available and has analyze_task
                if not hasattr(orchestrator, 'pattern_analyzer') or not callable(getattr(orchestrator.pattern_analyzer, 'analyze_task', None)):
                    logger.error("Orchestrator's pattern_analyzer or analyze_task method is not available.")
                    return {"error": "User pattern analysis functionality is currently unavailable."}

                result = await orchestrator.pattern_analyzer.analyze_task(
                    user_id=user_id, task_type=task_type, task_content=task_content
                )

                # Convert result to JSON-serializable format if it's a complex object
                # For now, assuming it returns a dict or a simple type
                if isinstance(result, (Path,)): # Example of handling non-serializable types
                    result = str(result)
                elif is_dataclass(result):
                    result = asdict(result)
                elif hasattr(result, 'to_dict'): # Fallback for other custom objects
                     result = result.to_dict()

                logger.info(f"User interaction logged: User '{user_id}', Type '{task_type}'.")
                return {"status": "success", "details": result}
            except Exception as e:
                logger.error(f"Error logging interaction for user {user_id}: {e}")
                return {"error": str(e)}

        log_interaction_tool = ToolDefinition(
            name="saadhan.user_pattern_analyzer.log_interaction",
            description="Logs user interaction for pattern analysis and context improvement. Should be called after most user turns.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="user_id", type="string", description="Unique identifier for the user.", required=True),
                ToolParameter(name="task_type", type="string", description="Type of task or interaction (e.g., 'code_generation', 'file_edit').", required=True),
                ToolParameter(name="task_content", type="string", description="Content related to the task (e.g., prompt, code snippet).", required=True),
            ]),
            execute_async=execute_log_interaction
        )
        tools.append(log_interaction_tool)

        # Tool 3: saadhan.template_manager.create_template
        async def execute_create_template(inputs: dict):
            template_data = inputs.get("template_data")
            if not template_data or not isinstance(template_data, dict):
                return {"error": "Missing or invalid type for required parameter: template_data (must be an object/dictionary)"}

            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'create_template', None)):
                    logger.error("Orchestrator's template_manager or create_template method is not available.")
                    return {"error": "Template creation functionality is currently unavailable."}

                # Assuming create_template returns a Template dataclass instance
                new_template = await orchestrator.template_manager.create_template(template_data)

                if not is_dataclass(new_template) and not isinstance(new_template, Template): # Check against imported/mocked Template
                    logger.warning(f"create_template returned an unexpected type: {type(new_template)}. Expected a dataclass.")
                    # Attempt to serialize anyway if it's not a known non-serializable type
                    if isinstance(new_template, (Path,)):
                         return {"error": "create_template returned a non-serializable type."}


                logger.info(f"Successfully created template: {template_data.get('name', 'Unknown name')}")
                # Convert dataclass to dict for JSON serialization
                return {"status": "success", "template": asdict(new_template) if is_dataclass(new_template) else new_template}
            except Exception as e:
                logger.error(f"Error creating template with data {template_data.get('name', 'Unknown name')}: {e}", exc_info=True)
                return {"error": str(e)}

        create_template_tool = ToolDefinition(
            name="saadhan.template_manager.create_template",
            description="Creates a new Saadhan template.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(
                    name="template_data",
                    type="object",
                    description="Dictionary containing template data (e.g., name, type, content, category, author, description, variables, metadata).",
                    required=True
                )
            ]),
            execute_async=execute_create_template
        )
        tools.append(create_template_tool)

        # Tool 4: saadhan.project_manager.create_project
        async def execute_create_project(inputs: dict):
            title = inputs.get("title")
            description = inputs.get("description")
            start_date = inputs.get("start_date")
            end_date = inputs.get("end_date")
            metadata = inputs.get("metadata", {}) # Optional, default to empty dict

            if not all([title, description, start_date, end_date]):
                missing_params = [
                    p for p, v in {
                        "title": title, "description": description,
                        "start_date": start_date, "end_date": end_date
                    }.items() if not v
                ]
                return {"error": f"Missing required parameters: {', '.join(missing_params)}"}

            if not isinstance(metadata, dict):
                 return {"error": "Invalid type for optional parameter: metadata (must be an object/dictionary if provided)"}

            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'create_project', None)):
                    logger.error("Orchestrator's project_manager or create_project method is not available.")
                    return {"error": "Project creation functionality is currently unavailable."}

                # Assuming create_project returns a Project dataclass instance
                new_project = await orchestrator.project_manager.create_project(
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    metadata=metadata
                )

                if not is_dataclass(new_project) and not isinstance(new_project, Project): # Check against imported/mocked Project
                    logger.warning(f"create_project returned an unexpected type: {type(new_project)}. Expected a dataclass.")
                    if isinstance(new_project, (Path,)):
                         return {"error": "create_project returned a non-serializable type."}

                logger.info(f"Successfully created project: {title}")
                # Convert dataclass to dict for JSON serialization
                return {"status": "success", "project": asdict(new_project) if is_dataclass(new_project) else new_project}
            except Exception as e:
                logger.error(f"Error creating project {title}: {e}", exc_info=True)
                return {"error": str(e)}

        create_project_tool = ToolDefinition(
            name="saadhan.project_manager.create_project",
            description="Creates a new Saadhan project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="title", type="string", description="Title of the project.", required=True),
                ToolParameter(name="description", type="string", description="Description of the project.", required=True),
                ToolParameter(name="start_date", type="string", description="Start date of the project (ISO format).", required=True),
                ToolParameter(name="end_date", type="string", description="End date of the project (ISO format).", required=True),
                ToolParameter(name="metadata", type="object", description="Optional dictionary for additional project metadata.", required=False)
            ]),
            execute_async=execute_create_project
        )
        tools.append(create_project_tool)

        # --- TemplateManager Tools ---

        # A.1: saadhan.template_manager.get_template
        async def execute_get_template(inputs: dict):
            template_id = inputs.get("template_id")
            if not template_id:
                return {"error": "Missing required parameter: template_id"}
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'get_template', None)):
                    logger.error("Orchestrator's template_manager or get_template method is not available.")
                    return {"error": "Template retrieval functionality is currently unavailable."}

                template_obj = await orchestrator.template_manager.get_template(template_id)
                if template_obj is None:
                    return {"error": f"Template with ID '{template_id}' not found."}

                logger.info(f"Successfully retrieved template: {template_id}")
                return {"status": "success", "template": asdict(template_obj) if is_dataclass(template_obj) else template_obj}
            except Exception as e:
                logger.error(f"Error retrieving template {template_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_template_tool = ToolDefinition(
            name="saadhan.template_manager.get_template",
            description="Retrieves a specific Saadhan template by its ID.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_id", type="string", description="ID of the template to retrieve.", required=True)
            ]),
            execute_async=execute_get_template
        )
        tools.append(get_template_tool)

        # A.2: saadhan.template_manager.update_template
        async def execute_update_template(inputs: dict):
            template_id = inputs.get("template_id")
            updates = inputs.get("updates")
            if not template_id:
                return {"error": "Missing required parameter: template_id"}
            if not updates or not isinstance(updates, dict):
                return {"error": "Missing or invalid type for required parameter: updates (must be an object/dictionary)"}
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'update_template', None)):
                    logger.error("Orchestrator's template_manager or update_template method is not available.")
                    return {"error": "Template update functionality is currently unavailable."}

                updated_template = await orchestrator.template_manager.update_template(template_id, updates)
                if updated_template is None:
                     return {"error": f"Failed to update template ID '{template_id}', or template not found."}

                logger.info(f"Successfully updated template: {template_id}")
                return {"status": "success", "template": asdict(updated_template) if is_dataclass(updated_template) else updated_template}
            except Exception as e:
                logger.error(f"Error updating template {template_id}: {e}", exc_info=True)
                return {"error": str(e)}

        update_template_tool = ToolDefinition(
            name="saadhan.template_manager.update_template",
            description="Updates an existing Saadhan template. Creates a new version if content changes.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_id", type="string", description="ID of the template to update.", required=True),
                ToolParameter(name="updates", type="object", description="Dictionary of fields to update.", required=True)
            ]),
            execute_async=execute_update_template
        )
        tools.append(update_template_tool)

        # A.3: saadhan.template_manager.list_templates
        async def execute_list_templates(inputs: dict):
            template_type = inputs.get("template_type") # Optional
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'list_templates', None)):
                    logger.error("Orchestrator's template_manager or list_templates method is not available.")
                    return {"error": "Template listing functionality is currently unavailable."}

                templates_list = await orchestrator.template_manager.list_templates(template_type=template_type)

                logger.info(f"Successfully listed templates (type: {template_type or 'any'}). Found {len(templates_list)} templates.")
                return {
                    "status": "success",
                    "templates": [asdict(t) if is_dataclass(t) else t for t in templates_list]
                }
            except Exception as e:
                logger.error(f"Error listing templates (type: {template_type or 'any'}): {e}", exc_info=True)
                return {"error": str(e)}

        list_templates_tool = ToolDefinition(
            name="saadhan.template_manager.list_templates",
            description="Lists all available Saadhan templates, optionally filtered by type.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_type", type="string", description="Optional type to filter templates.", required=False)
            ]),
            execute_async=execute_list_templates
        )
        tools.append(list_templates_tool)

        # A.4: saadhan.template_manager.delete_template
        async def execute_delete_template(inputs: dict):
            template_id = inputs.get("template_id")
            if not template_id:
                return {"error": "Missing required parameter: template_id"}
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'delete_template', None)):
                    logger.error("Orchestrator's template_manager or delete_template method is not available.")
                    return {"error": "Template deletion functionality is currently unavailable."}

                # Assuming delete_template returns boolean or raises error
                success = await orchestrator.template_manager.delete_template(template_id)
                if success:
                    logger.info(f"Successfully deleted template: {template_id}")
                    return {"status": "success", "message": f"Template {template_id} deleted successfully."}
                else:
                    logger.warning(f"Failed to delete template {template_id} (method returned false or template not found).")
                    return {"error": f"Failed to delete template {template_id}, or template not found."}
            except Exception as e:
                logger.error(f"Error deleting template {template_id}: {e}", exc_info=True)
                return {"error": str(e)}

        delete_template_tool = ToolDefinition(
            name="saadhan.template_manager.delete_template",
            description="Deletes a Saadhan template and its version history.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_id", type="string", description="ID of the template to delete.", required=True)
            ]),
            execute_async=execute_delete_template
        )
        tools.append(delete_template_tool)

        # A.5: saadhan.template_manager.get_template_versions
        async def execute_get_template_versions(inputs: dict):
            template_id = inputs.get("template_id")
            if not template_id:
                return {"error": "Missing required parameter: template_id"}
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'get_template_versions', None)):
                    logger.error("Orchestrator's template_manager or get_template_versions method is not available.")
                    return {"error": "Template version retrieval functionality is currently unavailable."}

                versions = await orchestrator.template_manager.get_template_versions(template_id)
                logger.info(f"Successfully retrieved versions for template: {template_id}")
                # Assuming versions is already a list of dicts or simple serializable types
                return {"status": "success", "versions": versions}
            except Exception as e:
                logger.error(f"Error retrieving versions for template {template_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_template_versions_tool = ToolDefinition(
            name="saadhan.template_manager.get_template_versions",
            description="Retrieves the version history of a specific Saadhan template.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_id", type="string", description="ID of the template.", required=True)
            ]),
            execute_async=execute_get_template_versions
        )
        tools.append(get_template_versions_tool)

        # A.6: saadhan.template_manager.render_template
        async def execute_render_template(inputs: dict):
            template_id = inputs.get("template_id")
            variables = inputs.get("variables")
            if not template_id:
                return {"error": "Missing required parameter: template_id"}
            if not variables or not isinstance(variables, dict):
                return {"error": "Missing or invalid type for required parameter: variables (must be an object/dictionary)"}
            try:
                if not hasattr(orchestrator, 'template_manager') or \
                   not callable(getattr(orchestrator.template_manager, 'render_template', None)):
                    logger.error("Orchestrator's template_manager or render_template method is not available.")
                    return {"error": "Template rendering functionality is currently unavailable."}

                rendered_content = await orchestrator.template_manager.render_template(template_id, variables)
                if not isinstance(rendered_content, str):
                    logger.warning(f"render_template for {template_id} did not return a string. Type: {type(rendered_content)}")
                    # Attempt to convert, or handle as error if conversion is risky
                    try:
                        rendered_content = str(rendered_content)
                    except Exception:
                        return {"error": "Rendered content is not a string and could not be converted."}

                logger.info(f"Successfully rendered template: {template_id}")
                return {"status": "success", "rendered_content": rendered_content}
            except Exception as e:
                logger.error(f"Error rendering template {template_id}: {e}", exc_info=True)
                return {"error": str(e)}

        render_template_tool = ToolDefinition(
            name="saadhan.template_manager.render_template",
            description="Renders a Saadhan template with provided variables.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="template_id", type="string", description="ID of the template to render.", required=True),
                ToolParameter(name="variables", type="object", description="Dictionary of variables for rendering.", required=True)
            ]),
            execute_async=execute_render_template
        )
        tools.append(render_template_tool)

        # --- ProjectManager Tools ---

        # B.1: saadhan.project_manager.update_project
        async def execute_update_project(inputs: dict):
            project_id = inputs.get("project_id")
            updates = inputs.get("updates")
            if not project_id:
                return {"error": "Missing required parameter: project_id"}
            if not updates or not isinstance(updates, dict):
                return {"error": "Missing or invalid type for required parameter: updates (must be an object/dictionary)"}
            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'update_project', None)):
                    logger.error("Orchestrator's project_manager or update_project method is not available.")
                    return {"error": "Project update functionality is currently unavailable."}

                updated_project = await orchestrator.project_manager.update_project(project_id, updates)
                if updated_project is None:
                    return {"error": f"Failed to update project ID '{project_id}', or project not found."}

                logger.info(f"Successfully updated project: {project_id}")
                return {"status": "success", "project": asdict(updated_project) if is_dataclass(updated_project) else updated_project}
            except Exception as e:
                logger.error(f"Error updating project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        update_project_tool = ToolDefinition(
            name="saadhan.project_manager.update_project",
            description="Updates an existing Saadhan project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project to update.", required=True),
                ToolParameter(name="updates", type="object", description="Dictionary of fields to update.", required=True)
            ]),
            execute_async=execute_update_project
        )
        tools.append(update_project_tool)

        # B.2: saadhan.project_manager.get_project
        async def execute_get_project(inputs: dict):
            project_id = inputs.get("project_id")
            if not project_id:
                return {"error": "Missing required parameter: project_id"}
            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'get_project', None)):
                    logger.error("Orchestrator's project_manager or get_project method is not available.")
                    return {"error": "Project retrieval functionality is currently unavailable."}

                project_obj = await orchestrator.project_manager.get_project(project_id)
                if project_obj is None:
                    return {"error": f"Project with ID '{project_id}' not found."}

                logger.info(f"Successfully retrieved project: {project_id}")
                return {"status": "success", "project": asdict(project_obj) if is_dataclass(project_obj) else project_obj}
            except Exception as e:
                logger.error(f"Error retrieving project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_project_tool = ToolDefinition(
            name="saadhan.project_manager.get_project",
            description="Retrieves details of a specific Saadhan project by its ID.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project to retrieve.", required=True)
            ]),
            execute_async=execute_get_project
        )
        tools.append(get_project_tool)

        # B.3: saadhan.project_manager.list_projects
        async def execute_list_projects(inputs: dict):
            status = inputs.get("status") # Optional
            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'list_projects', None)):
                    logger.error("Orchestrator's project_manager or list_projects method is not available.")
                    return {"error": "Project listing functionality is currently unavailable."}

                projects_list = await orchestrator.project_manager.list_projects(status=status)

                logger.info(f"Successfully listed projects (status: {status or 'any'}). Found {len(projects_list)} projects.")
                return {
                    "status": "success",
                    "projects": [asdict(p) if is_dataclass(p) else p for p in projects_list]
                }
            except Exception as e:
                logger.error(f"Error listing projects (status: {status or 'any'}): {e}", exc_info=True)
                return {"error": str(e)}

        list_projects_tool = ToolDefinition(
            name="saadhan.project_manager.list_projects",
            description="Lists all Saadhan projects, optionally filtered by status.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="status", type="string", description="Optional status to filter projects.", required=False)
            ]),
            execute_async=execute_list_projects
        )
        tools.append(list_projects_tool)

        # B.4: saadhan.project_manager.add_activity
        async def execute_add_activity(inputs: dict):
            project_id = inputs.get("project_id")
            title = inputs.get("title")
            description = inputs.get("description")
            start_date = inputs.get("start_date")
            end_date = inputs.get("end_date")
            dependencies = inputs.get("dependencies", []) # Optional, default to empty list

            required_params = {
                "project_id": project_id, "title": title, "description": description,
                "start_date": start_date, "end_date": end_date
            }
            missing = [k for k, v in required_params.items() if not v]
            if missing:
                return {"error": f"Missing required parameters: {', '.join(missing)}"}

            if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
                return {"error": "Invalid type for optional parameter: dependencies (must be an array of strings if provided)"}

            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'add_activity', None)):
                    logger.error("Orchestrator's project_manager or add_activity method is not available.")
                    return {"error": "Activity addition functionality is currently unavailable."}

                activity_obj = await orchestrator.project_manager.add_activity(
                    project_id=project_id, title=title, description=description,
                    start_date=start_date, end_date=end_date, dependencies=dependencies
                )
                logger.info(f"Successfully added activity '{title}' to project {project_id}")
                return {"status": "success", "activity": asdict(activity_obj) if is_dataclass(activity_obj) else activity_obj}
            except Exception as e:
                logger.error(f"Error adding activity to project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        add_activity_tool = ToolDefinition(
            name="saadhan.project_manager.add_activity",
            description="Adds a new activity to a specified Saadhan project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project.", required=True),
                ToolParameter(name="title", type="string", description="Title of the activity.", required=True),
                ToolParameter(name="description", type="string", description="Description of the activity.", required=True),
                ToolParameter(name="start_date", type="string", description="Start date of the activity (ISO format).", required=True),
                ToolParameter(name="end_date", type="string", description="End date of the activity (ISO format).", required=True),
                ToolParameter(name="dependencies", type="array", item_type="string", description="Optional list of activity IDs this activity depends on.", required=False)
            ]),
            execute_async=execute_add_activity
        )
        tools.append(add_activity_tool)

        # B.5: saadhan.project_manager.add_beneficiary
        async def execute_add_beneficiary(inputs: dict):
            project_id = inputs.get("project_id")
            name = inputs.get("name")
            beneficiary_type = inputs.get("type") # MCP 'type' vs Python 'type'
            contact = inputs.get("contact")
            benefits = inputs.get("benefits")

            required_params = {
                "project_id": project_id, "name": name, "type": beneficiary_type,
                "contact": contact, "benefits": benefits
            }
            missing = [k for k, v in required_params.items() if not v]
            if missing:
                return {"error": f"Missing required parameters: {', '.join(missing)}"}

            if not isinstance(benefits, list) or not all(isinstance(item, str) for item in benefits):
                return {"error": "Invalid type for required parameter: benefits (must be an array of strings)"}

            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'add_beneficiary', None)):
                    logger.error("Orchestrator's project_manager or add_beneficiary method is not available.")
                    return {"error": "Beneficiary addition functionality is currently unavailable."}

                beneficiary_obj = await orchestrator.project_manager.add_beneficiary(
                    project_id=project_id, name=name, type=beneficiary_type,
                    contact=contact, benefits=benefits
                )
                logger.info(f"Successfully added beneficiary '{name}' to project {project_id}")
                return {"status": "success", "beneficiary": asdict(beneficiary_obj) if is_dataclass(beneficiary_obj) else beneficiary_obj}
            except Exception as e:
                logger.error(f"Error adding beneficiary to project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        add_beneficiary_tool = ToolDefinition(
            name="saadhan.project_manager.add_beneficiary",
            description="Adds a beneficiary to a specified Saadhan project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project.", required=True),
                ToolParameter(name="name", type="string", description="Name of the beneficiary.", required=True),
                ToolParameter(name="type", type="string", description="Type of beneficiary (e.g., individual, community).", required=True),
                ToolParameter(name="contact", type="string", description="Contact information for the beneficiary.", required=True),
                ToolParameter(name="benefits", type="array", item_type="string", description="List of benefits for the beneficiary.", required=True)
            ]),
            execute_async=execute_add_beneficiary
        )
        tools.append(add_beneficiary_tool)

        # B.6: saadhan.project_manager.update_progress
        async def execute_update_progress(inputs: dict):
            project_id = inputs.get("project_id")
            activity_id = inputs.get("activity_id") # Optional
            progress = inputs.get("progress")

            if not project_id:
                return {"error": "Missing required parameter: project_id"}
            if progress is None: # progress can be 0, so check for None
                return {"error": "Missing required parameter: progress"}
            if not isinstance(progress, (int, float)):
                return {"error": "Invalid type for progress, must be a number."}

            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'update_progress', None)):
                    logger.error("Orchestrator's project_manager or update_progress method is not available.")
                    return {"error": "Progress update functionality is currently unavailable."}

                # Assuming update_progress returns the updated progress value or a status dict
                result = await orchestrator.project_manager.update_progress(
                    project_id=project_id, activity_id=activity_id, progress=progress
                )
                logger.info(f"Successfully updated progress for project {project_id} (Activity: {activity_id or 'overall'}) to {progress}")
                # The result could be just the progress, or a more complex object.
                # If it's a simple value, wrap it. If it's an object, try asdict.
                if isinstance(result, (int, float, str, bool)):
                    return {"status": "success", "progress_details": result}
                else:
                    return {"status": "success", "progress_details": asdict(result) if is_dataclass(result) else result}

            except Exception as e:
                logger.error(f"Error updating progress for project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        update_progress_tool = ToolDefinition(
            name="saadhan.project_manager.update_progress",
            description="Updates the progress of a Saadhan project or a specific activity.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project.", required=True),
                ToolParameter(name="activity_id", type="string", description="Optional ID of the activity to update progress for. If null, updates overall project progress.", required=False),
                ToolParameter(name="progress", type="number", description="Progress value (e.g., percentage 0-100).", required=True)
            ]),
            execute_async=execute_update_progress
        )
        tools.append(update_progress_tool)

        # B.7: saadhan.project_manager.generate_report
        async def execute_generate_report(inputs: dict):
            project_id = inputs.get("project_id")
            if not project_id:
                return {"error": "Missing required parameter: project_id"}

            try:
                if not hasattr(orchestrator, 'project_manager') or \
                   not callable(getattr(orchestrator.project_manager, 'generate_report', None)):
                    logger.error("Orchestrator's project_manager or generate_report method is not available.")
                    return {"error": "Report generation functionality is currently unavailable."}

                report_data = await orchestrator.project_manager.generate_report(project_id=project_id)

                logger.info(f"Successfully generated report for project {project_id}")
                # Report data could be a complex dict, or a string (e.g. pre-formatted text/html)
                if isinstance(report_data, str):
                    return {"status": "success", "report_content": report_data, "type": "string"}
                elif isinstance(report_data, dict):
                     return {"status": "success", "report_data": report_data, "type": "object"}
                else: # Attempt conversion if dataclass
                    return {"status": "success", "report_data": asdict(report_data) if is_dataclass(report_data) else report_data, "type": "object_fallback"}
            except Exception as e:
                logger.error(f"Error generating report for project {project_id}: {e}", exc_info=True)
                return {"error": str(e)}

        generate_report_tool = ToolDefinition(
            name="saadhan.project_manager.generate_report",
            description="Generates a status report for a Saadhan project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="project_id", type="string", description="ID of the project for which to generate a report.", required=True)
            ]),
            execute_async=execute_generate_report
        )
        tools.append(generate_report_tool)

        # --- ResearchManager Tools ---

        # A.1: saadhan.research_manager.create_research
        async def execute_create_research(inputs: dict):
            title = inputs.get("title")
            description = inputs.get("description")
            objectives = inputs.get("objectives")
            methodology = inputs.get("methodology")

            if not all([title, description, objectives, methodology]):
                return {"error": "Missing one or more required parameters: title, description, objectives, methodology"}
            if not isinstance(objectives, list) or not all(isinstance(obj, str) for obj in objectives):
                return {"error": "Invalid type for objectives: must be an array of strings."}

            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'create_research', None)):
                    logger.error("Orchestrator's research_manager or create_research method is not available.")
                    return {"error": "Research creation functionality is currently unavailable."}

                research_obj = await orchestrator.research_manager.create_research(
                    title=title, description=description, objectives=objectives, methodology=methodology
                )
                logger.info(f"Successfully created research: {title}")
                return {"status": "success", "research": asdict(research_obj) if is_dataclass(research_obj) else research_obj}
            except Exception as e:
                logger.error(f"Error creating research '{title}': {e}", exc_info=True)
                return {"error": str(e)}

        create_research_tool = ToolDefinition(
            name="saadhan.research_manager.create_research",
            description="Creates a new research project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="title", type="string", description="Title of the research.", required=True),
                ToolParameter(name="description", type="string", description="Description of the research.", required=True),
                ToolParameter(name="objectives", type="array", item_type="string", description="List of research objectives.", required=True),
                ToolParameter(name="methodology", type="string", description="Methodology of the research.", required=True),
            ]),
            execute_async=execute_create_research
        )
        tools.append(create_research_tool)

        # A.2: saadhan.research_manager.add_source
        async def execute_add_source(inputs: dict):
            research_id = inputs.get("research_id")
            title = inputs.get("title")
            url = inputs.get("url")
            source_type = inputs.get("source_type")
            description = inputs.get("description")

            if not all([research_id, title, url, source_type, description]):
                return {"error": "Missing one or more required parameters: research_id, title, url, source_type, description"}

            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'add_source', None)):
                    logger.error("Orchestrator's research_manager or add_source method is not available.")
                    return {"error": "Adding research source functionality is currently unavailable."}

                source_obj = await orchestrator.research_manager.add_source(
                    research_id=research_id, title=title, url=url, source_type=source_type, description=description
                )
                logger.info(f"Successfully added source '{title}' to research {research_id}")
                return {"status": "success", "source": asdict(source_obj) if is_dataclass(source_obj) else source_obj}
            except Exception as e:
                logger.error(f"Error adding source to research {research_id}: {e}", exc_info=True)
                return {"error": str(e)}

        add_source_tool = ToolDefinition(
            name="saadhan.research_manager.add_source",
            description="Adds a new source to a research project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research project.", required=True),
                ToolParameter(name="title", type="string", description="Title of the source.", required=True),
                ToolParameter(name="url", type="string", description="URL or identifier of the source.", required=True),
                ToolParameter(name="source_type", type="string", description="Type of the source (e.g., article, book).", required=True),
                ToolParameter(name="description", type="string", description="Brief description of the source.", required=True),
            ]),
            execute_async=execute_add_source
        )
        tools.append(add_source_tool)

        # A.3: saadhan.research_manager.add_finding
        async def execute_add_finding(inputs: dict):
            research_id = inputs.get("research_id")
            title = inputs.get("title")
            description = inputs.get("description")
            evidence = inputs.get("evidence") # Assuming string or simple dict

            if not all([research_id, title, description, evidence]):
                 return {"error": "Missing one or more required parameters: research_id, title, description, evidence"}

            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'add_finding', None)):
                    logger.error("Orchestrator's research_manager or add_finding method is not available.")
                    return {"error": "Adding research finding functionality is currently unavailable."}

                finding_obj = await orchestrator.research_manager.add_finding(
                    research_id=research_id, title=title, description=description, evidence=evidence
                )
                logger.info(f"Successfully added finding '{title}' to research {research_id}")
                return {"status": "success", "finding": asdict(finding_obj) if is_dataclass(finding_obj) else finding_obj}
            except Exception as e:
                logger.error(f"Error adding finding to research {research_id}: {e}", exc_info=True)
                return {"error": str(e)}

        add_finding_tool = ToolDefinition(
            name="saadhan.research_manager.add_finding",
            description="Adds a new finding to a research project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research project.", required=True),
                ToolParameter(name="title", type="string", description="Title of the finding.", required=True),
                ToolParameter(name="description", type="string", description="Detailed description of the finding.", required=True),
                ToolParameter(name="evidence", type="string", description="Evidence supporting the finding (e.g., text, link, data snippet).", required=True), # Could be 'object' if more complex
            ]),
            execute_async=execute_add_finding
        )
        tools.append(add_finding_tool)

        # A.4: saadhan.research_manager.update_research
        async def execute_update_research(inputs: dict):
            research_id = inputs.get("research_id")
            updates = inputs.get("updates")
            if not research_id or not updates or not isinstance(updates, dict):
                return {"error": "Missing research_id or updates, or updates is not an object."}

            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'update_research', None)):
                    logger.error("Orchestrator's research_manager or update_research method is not available.")
                    return {"error": "Research update functionality is currently unavailable."}

                # Note: Original update_research calls self.version_control.save_version(...)
                # This might require orchestrator.file_manager to have save_version or a proper VersionControl component.
                # Assuming this is handled within the orchestrator's method.
                updated_research = await orchestrator.research_manager.update_research(research_id, updates)
                if updated_research is None:
                    return {"error": f"Failed to update research ID '{research_id}', or research not found."}

                logger.info(f"Successfully updated research: {research_id}")
                return {"status": "success", "research": asdict(updated_research) if is_dataclass(updated_research) else updated_research}
            except Exception as e:
                logger.error(f"Error updating research {research_id}: {e}", exc_info=True)
                # Consider more specific error for version control issues if detectable
                return {"error": str(e)}

        update_research_tool = ToolDefinition(
            name="saadhan.research_manager.update_research",
            description="Updates an existing research project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research project to update.", required=True),
                ToolParameter(name="updates", type="object", description="Dictionary of fields to update.", required=True)
            ]),
            execute_async=execute_update_research
        )
        tools.append(update_research_tool)

        # A.5: saadhan.research_manager.get_research
        async def execute_get_research(inputs: dict):
            research_id = inputs.get("research_id")
            if not research_id:
                return {"error": "Missing required parameter: research_id"}
            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'get_research', None)):
                    logger.error("Orchestrator's research_manager or get_research method is not available.")
                    return {"error": "Research retrieval functionality is currently unavailable."}

                research_obj = await orchestrator.research_manager.get_research(research_id)
                if research_obj is None:
                    return {"error": f"Research with ID '{research_id}' not found."}

                logger.info(f"Successfully retrieved research: {research_id}")
                return {"status": "success", "research": asdict(research_obj) if is_dataclass(research_obj) else research_obj}
            except Exception as e:
                logger.error(f"Error retrieving research {research_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_research_tool = ToolDefinition(
            name="saadhan.research_manager.get_research",
            description="Retrieves a specific research project by its ID.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research to retrieve.", required=True)
            ]),
            execute_async=execute_get_research
        )
        tools.append(get_research_tool)

        # A.6: saadhan.research_manager.list_research
        async def execute_list_research(inputs: dict):
            status = inputs.get("status") # Optional
            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'list_research', None)):
                    logger.error("Orchestrator's research_manager or list_research method is not available.")
                    return {"error": "Research listing functionality is currently unavailable."}

                # Note: Original list_research loads from JSON files. Pathing consistency is key.
                # Assuming this is handled by the orchestrator's method.
                research_list = await orchestrator.research_manager.list_research(status=status)

                logger.info(f"Successfully listed research (status: {status or 'all'}). Found {len(research_list)} items.")
                return {
                    "status": "success",
                    "research_items": [asdict(r) if is_dataclass(r) else r for r in research_list]
                }
            except Exception as e:
                logger.error(f"Error listing research (status: {status or 'all'}): {e}", exc_info=True)
                return {"error": str(e)}

        list_research_tool = ToolDefinition(
            name="saadhan.research_manager.list_research",
            description="Lists all research projects, optionally filtered by status.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="status", type="string", description="Optional status to filter research projects.", required=False)
            ]),
            execute_async=execute_list_research
        )
        tools.append(list_research_tool)

        # A.7: saadhan.research_manager.generate_report (research)
        async def execute_generate_research_report(inputs: dict): # Renamed to avoid conflict with project report
            research_id = inputs.get("research_id")
            if not research_id:
                return {"error": "Missing required parameter: research_id"}
            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'generate_report', None)):
                    logger.error("Orchestrator's research_manager or generate_report method is not available.")
                    return {"error": "Research report generation functionality is currently unavailable."}

                report_data = await orchestrator.research_manager.generate_report(research_id=research_id)
                logger.info(f"Successfully generated report for research {research_id}")
                return {"status": "success", "report": asdict(report_data) if is_dataclass(report_data) else report_data}
            except Exception as e:
                logger.error(f"Error generating report for research {research_id}: {e}", exc_info=True)
                return {"error": str(e)}

        generate_research_report_tool = ToolDefinition(
            name="saadhan.research_manager.generate_report",
            description="Generates a summary report for a specific research project.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research to generate a report for.", required=True)
            ]),
            execute_async=execute_generate_research_report
        )
        tools.append(generate_research_report_tool)

        # A.8: saadhan.research_manager.analyze_sources
        async def execute_analyze_sources(inputs: dict):
            research_id = inputs.get("research_id")
            if not research_id:
                return {"error": "Missing required parameter: research_id"}
            try:
                if not hasattr(orchestrator, 'research_manager') or \
                   not callable(getattr(orchestrator.research_manager, 'analyze_sources', None)):
                    logger.error("Orchestrator's research_manager or analyze_sources method is not available.")
                    return {"error": "Research source analysis functionality is currently unavailable."}

                # Note: Original analyze_sources might have source['authors'] KeyError.
                # The method should internally handle if 'authors' is missing or provide default.
                analysis_result = await orchestrator.research_manager.analyze_sources(research_id)
                logger.info(f"Successfully analyzed sources for research: {research_id}")
                return {"status": "success", "analysis": asdict(analysis_result) if is_dataclass(analysis_result) else analysis_result}
            except KeyError as ke: # Specific catch for potential known issues
                logger.error(f"KeyError during source analysis for research {research_id}: {ke}. This might be an issue with source data structure (e.g. missing 'authors' key).", exc_info=True)
                return {"error": f"Data error during source analysis: {ke}. Check source data structure."}
            except Exception as e:
                logger.error(f"Error analyzing sources for research {research_id}: {e}", exc_info=True)
                return {"error": str(e)}

        analyze_sources_tool = ToolDefinition(
            name="saadhan.research_manager.analyze_sources",
            description="Analyzes sources associated with a research project (e.g., for common themes, author analysis).",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="research_id", type="string", description="ID of the research project.", required=True)
            ]),
            execute_async=execute_analyze_sources
        )
        tools.append(analyze_sources_tool)

        # --- IdentityManager Tools ---

        # B.1: saadhan.identity_manager.add_employee
        async def execute_add_employee(inputs: dict):
            name = inputs.get("name")
            designation = inputs.get("designation")
            department = inputs.get("department")
            if not all([name, designation, department]):
                return {"error": "Missing one or more required parameters: name, designation, department"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'add_employee', None)):
                    logger.error("Orchestrator's identity_manager or add_employee method is not available.")
                    return {"error": "Employee addition functionality is currently unavailable."}

                employee_obj = await orchestrator.identity_manager.add_employee(name, designation, department)
                logger.info(f"Successfully added employee: {name}")
                return {"status": "success", "employee": asdict(employee_obj) if is_dataclass(employee_obj) else employee_obj}
            except Exception as e:
                logger.error(f"Error adding employee {name}: {e}", exc_info=True)
                return {"error": str(e)}

        add_employee_tool = ToolDefinition(
            name="saadhan.identity_manager.add_employee",
            description="Adds a new employee to the system.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="name", type="string", description="Full name of the employee.", required=True),
                ToolParameter(name="designation", type="string", description="Designation of the employee.", required=True),
                ToolParameter(name="department", type="string", description="Department of the employee.", required=True),
            ]),
            execute_async=execute_add_employee
        )
        tools.append(add_employee_tool)

        # B.2: saadhan.identity_manager.add_user
        async def execute_add_user(inputs: dict):
            name = inputs.get("name")
            if not name:
                return {"error": "Missing required parameter: name"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'add_user', None)):
                    logger.error("Orchestrator's identity_manager or add_user method is not available.")
                    return {"error": "User addition functionality is currently unavailable."}

                user_obj = await orchestrator.identity_manager.add_user(name)
                logger.info(f"Successfully added user: {name}")
                return {"status": "success", "user": asdict(user_obj) if is_dataclass(user_obj) else user_obj}
            except Exception as e:
                logger.error(f"Error adding user {name}: {e}", exc_info=True)
                return {"error": str(e)}

        add_user_tool = ToolDefinition(
            name="saadhan.identity_manager.add_user",
            description="Adds a new general user to the system (non-employee).",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="name", type="string", description="Name of the user.", required=True)
            ]),
            execute_async=execute_add_user
        )
        tools.append(add_user_tool)

        # B.3: saadhan.identity_manager.update_employee_interaction_pattern
        async def execute_update_employee_interaction_pattern(inputs: dict):
            employee_id = inputs.get("employee_id")
            pattern = inputs.get("pattern") # Assuming pattern is a dict or complex object
            if not employee_id or pattern is None: # pattern could be an empty dict
                return {"error": "Missing required parameters: employee_id, pattern"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'update_interaction_pattern', None)): # Original method name
                    logger.error("Orchestrator's identity_manager or update_interaction_pattern method is not available.")
                    return {"error": "Employee interaction pattern update functionality is currently unavailable."}

                # Assuming update_interaction_pattern takes (user_id, pattern_data, is_employee=True)
                # Or a more specific method exists for employees. Sticking to prompt's implication.
                success = await orchestrator.identity_manager.update_interaction_pattern(employee_id, pattern, is_employee=True) # Assuming is_employee flag
                if success:
                    logger.info(f"Successfully updated interaction pattern for employee {employee_id}")
                    return {"status": "success", "message": "Interaction pattern updated."}
                else:
                    logger.warning(f"Failed to update interaction pattern for employee {employee_id}")
                    return {"error": "Failed to update interaction pattern."}
            except Exception as e:
                logger.error(f"Error updating interaction pattern for employee {employee_id}: {e}", exc_info=True)
                return {"error": str(e)}

        update_employee_interaction_pattern_tool = ToolDefinition(
            name="saadhan.identity_manager.update_employee_interaction_pattern",
            description="Updates the interaction pattern for an employee.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="employee_id", type="string", description="ID of the employee.", required=True),
                ToolParameter(name="pattern", type="object", description="The interaction pattern data (dictionary/object).", required=True),
            ]),
            execute_async=execute_update_employee_interaction_pattern
        )
        tools.append(update_employee_interaction_pattern_tool)

        # B.4: saadhan.identity_manager.update_user_interaction_history
        async def execute_update_user_interaction_history(inputs: dict):
            user_id = inputs.get("user_id")
            interaction_type = inputs.get("interaction_type")
            content = inputs.get("content")
            if not all([user_id, interaction_type, content]):
                return {"error": "Missing required parameters: user_id, interaction_type, content"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'update_user_interaction', None)): # Original method name
                    logger.error("Orchestrator's identity_manager or update_user_interaction method is not available.")
                    return {"error": "User interaction history update functionality is currently unavailable."}

                success = await orchestrator.identity_manager.update_user_interaction(user_id, interaction_type, content)
                if success:
                    logger.info(f"Successfully updated interaction history for user {user_id}")
                    return {"status": "success", "message": "Interaction history updated."}
                else:
                    logger.warning(f"Failed to update interaction history for user {user_id}")
                    return {"error": "Failed to update interaction history."}
            except Exception as e:
                logger.error(f"Error updating interaction history for user {user_id}: {e}", exc_info=True)
                return {"error": str(e)}

        update_user_interaction_history_tool = ToolDefinition(
            name="saadhan.identity_manager.update_user_interaction_history",
            description="Updates the interaction history for a general user.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="user_id", type="string", description="ID of the user.", required=True),
                ToolParameter(name="interaction_type", type="string", description="Type of interaction (e.g., 'query', 'feedback').", required=True),
                ToolParameter(name="content", type="string", description="Content of the interaction.", required=True),
            ]),
            execute_async=execute_update_user_interaction_history
        )
        tools.append(update_user_interaction_history_tool)

        # B.5: saadhan.identity_manager.get_employee_greeting
        async def execute_get_employee_greeting(inputs: dict):
            employee_id = inputs.get("employee_id")
            if not employee_id:
                return {"error": "Missing required parameter: employee_id"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'get_greeting', None)): # Original method name
                    logger.error("Orchestrator's identity_manager or get_greeting method is not available.")
                    return {"error": "Greeting retrieval functionality is currently unavailable."}

                # Assuming get_greeting takes user_id and is_employee flag
                greeting = await orchestrator.identity_manager.get_greeting(employee_id, is_employee=True)
                logger.info(f"Retrieved greeting for employee {employee_id}")
                return {"status": "success", "greeting": greeting}
            except Exception as e:
                logger.error(f"Error retrieving greeting for employee {employee_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_employee_greeting_tool = ToolDefinition(
            name="saadhan.identity_manager.get_employee_greeting",
            description="Gets a personalized greeting for an employee.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="employee_id", type="string", description="ID of the employee.", required=True)
            ]),
            execute_async=execute_get_employee_greeting
        )
        tools.append(get_employee_greeting_tool)

        # B.6: saadhan.identity_manager.is_employee
        async def execute_is_employee(inputs: dict):
            user_id = inputs.get("user_id")
            if not user_id:
                return {"error": "Missing required parameter: user_id"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'is_employee', None)):
                    logger.error("Orchestrator's identity_manager or is_employee method is not available.")
                    return {"error": "Employee check functionality is currently unavailable."}

                is_emp = await orchestrator.identity_manager.is_employee(user_id)
                logger.info(f"Checked if user {user_id} is employee: {is_emp}")
                return {"status": "success", "is_employee": is_emp}
            except Exception as e:
                logger.error(f"Error checking if user {user_id} is employee: {e}", exc_info=True)
                return {"error": str(e)}

        is_employee_tool = ToolDefinition(
            name="saadhan.identity_manager.is_employee",
            description="Checks if a given user ID belongs to an employee.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="user_id", type="string", description="ID of the user to check.", required=True)
            ]),
            execute_async=execute_is_employee
        )
        tools.append(is_employee_tool)

        # B.7: saadhan.identity_manager.get_employee_profile
        async def execute_get_employee_profile(inputs: dict):
            employee_id = inputs.get("employee_id")
            if not employee_id:
                return {"error": "Missing required parameter: employee_id"}
            try:
                if not hasattr(orchestrator, 'identity_manager') or \
                   not callable(getattr(orchestrator.identity_manager, 'get_employee_context', None)): # Original method name
                    logger.error("Orchestrator's identity_manager or get_employee_context method is not available.")
                    return {"error": "Employee profile retrieval functionality is currently unavailable."}

                profile_data = await orchestrator.identity_manager.get_employee_context(employee_id)
                if profile_data is None:
                    return {"error": f"Employee profile for ID '{employee_id}' not found."}
                logger.info(f"Retrieved profile for employee {employee_id}")
                return {"status": "success", "profile": asdict(profile_data) if is_dataclass(profile_data) else profile_data}
            except Exception as e:
                logger.error(f"Error retrieving profile for employee {employee_id}: {e}", exc_info=True)
                return {"error": str(e)}

        get_employee_profile_tool = ToolDefinition(
            name="saadhan.identity_manager.get_employee_profile",
            description="Retrieves the profile or context for an employee.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="employee_id", type="string", description="ID of the employee.", required=True)
            ]),
            execute_async=execute_get_employee_profile
        )
        tools.append(get_employee_profile_tool)

        # --- ProjectDetector Tools ---

        # C.1: saadhan.project_detector.detect_project_type
        async def execute_detect_project_type(inputs: dict):
            description = inputs.get("description")
            objectives = inputs.get("objectives")
            if not description or not objectives:
                return {"error": "Missing required parameters: description, objectives"}
            if not isinstance(objectives, list) or not all(isinstance(obj, str) for obj in objectives):
                return {"error": "Invalid type for objectives: must be an array of strings."}

            try:
                # Ensure orchestrator itself has project_detector, and it has the method
                if not hasattr(orchestrator, 'project_detector') or \
                   not callable(getattr(orchestrator.project_detector, 'detect_project_type', None)):
                    logger.error("Orchestrator's project_detector or detect_project_type method is not available.")
                    return {"error": "Project type detection functionality is currently unavailable."}

                project_type = await orchestrator.project_detector.detect_project_type(description, objectives)
                logger.info(f"Detected project type: {project_type}")
                return {"status": "success", "project_type": project_type} # Assuming it returns a string
            except Exception as e:
                logger.error(f"Error detecting project type: {e}", exc_info=True)
                return {"error": str(e)}

        detect_project_type_tool = ToolDefinition(
            name="saadhan.project_detector.detect_project_type",
            description="Detects the type of a project based on its description and objectives.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="description", type="string", description="Detailed description of the project.", required=True),
                ToolParameter(name="objectives", type="array", item_type="string", description="List of project objectives.", required=True),
            ]),
            execute_async=execute_detect_project_type
        )
        tools.append(detect_project_type_tool)

        # C.2: saadhan.project_detector.analyze_project_context
        async def execute_analyze_project_context(inputs: dict):
            description = inputs.get("description")
            objectives = inputs.get("objectives")
            if not description or not objectives:
                return {"error": "Missing required parameters: description, objectives"}
            if not isinstance(objectives, list) or not all(isinstance(obj, str) for obj in objectives):
                return {"error": "Invalid type for objectives: must be an array of strings."}

            try:
                if not hasattr(orchestrator, 'project_detector') or \
                   not callable(getattr(orchestrator.project_detector, 'analyze_project_context', None)):
                    logger.error("Orchestrator's project_detector or analyze_project_context method is not available.")
                    return {"error": "Project context analysis functionality is currently unavailable."}

                context_analysis = await orchestrator.project_detector.analyze_project_context(description, objectives)
                logger.info("Successfully analyzed project context.")
                return {"status": "success", "analysis": asdict(context_analysis) if is_dataclass(context_analysis) else context_analysis}
            except Exception as e:
                logger.error(f"Error analyzing project context: {e}", exc_info=True)
                return {"error": str(e)}

        analyze_project_context_tool = ToolDefinition(
            name="saadhan.project_detector.analyze_project_context",
            description="Analyzes the context of a project from its description and objectives.",
            input_schema=ToolInputSchema(parameters=[
                ToolParameter(name="description", type="string", description="Detailed description of the project.", required=True),
                ToolParameter(name="objectives", type="array", item_type="string", description="List of project objectives.", required=True),
            ]),
            execute_async=execute_analyze_project_context
        )
        tools.append(analyze_project_context_tool)

    else:
        logger.warning("Orchestrator not available. No Saadhan tools will be loaded.")
        # It might be useful to add a dummy tool if no tools are loaded,
        # to confirm the server itself is running, e.g., a health check tool.

    # Start the MCP server
    # The actual name and version would likely come from a config file or environment variables
    server_name = "SaadhanMCP"
    server_version = "0.1.0"
    logger.info(f"Starting MCP Server '{server_name}' v{server_version} with {len(tools)} tool(s).")

    # This is where the actual server runner from the mcp library would be called
    await run_stdio_server_async(tools, name=server_name, version=server_version)

    logger.info(f"MCP Server '{server_name}' has shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
