from python.helpers.tool import BaseTool
from typing import Dict, Any # For schema typing

class TaskDone(BaseTool):

    @property
    def name(self) -> str:
        return "task_done"

    @property
    def description(self) -> str:
        return "Signals that the current task is complete and the agent should stop further processing and respond. Input should be the final message to the user."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The final message or summary of the completed task."
                }
            },
            "required": ["text"]
        }

    async def execute(self, **kwargs: Any) -> str:
        text_response = kwargs.get("text", "Task marked as done.")

        # Log the action (similar to old before_execution)
        self.agent.context.log.log(
            type="response",
            heading=f"{self.agent.agent_name}: Task done",
            content=text_response
        )

        # Existing logic from the old tool
        self.agent.set_data("timeout", 0)

        # BaseTool.execute returns a string.
        # This string will be the message.
        # process_tools will need to identify that "task_done" was called
        # and then handle the loop termination.
        return text_response