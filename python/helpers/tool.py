from abc import ABC, abstractmethod # Modified this line
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING # Added for BaseTool

# Use TYPE_CHECKING for Agent import to avoid circular dependencies if agent.py imports from this module
if TYPE_CHECKING:
    from agent import Agent
    # If agent.py is in root, and this is python/helpers/tool.py, relative import:
    # from ...agent import Agent
else:
    # For runtime, if direct import works or if Agent is mostly for type hints in BaseTool constructor
    # This might need adjustment based on actual project structure and runtime behavior.
    # Using a forward reference / string literal 'Agent' in __init__ is safer.
    pass


from agent import Agent # This existing import might be for the old Tool class. Let's keep it for now.
from python.helpers.print_style import PrintStyle
from python.helpers.strings import sanitize_string


@dataclass
class Response:
    message:str
    break_loop: bool

class Tool:

    def __init__(self, agent: Agent, name: str, method: str | None, args: dict[str,str], message: str, **kwargs) -> None:
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.message = message

    @abstractmethod
    async def execute(self,**kwargs) -> Response:
        pass

    async def before_execution(self, **kwargs):
        PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
        self.log = self.get_log_object()
        if self.args and isinstance(self.args, dict):
            for key, value in self.args.items():
                PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key)+": ")
                PrintStyle(font_color="#85C1E9", padding=isinstance(value,str) and "\n" in value).stream(value)
                PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs):
        text = sanitize_string(response.message.strip())
        self.agent.hist_add_tool_result(self.name, text)
        PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color="#85C1E9").print(text)
        self.log.update(content=text)

    def get_log_object(self):
        if self.method:
            heading = f"{self.agent.agent_name}: Using tool '{self.name}:{self.method}'"
        else:
            heading = f"{self.agent.agent_name}: Using tool '{self.name}'"
        return self.agent.context.log.log(type="tool", heading=heading, content="", kvps=self.args)

    def nice_key(self, key:str):
        words = key.split('_')
        words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        result = ' '.join(words)
        return result


class BaseTool(ABC):
    def __init__(self, agent: 'Agent'): # Use string literal 'Agent' for type hint
        self.agent = agent

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does, its purpose, and when to use it."""
        pass

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """JSON schema for the tool's input parameters.
        Should follow the JSON Schema specification.
        Example:
        {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Description of param1."},
                "param2": {"type": "integer", "description": "Description of param2."}
            },
            "required": ["param1"]
        }
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Executes the tool with the given arguments.
        Args:
            **kwargs: The arguments for the tool, matching the defined schema.
        Returns:
            A string representing the result of the tool execution.
        """
        pass
