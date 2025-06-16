import os
import importlib
import inspect
import fnmatch
from typing import Dict, Type, Optional, TYPE_CHECKING

from .tool import BaseTool
from .files import get_abs_path # Assuming files.py is in the same directory (python/helpers/)

if TYPE_CHECKING:
    # If agent.py is in root, and this is python/helpers/tool_registry.py
    from ...agent import Agent
else:
    # Using string literal 'Agent' for type hints to avoid import issues in subtask
    pass

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {} # Stores instantiated tools
        self.tool_classes: Dict[str, Type[BaseTool]] = {} # Stores tool classes

    def discover_and_register_tools(self, agent: 'Agent', tool_directory: str = "python/tools"):
        """Discovers tools in the given directory, instantiates them, and registers them."""
        abs_tool_dir = get_abs_path(tool_directory)

        if not os.path.isdir(abs_tool_dir):
            agent.context.log.log(type="warning", heading="Tool Discovery", content=f"Tool directory {abs_tool_dir} not found.")
            return

        for filename in os.listdir(abs_tool_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                # Construct module path relative to the project structure.
                # If tool_directory is "python/tools", then module is "python.tools.modulename"
                module_path_parts = tool_directory.replace('/', '.').split('.')
                # Ensure no empty parts if tool_directory starts with / or has //
                module_path_parts = [part for part in module_path_parts if part]
                module_path_parts.append(module_name)
                module_import_path = ".".join(module_path_parts)

                try:
                    module = importlib.import_module(module_import_path)
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        if issubclass(cls, BaseTool) and cls is not BaseTool:
                            try:
                                tool_instance = cls(agent=agent)
                                if tool_instance.name in self.tool_classes:
                                    agent.context.log.log(type="warning", heading="Tool Registration", content=f"Duplicate tool name '{tool_instance.name}' found from {module_import_path}. Existing: {self.tool_classes[tool_instance.name]}. New: {cls}. Skipping new.")
                                else:
                                    self.tools[tool_instance.name] = tool_instance
                                    self.tool_classes[tool_instance.name] = cls
                                    agent.context.log.log(type="info", heading="Tool Registration", content=f"Registered tool: {tool_instance.name} from {module_import_path}")
                            except Exception as e:
                                agent.context.log.log(type="error", heading="Tool Instantiation Error", content=f"Error instantiating tool {cls.__name__} from {module_import_path}: {e}")
                except ImportError as e:
                    agent.context.log.log(type="error", heading="Tool Import Error", content=f"Error importing tool module {module_import_path}: {e}")
                except Exception as e: # Catch other potential errors during module processing
                    agent.context.log.log(type="error", heading="Tool Discovery Error", content=f"Error processing tool module {module_import_path}: {e}")


    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Gets an instantiated tool by its name."""
        return self.tools.get(name)

    def get_tool_class(self, name: str) -> Optional[Type[BaseTool]]:
        """Gets a tool class by its name."""
        return self.tool_classes.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        return self.tools

    def get_all_tool_schemas(self) -> list[dict]:
        """Returns a list of schemas for all registered tools, including name and description."""
        schemas = []
        for tool_name, tool_instance in self.tools.items():
            try:
                schemas.append({
                    "name": tool_instance.name,
                    "description": tool_instance.description,
                    "schema": tool_instance.schema,
                })
            except Exception as e:
                # Log if a tool fails to provide its schema details
                if hasattr(tool_instance, 'agent') and hasattr(tool_instance.agent, 'context'):
                    tool_instance.agent.context.log.log(type="error", heading="Tool Schema Error", content=f"Error retrieving schema for tool {tool_name}: {e}")
                else:
                    print(f"Error retrieving schema for tool {tool_name} (agent context not available for logging): {e}")

        return schemas
