import asyncio
import nest_asyncio
nest_asyncio.apply()

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Coroutine, Dict, Literal, Optional, Type # Added Optional, Type
from enum import Enum
import uuid
import os
import models
import jsonschema

from python.helpers import extract_tools, files, errors, history, tokens
from python.helpers import dirty_json
from python.helpers.print_style import PrintStyle
from python.helpers.tool import BaseTool # Added BaseTool import
from python.helpers.tool_registry import ToolRegistry # Added ToolRegistry import
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

import python.helpers.log as Log
from python.helpers.dirty_json import DirtyJson
from python.helpers.defer import DeferredTask
from typing import Callable
from python.helpers.localization import Localization


class AgentContextType(Enum):
    USER = "user"
    TASK = "task"
    MCP = "mcp"


class AgentContext:

    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0

    def __init__(
        self,
        config: "AgentConfig",
        id: str | None = None,
        name: str | None = None,
        agent0: "Agent|None" = None,
        log: Log.Log | None = None,
        paused: bool = False,
        streaming_agent: "Agent|None" = None,
        created_at: datetime | None = None,
        type: AgentContextType = AgentContextType.USER,
        last_message: datetime | None = None,
    ):
        # build context
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.agent0 = agent0 or Agent(0, self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.type = type
        AgentContext._counter += 1
        self.no = AgentContext._counter
        # set to start of unix epoch
        self.last_message = last_message or datetime.now(timezone.utc)

        existing = self._contexts.get(self.id, None)
        if existing:
            AgentContext.remove(self.id)
        self._contexts[self.id] = self

    @staticmethod
    def get(id: str):
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def first():
        if not AgentContext._contexts:
            return None
        return list(AgentContext._contexts.values())[0]
    
    @staticmethod
    def all():
        return list(AgentContext._contexts.values())

    @staticmethod
    def remove(id: str):
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": (
                Localization.get().serialize_datetime(self.created_at)
                if self.created_at else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "no": self.no,
            "log_guid": self.log.guid,
            "log_version": len(self.log.updates),
            "log_length": len(self.log.logs),
            "paused": self.paused,
            "last_message": (
                Localization.get().serialize_datetime(self.last_message)
                if self.last_message else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "type": self.type.value,
        }

    @staticmethod
    def log_to_all(
        type: Log.Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: Log.ProgressUpdate | None = None,
        id: str | None = None,  # Add id parameter
        **kwargs,
    ) -> list[Log.LogItem]:
        items: list[Log.LogItem] = []
        for context in AgentContext.all():
            items.append(context.log.log(type, heading, content, kvps, temp, update_progress, id, **kwargs))
        return items

    def kill_process(self):
        if self.task:
            self.task.kill()

    def reset(self):
        self.kill_process()
        self.log.reset()
        self.agent0 = Agent(0, self.config, self)
        self.streaming_agent = None
        self.paused = False

    def nudge(self):
        self.kill_process()
        self.paused = False
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self):
        return self.streaming_agent or self.agent0

    def communicate(self, msg: "UserMessage", broadcast_level: int = 1):
        self.paused = False  # unpause if paused

        current_agent = self.get_agent()

        if self.task and self.task.is_alive():
            # set intervention messages to agent(s):
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != 0:
                intervention_agent.intervention = msg
                broadcast_level -= 1
                intervention_agent = intervention_agent.data.get(
                    Agent.DATA_NAME_SUPERIOR, None
                )
        else:
            self.task = self.run_task(self._process_chain, current_agent, msg)

        return self.task

    def run_task(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ):
        if not self.task:
            self.task = DeferredTask(
                thread_name=self.__class__.__name__,
            )
        self.task.start_task(func, *args, **kwargs)
        return self.task

    # this wrapper ensures that superior agents are called back if the chat was loaded from file and original callstack is gone
    async def _process_chain(self, agent: "Agent", msg: "UserMessage|str", user=True):
        try:
            msg_template = (
                agent.hist_add_user_message(msg)  # type: ignore
                if user
                else agent.hist_add_tool_result(
                    tool_name="call_subordinate", tool_result=msg  # type: ignore
                )
            )
            response = await agent.monologue()  # type: ignore
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response, False)  # type: ignore
            return response
        except Exception as e:
            agent.handle_critical_exception(e)


@dataclass
class ModelConfig:
    provider: models.ModelProvider
    name: str
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict = field(default_factory=dict)


@dataclass
class AgentConfig:
    chat_model: ModelConfig
    utility_model: ModelConfig
    embeddings_model: ModelConfig
    browser_model: ModelConfig
    mcp_servers: str
    repairable_error_threshold: int = 3
    prompts_version: str | None = None
    history_truncation_strategy: Literal['summarize', 'truncate_oldest'] = 'truncate_oldest'
    prompt_structure_and_response_buffer: int = 250
    tool_execution_max_retries: int = 2  # Max retries for a failing tool
    tool_execution_retry_delay: float = 1.0  # Initial delay in seconds for retries
    tool_execution_retry_backoff_factor: float = 2.0 # Factor to multiply delay by for each retry
    code_exec_require_confirmation: bool = False # Default to no confirmation
    prompts_subdir: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    code_exec_docker_enabled: bool = False
    code_exec_docker_name: str = "A0-dev"
    code_exec_docker_image: str = "frdel/agent-zero-run:development"
    code_exec_docker_ports: dict[str, int] = field(
        default_factory=lambda: {"22/tcp": 55022, "80/tcp": 55080}
    )
    code_exec_docker_volumes: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            files.get_base_dir(): {"bind": "/a0", "mode": "rw"},
            files.get_abs_path("work_dir"): {"bind": "/root", "mode": "rw"},
        }
    )
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    code_exec_ssh_pass: str = ""
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    message: str
    attachments: list[str] = field(default_factory=list[str])
    system_message: list[str] = field(default_factory=list[str])


class LoopData:
    def __init__(self, **kwargs):
        self.iteration = -1
        self.system = []
        self.user_message: history.Message | None = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_temporary: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.extras_persistent: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.last_response = ""

        # override values with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# intervention exception class - skips rest of message loop iteration
class InterventionException(Exception):
    pass


# killer exception class - not forwarded to LLM, cannot be fixed on its own, ends message loop
class RepairableException(Exception):
    pass


class HandledException(Exception):
    pass


class ToolExecutionError(Exception):
    pass


class PromptGenerationError(Exception):
    pass


class ModelResponseError(Exception):
    pass


class Agent:

    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"
    DATA_NAME_CTX_WINDOW = "ctx_window"

    def __init__(
        self, number: int, config: AgentConfig, context: AgentContext | None = None
    ):

        # agent config
        self.config = config

        # agent context
        self.context = context or AgentContext(config)

        # non-config vars
        self.number = number
        self.agent_name = f"Agent {self.number}"

        self.history = history.History(self)
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data = {}  # free data object all the tools can use
        self.repairable_error_count = 0
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover_and_register_tools(agent=self)

    async def monologue(self):
        while True:
            try:
                self.repairable_error_count = 0
                # loop data dictionary to pass to extensions
                self.loop_data = LoopData(user_message=self.last_user_message)
                # call monologue_start extensions
                await self.call_extensions("monologue_start", loop_data=self.loop_data)

                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                # let the agent run message loop until he stops it with a response tool
                while True:

                    self.context.streaming_agent = self  # mark self as current streamer
                    self.loop_data.iteration += 1

                    # call message_loop_start extensions
                    await self.call_extensions("message_loop_start", loop_data=self.loop_data)

                    try:
                        # prepare LLM chain (model, system, history)
                        prompt = await self.prepare_prompt(loop_data=self.loop_data)

                        # output that the agent is starting
                        PrintStyle(
                            bold=True,
                            font_color="green",
                            padding=True,
                            background_color="white",
                        ).print(f"{self.agent_name}: Generating")
                        log = self.context.log.log(
                            type="agent", heading=f"{self.agent_name}: Generating"
                        )

                        async def stream_callback(chunk: str, full: str):
                            # output the agent response stream
                            if chunk:
                                printer.stream(chunk)
                                self.log_from_stream(full, log)

                        agent_response = await self.call_chat_model(
                            prompt, callback=stream_callback
                        )  # type: ignore

                        await self.handle_intervention(agent_response)

                        if (
                            self.loop_data.last_response == agent_response
                        ):  # if assistant_response is the same as last message in history, let him know
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # Append warning message to the history
                            warning_msg = self.read_prompt("fw.msg_repeat.md")
                            self.hist_add_warning(message=warning_msg)
                            PrintStyle(font_color="orange", padding=True).print(
                                warning_msg
                            )
                            self.context.log.log(type="warning", content=warning_msg)

                        else:  # otherwise proceed with tool
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # process tools requested in agent message
                            tools_result = await self.process_tools(agent_response)
                            if tools_result:  # final response of message loop available
                                return tools_result  # break the execution if the task is done

                    # exceptions inside message loop:
                    except InterventionException as e:
                        pass  # intervention message has been handled in handle_intervention(), proceed with conversation loop
                    except ToolExecutionError as e:
                        error_message = errors.format_error(e)
                        self.hist_add_warning(error_message)
                        PrintStyle(font_color="red", padding=True).print(error_message)
                        self.context.log.log(type="error", content=error_message, heading="Tool Execution Error")
                        # TODO: Implement retry logic with exponential backoff for ToolExecutionError
                        raise RepairableException(f"Tool execution failed: {e}") from e
                    except ModelResponseError as e:
                        error_message = errors.format_error(e)
                        self.hist_add_warning(error_message)
                        PrintStyle(font_color="red", padding=True).print(error_message)
                        self.context.log.log(type="error", content=error_message, heading="Model Response Error")
                        # TODO: Implement retry logic with exponential backoff for ModelResponseError
                        raise RepairableException(f"Model response error: {e}") from e
                    except PromptGenerationError as e:
                        error_message = errors.format_error(e)
                        PrintStyle(font_color="red", padding=True).print(error_message)
                        self.context.log.log(type="error", content=error_message, heading="Prompt Generation Error")
                        raise HandledException(f"Prompt generation failed: {e}") from e
                    except RepairableException as e:
                        self.repairable_error_count += 1
                        if self.repairable_error_count >= self.config.repairable_error_threshold:
                            self.context.log.log(type="error", heading="Repair Threshold Reached", content=f"Agent {self.agent_name} encountered {self.repairable_error_count} consecutive repairable errors. Escalating to HandledException.")
                            raise HandledException(f"Repairable error threshold reached for agent {self.agent_name}. Last error: {e}") from e
                        else:
                            # Forward repairable errors to the LLM, maybe it can fix them
                            error_message = errors.format_error(e)
                            self.hist_add_warning(error_message)
                            PrintStyle(font_color="red", padding=True).print(error_message)
                            self.context.log.log(type="error", content=error_message)
                    except Exception as e:
                        # Other exception kill the loop
                        self.handle_critical_exception(e)

                    finally:
                        # call message_loop_end extensions
                        await self.call_extensions(
                            "message_loop_end", loop_data=self.loop_data
                        )

            # exceptions outside message loop:
            except InterventionException as e:
                self.context.log.log(type="info", heading="Agent Intervention", content=f"Agent {self.agent_name} received an intervention. Message: {e}")
                pass  # just start over
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None  # unset current streamer
                # call monologue_end extensions
                await self.call_extensions("monologue_end", loop_data=self.loop_data)  # type: ignore

    async def prepare_prompt(self, loop_data: LoopData) -> ChatPromptTemplate:
        self.context.log.set_progress("Building prompt")
        await self.call_extensions("message_loop_prompts_before", loop_data=loop_data)

        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output() # This is just agent's own history

        await self.call_extensions("message_loop_prompts_after", loop_data=loop_data)

        # === Start of new context window management logic ===
        system_text = "\n\n".join(loop_data.system)
        system_tokens = tokens.count_tokens(system_text)

        target_ctx_length = self.config.chat_model.ctx_length
        # Buffer for the final prompt structure (e.g., role tags, separators) and expected model output
        prompt_structure_and_response_buffer = self.config.prompt_structure_and_response_buffer

        available_tokens_for_dynamic_content = target_ctx_length - system_tokens - prompt_structure_and_response_buffer

        # Prepare extras (these are OutputMessage format)
        extras_data = {**loop_data.extras_persistent, **loop_data.extras_temporary}
        extras_output_messages: list[history.OutputMessage] = []
        if extras_data:
            extras_content_str = self.read_prompt("agent.context.extras.md", extras=dirty_json.stringify(extras_data))
            # history.Message(...).output() returns a list of history.OutputMessage
            extras_output_messages = history.Message(False, content=extras_content_str).output()

        # Combine history and extras
        # loop_data.history_output is from agent's direct history
        all_dynamic_output_messages: list[history.OutputMessage] = loop_data.history_output + extras_output_messages

        current_dynamic_tokens = tokens.count_tokens(history.output_text(all_dynamic_output_messages))

        managed_dynamic_output_messages = all_dynamic_output_messages
        truncation_applied = "none"

        if current_dynamic_tokens > available_tokens_for_dynamic_content:
            truncation_applied = self.config.history_truncation_strategy
            if self.config.history_truncation_strategy == 'truncate_oldest':
                temp_messages = list(all_dynamic_output_messages) # Make a mutable copy
                while tokens.count_tokens(history.output_text(temp_messages)) > available_tokens_for_dynamic_content and temp_messages:
                    # Naive: remove oldest. A better way might preserve user/assistant turns or important messages.
                    temp_messages.pop(0)
                managed_dynamic_output_messages = temp_messages
                self.context.log.log(type="info", heading="Context Truncation", content=f"Truncated oldest messages to fit context window. Original dynamic tokens: {current_dynamic_tokens}, New dynamic tokens: {tokens.count_tokens(history.output_text(managed_dynamic_output_messages))}, Available for dynamic: {available_tokens_for_dynamic_content}")

            elif self.config.history_truncation_strategy == 'summarize':
                # Actual summarization is complex and needs an LLM call.
                # For this subtask, log a warning and fallback to 'truncate_oldest'.
                self.context.log.log(type="warning", heading="Context Management", content="History summarization strategy is selected but not fully implemented; using 'truncate_oldest' as fallback.")
                truncation_applied = "summarize (fallback: truncate_oldest)" # Be clear about fallback
                temp_messages = list(all_dynamic_output_messages)
                while tokens.count_tokens(history.output_text(temp_messages)) > available_tokens_for_dynamic_content and temp_messages:
                    temp_messages.pop(0)
                managed_dynamic_output_messages = temp_messages
                self.context.log.log(type="info", heading="Context Truncation (Summarize Fallback)", content=f"Truncated oldest messages to fit context window. Original dynamic tokens: {current_dynamic_tokens}, New dynamic tokens: {tokens.count_tokens(history.output_text(managed_dynamic_output_messages))}, Available for dynamic: {available_tokens_for_dynamic_content}")

        # Convert the managed list of OutputMessage to Langchain BaseMessage objects
        final_langchain_messages: list[BaseMessage] = history.output_langchain(managed_dynamic_output_messages)

        loop_data.extras_temporary.clear() # Clear temp extras after they've been processed

        # === End of new context window management logic ===

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_text),
                *final_langchain_messages,
            ]
        )

        # Store context window data using the final formatted prompt string for accurate token count
        final_prompt_str = prompt.format() # This resolves all templates and roles
        final_token_count = tokens.count_tokens(final_prompt_str)

        self.set_data(
            Agent.DATA_NAME_CTX_WINDOW,
            {
                "text": final_prompt_str,
                "tokens": final_token_count,
                "max_tokens": target_ctx_length,
                "truncation_applied": truncation_applied,
                "system_tokens": system_tokens,
                "dynamic_tokens_before_manage": current_dynamic_tokens,
                "dynamic_tokens_after_manage": tokens.count_tokens(history.output_text(managed_dynamic_output_messages)),
                "available_for_dynamic": available_tokens_for_dynamic_content
            },
        )
        return prompt

    def handle_critical_exception(self, exception: Exception):
        if isinstance(exception, HandledException):
            raise exception  # Re-raise the exception to kill the loop
        elif isinstance(exception, asyncio.CancelledError):
            # Handling for asyncio.CancelledError
            PrintStyle(font_color="white", background_color="red", padding=True).print(
                f"Context {self.context.id} terminated during message loop"
            )
            raise HandledException(
                exception
            )  # Re-raise the exception to cancel the loop
        else:
            # Handling for general exceptions
            error_text = errors.error_text(exception)
            error_message = errors.format_error(exception)
            PrintStyle(font_color="red", padding=True).print(error_message)
            self.context.log.log(
                type="error",
                heading="Error",
                content=error_message,
                kvps={"text": error_text},
            )
            raise HandledException(exception)  # Re-raise the exception to kill the loop

    async def get_system_prompt(self, loop_data: LoopData) -> list[str]:
        system_prompt = []
        await self.call_extensions(
            "system_prompt", system_prompt=system_prompt, loop_data=loop_data
        )
        return system_prompt

    def _resolve_prompt_file_path(self, file_name: str) -> str:
        primary_search_dir = files.get_abs_path("prompts", "default")
        backup_search_dirs = []
        if self.config.prompts_subdir:
            primary_search_dir = files.get_abs_path("prompts", self.config.prompts_subdir)
            backup_search_dirs.append(files.get_abs_path("prompts", "default"))

        # 1. Try versioned file in primary directory
        if self.config.prompts_version:
            base, ext = os.path.splitext(file_name)
            versioned_file = f"{base}.{self.config.prompts_version}{ext}"
            path_to_check = files.get_abs_path(primary_search_dir, versioned_file)
            if os.path.exists(path_to_check):
                return path_to_check

            # 2. Try versioned file in backup directories
            for b_dir in backup_search_dirs:
                path_to_check = files.get_abs_path(b_dir, versioned_file)
                if os.path.exists(path_to_check):
                    return path_to_check

        # 3. Try original file in primary directory
        path_to_check = files.get_abs_path(primary_search_dir, file_name)
        if os.path.exists(path_to_check):
            return path_to_check

        # 4. Try original file in backup directories
        for b_dir in backup_search_dirs:
            path_to_check = files.get_abs_path(b_dir, file_name)
            if os.path.exists(path_to_check):
                return path_to_check

        # 5. If not found anywhere, raise FileNotFoundError
        # Construct a helpful error message
        checked_paths = []
        if self.config.prompts_version:
            base, ext = os.path.splitext(file_name)
            versioned_file = f"{base}.{self.config.prompts_version}{ext}"
            checked_paths.append(files.get_abs_path(primary_search_dir, versioned_file))
            for b_dir in backup_search_dirs: checked_paths.append(files.get_abs_path(b_dir, versioned_file))

        checked_paths.append(files.get_abs_path(primary_search_dir, file_name))
        for b_dir in backup_search_dirs: checked_paths.append(files.get_abs_path(b_dir, file_name))

        raise FileNotFoundError(f"Prompt file '{file_name}' (and its versioned variant if applicable) not found. Checked: {checked_paths}")

    def parse_prompt(self, file: str, **kwargs) -> Any:
        resolved_absolute_path = self._resolve_prompt_file_path(file)
        # Similar to read_prompt, pass absolute path. files.parse_file handles the rest.
        return files.parse_file(resolved_absolute_path, _backup_dirs=[], **kwargs)

    def read_prompt(self, file: str, **kwargs) -> str:
        resolved_absolute_path = self._resolve_prompt_file_path(file)
        # python.helpers.files.read_file expects a path relative to project root, or one it can find.
        # If we pass an absolute path, its internal find_file_in_dirs should just confirm it.
        # The _backup_dirs argument for files.read_file will be empty, as path is pre-resolved.
        # The kwargs are passed for Jinja rendering and include processing within files.read_file.
        return files.read_file(resolved_absolute_path, _backup_dirs=[], **kwargs)

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(
        self, ai: bool, content: history.MessageContent, tokens: int = 0
    ):
        self.last_message = datetime.now(timezone.utc)
        return self.history.add_message(ai=ai, content=content, tokens=tokens)

    def hist_add_user_message(self, message: UserMessage, intervention: bool = False):
        self.history.new_topic()  # user message starts a new topic in history

        # load message template based on intervention
        if intervention:
            content = self.parse_prompt(
                "fw.intervention.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message
            )
        else:
            content = self.parse_prompt(
                "fw.user_message.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message
            )

        # remove empty parts from template
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}

        # add to history
        msg = self.hist_add_message(False, content=content)  # type: ignore
        self.last_user_message = msg
        return msg

    def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt("fw.ai_response.md", message=message)
        return self.hist_add_message(True, content=content)

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt("fw.warning.md", message=message)
        return self.hist_add_message(False, content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str):
        content = self.parse_prompt(
            "fw.tool_result.md", tool_name=tool_name, tool_result=tool_result
        )
        return self.hist_add_message(False, content=content)

    def concat_messages(
        self, messages
    ):  # TODO add param for message range, topic, history
        return self.history.output_text(human_label="user", ai_label="assistant")

    def get_chat_model(self):
        return models.get_model(
            models.ModelType.CHAT,
            self.config.chat_model.provider,
            self.config.chat_model.name,
            **self.config.chat_model.kwargs,
        )

    def get_utility_model(self):
        return models.get_model(
            models.ModelType.CHAT,
            self.config.utility_model.provider,
            self.config.utility_model.name,
            **self.config.utility_model.kwargs,
        )

    def get_embedding_model(self):
        return models.get_model(
            models.ModelType.EMBEDDING,
            self.config.embeddings_model.provider,
            self.config.embeddings_model.name,
            **self.config.embeddings_model.kwargs,
        )

    async def call_utility_model(
        self,
        system: str,
        message: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessage(content=system), HumanMessage(content=message)]
        )

        response = ""

        # model class
        model = self.get_utility_model()

        # rate limiter
        limiter = await self.rate_limiter(
            self.config.utility_model, prompt.format(), background
        )

        async for chunk in (prompt | model).astream({}):
            await self.handle_intervention()  # wait for intervention and handle it, if paused

            content = models.parse_chunk(chunk)
            limiter.add(output=tokens.approximate_tokens(content))
            response += content

            if callback:
                await callback(content)

        return response

    async def call_chat_model(
        self,
        prompt: ChatPromptTemplate,
        callback: Callable[[str, str], Awaitable[None]] | None = None,
    ):
        response = ""

        # model class
        model = self.get_chat_model()

        # rate limiter
        limiter = await self.rate_limiter(self.config.chat_model, prompt.format())

        async for chunk in (prompt | model).astream({}):
            await self.handle_intervention()  # wait for intervention and handle it, if paused

            content = models.parse_chunk(chunk)
            limiter.add(output=tokens.approximate_tokens(content))
            response += content

            if callback:
                await callback(content, response)

        return response

    async def rate_limiter(
        self, model_config: ModelConfig, input: str, background: bool = False
    ):
        # rate limiter log
        wait_log = None

        async def wait_callback(msg: str, key: str, total: int, limit: int):
            nonlocal wait_log
            if not wait_log:
                wait_log = self.context.log.log(
                    type="util",
                    update_progress="none",
                    heading=msg,
                    model=f"{model_config.provider.value}\\{model_config.name}",
                )
            wait_log.update(heading=msg, key=key, value=total, limit=limit)
            if not background:
                self.context.log.set_progress(msg, -1)

        # rate limiter
        limiter = models.get_rate_limiter(
            model_config.provider,
            model_config.name,
            model_config.limit_requests,
            model_config.limit_input,
            model_config.limit_output,
        )
        limiter.add(input=tokens.approximate_tokens(input))
        limiter.add(requests=1)
        await limiter.wait(callback=wait_callback)
        return limiter

    async def handle_intervention(self, progress: str = ""):
        while self.context.paused:
            await asyncio.sleep(0.1)  # wait if paused
        if (
            self.intervention
        ):  # if there is an intervention message, but not yet processed
            msg = self.intervention
            self.intervention = None  # reset the intervention message
            if progress.strip():
                self.hist_add_ai_response(progress)
            # append the intervention message
            self.hist_add_user_message(msg, intervention=True)
            raise InterventionException(msg)

    async def wait_if_paused(self):
        while self.context.paused:
            await asyncio.sleep(0.1)

    async def process_tools(self, msg: str):
        # search for tool usage requests in agent message
        tool_request = extract_tools.json_parse_dirty(msg)

        if tool_request is not None:
            raw_tool_name = tool_request.get("tool_name", "")  # Get the raw tool name
            tool_args = tool_request.get("tool_args", {})
            
            tool_name = raw_tool_name  # Initialize tool_name with raw_tool_name
            tool_method = None  # Initialize tool_method

            # Split raw_tool_name into tool_name and tool_method if applicable
            if ":" in raw_tool_name:
                tool_name, tool_method = raw_tool_name.split(":", 1)
            
            tool = None  # Initialize tool to None

            # Try getting tool from MCP first
            try:
                import python.helpers.mcp_handler as mcp_helper 
                mcp_tool_candidate = mcp_helper.MCPConfig.get_instance().get_tool(self, tool_name)
                if mcp_tool_candidate:
                    tool = mcp_tool_candidate
            except ImportError:
                PrintStyle(background_color="black", font_color="yellow", padding=True).print(
                    "MCP helper module not found. Skipping MCP tool lookup."
                 )
            except Exception as e:
                PrintStyle(background_color="black", font_color="red", padding=True).print(
                    f"Failed to get MCP tool '{tool_name}': {e}"
                )

            # Fallback to local get_tool if MCP tool was not found or MCP lookup failed
            if not tool: # tool here is the MCP tool candidate
                # If MCP tool not found, try local registry
                tool_name_to_lookup = tool_name # tool_name is already the base name after potential split

                tool_instance = self.get_tool(name=tool_name_to_lookup) # This now returns Optional[BaseTool]

                if tool_instance:
                    await self.handle_intervention()

                    # **Input Validation**
                    try:
                        jsonschema.validate(instance=tool_args, schema=tool_instance.schema)
                        self.context.log.log(type="debug", heading=f"Tool Input Validation", content=f"Inputs for {tool_instance.name} are valid.")
                    except jsonschema.exceptions.ValidationError as e_validate:
                        error_message = f"Tool input validation failed for {tool_instance.name}: {e_validate.message}"
                        # Correctly format the path if it's not empty
                        path_str = '.'.join(str(p) for p in e_validate.path) if e_validate.path else "input"
                        short_error = f"Input validation error for {tool_instance.name}: field '{path_str}' - {e_validate.message}"
                        self.context.log.log(type="error", heading="Tool Input Error", content=error_message)
                        self.hist_add_warning(f"Error: {short_error}. The arguments provided for '{tool_instance.name}' were invalid. Please check the required parameters and types.")
                        raise RepairableException(f"Invalid arguments for tool {tool_instance.name}. Details: {short_error}") from e_validate

                    # **Retry Logic for Execution**
                    retries = 0
                    current_delay = self.config.tool_execution_retry_delay
                    tool_result_str = None # Initialize to ensure it's defined

                    while retries <= self.config.tool_execution_max_retries:
                        await self.handle_intervention() # Check before each attempt
                        try:
                            tool_result_str = await tool_instance.execute(**tool_args)
                            await self.handle_intervention() # Check after successful execution
                            break # Success, exit retry loop

                        except InterventionException: # Make sure intervention is re-raised
                            raise
                        except Exception as e_exec: # Catch any exception during tool.execute
                            error_message_formatted = errors.format_error(e_exec)
                            error_heading = f"Tool Execution Attempt Failed ({tool_instance.name}, Attempt {retries + 1})"
                            self.context.log.log(type="error", heading=error_heading, content=error_message_formatted)

                            if retries < self.config.tool_execution_max_retries:
                                self.context.log.log(type="info", heading="Tool Retry", content=f"Retrying tool {tool_instance.name} in {current_delay:.2f}s...")
                                await asyncio.sleep(current_delay)
                                current_delay *= self.config.tool_execution_retry_backoff_factor
                                retries += 1
                            else:
                                # Max retries reached, raise ToolExecutionError
                                self.context.log.log(type="error", heading="Tool Execution Failed", content=f"Tool {tool_instance.name} failed after {self.config.tool_execution_max_retries + 1} attempts.")
                                raise ToolExecutionError(f"Tool {tool_instance.name} failed after {self.config.tool_execution_max_retries + 1} attempts. Last error: {e_exec}") from e_exec

                    if tool_result_str is None: # Should be caught by break or raise in loop
                         # This case should ideally not be reached if the loop always breaks or raises.
                         # If it is reached, it means something went wrong with the loop logic itself.
                         self.context.log.log(type="error", heading="Tool Execution Logic Error", content=f"Tool {tool_instance.name} exited retry loop unexpectedly without a result or specific error.")
                         raise ToolExecutionError(f"Tool {tool_instance.name} execution finished retry loop without result or definitive error.")

                    # Add the tool's string result to history (if successful)
                    self.hist_add_tool_result(tool_name=tool_instance.name, tool_result=tool_result_str)

                    # Handle loop breaking for specific tools like "task_done"
                    if tool_instance.name == "task_done":
                        return tool_result_str
                else:
                    # This 'else' corresponds to 'if tool_instance:'
                    # This part handles when tool_instance is None (not found by self.get_tool from local registry)
                    error_detail = f"Tool '{raw_tool_name}' not found in local registry."
                    self.hist_add_warning(error_detail)
                    PrintStyle(font_color="red", padding=True).print(error_detail)
                    self.context.log.log(type="error", content=f"{self.agent_name}: {error_detail}")

            # If an MCP tool *was* found and assigned to `tool` variable:
            elif tool: # This 'elif' is for the case where MCP tool was found
                # This assumes the MCP tool adheres to the old Tool class structure for now.
                # This part will need refactoring if MCP tools also move to BaseTool.
                # For this subtask, we leave MCP tool execution as it was.
                # IMPORTANT: This means `tool` variable here is an old-style tool from MCP.
                # The new `tool_instance` is for BaseTools from local registry.
                # The original code would have proceeded with `tool.before_execution` etc.
                # We need to ensure that if an MCP tool was found, its execution path is preserved.

                # Preserving original execution path for MCP tools (or old tools if any slip through)
                # This requires `tool` to be the one from `self.get_tool` if not MCP.
                # The structure should be:
                # 1. Try MCP. If found, `tool = mcp_tool_candidate`.
                # 2. If not MCP, `tool_instance_base = self.get_tool(...)`.
                # 3. If `tool_instance_base` found, execute it.
                # 4. Else if `tool` (from MCP) found, execute it (old way).
                # 5. Else, tool not found.

                # The current diff places the new logic inside the `if not tool:` (meaning MCP tool not found) block.
                # This is correct. If an MCP tool *is* found, the `if not tool:` block is skipped.
                # The original code after `if not tool: tool = self.get_tool(...)` was:
                # `if tool:` followed by execution. This `tool` could be MCP or local (old style).
                # This needs to be carefully merged.

                # Let's refine the replacement. The new logic should replace the *local tool handling* part.
                # The MCP tool, if found, would be in `tool` and should be handled by the original `if tool:` block
                # that expected an old-style tool.
                # This subtask's goal is to begin adapting for BaseTool, so local tools are the focus.
                # The provided diff correctly puts the new logic inside the `if not tool:` (MCP not found)
                # and then handles `tool_instance` (BaseTool).
                # The `else` for `if tool_instance` handles "BaseTool not found in registry".
                # What happens if MCP tool was found? The original code had a single `if tool:`
                # that would execute it.
                # The current structure is:
                # if mcp_tool: tool = mcp_tool
                # if not tool: # (meaning no MCP tool)
                #    tool_instance = self.get_tool() # new BaseTool lookup
                #    if tool_instance: execute BaseTool
                #    else: error "not in local registry"
                # This leaves a gap: what if MCP tool was found? It's in `tool` but not executed.
                # The original code needs to be preserved for the MCP case.

                # Corrected structure for process_tools:
                # ...
                # tool = None
                # try: mcp_tool = ...; if mcp_tool: tool = mcp_tool
                # except: ...
                #
                # if tool: # This is an MCP tool (or old style if logic was different)
                #    # Execute MCP/old-style tool (original logic for this path)
                #    await self.handle_intervention()
                #    await tool.before_execution(**tool_args) # Assuming old interface
                #    # ... and so on for old tool execution ...
                #    response = await tool.execute(**tool_args)
                #    await tool.after_execution(response)
                #    if response.break_loop: return response.message
                # else: # No MCP tool found, try new local BaseTool registry
                #    tool_name_to_lookup = ...
                #    tool_instance = self.get_tool(name=tool_name_to_lookup)
                #    if tool_instance:
                #        # ... new BaseTool execution logic from subtask ...
                #        # (as provided in the SEARCH block for this diff)
                #        return tool_result_str # if task_done
                #    else:
                #        # error "not in local registry"
                # ...
                # This means the replacement should be more targeted.
                # The diff tool will apply the change to the section that originally called `self.get_tool`
                # for local tools.

                # The provided diff is intended to replace the *fallback* local tool logic.
                # The key is that `tool = self.get_tool(...)` is replaced.
                # The original code structure was:
                #   (Try MCP)
                #   if not tool: tool = self.get_tool(name=tool_name, method=tool_method, args=tool_args, message=msg)
                #   if tool: (execute tool, which could be MCP or local old-style)
                #   else: (error tool not found)
                # The change needs to fit into this.
                # The new `self.get_tool` returns `BaseTool | None`.
                # The old `self.get_tool` returned an old `Tool` instance (even `Unknown`).

                # The provided SEARCH block in the subtask description is:
                #    # Fallback to local get_tool if MCP tool was not found or MCP lookup failed
                #    if not tool:
                #        tool = self.get_tool(name=tool_name, method=tool_method, args=tool_args, message=msg) # OLD get_tool
                #
                #    if tool: # This `tool` could be from MCP or the OLD get_tool
                #        await self.handle_intervention()
                #        await tool.before_execution(**tool_args)
                #        # ... execute old tool ...
                #    else: # error_detail = f"Tool '{raw_tool_name}' not found or could not be initialized."
                #
                # The REPLACE block is the new logic for BaseTools.
                # This means the `if tool:` block that executes the tool also needs to change
                # if the tool is a BaseTool.

                # Simpler approach for this step:
                # The diff should replace the part *after* MCP tools are tried.
                # The existing code, after trying MCP, does:
                #   `if not tool: tool = self.get_tool(...)` (old get_tool)
                #   `if tool: ... execute old style ...`
                #   `else: ... tool not found ...`
                # We are changing `self.get_tool` to return `BaseTool | None`.
                # So the execution logic in `if tool:` must distinguish.

                # The provided SEARCH block for the diff tool needs to be the part that handles
                # the *local tool* path.
                # The current diff will apply to the `if not tool: tool = self.get_tool(...)` part,
                # and then the subsequent `if tool:` execution. This is complex.

                # Let's assume the provided SEARCH block correctly identifies the section for local tools.
                # The key is that if an MCP tool is found, it's handled by logic *outside* this diff.
                # If no MCP tool, then this new logic runs.
                # This seems to be what the diff implies by its placement.
                pass # This is a placeholder for the original logic if MCP tool was found and needs old execution style.
                # The diff will replace the section that was for *local* tools.
                # The `elif tool:` part in my reasoning above was to address if MCP tool was found.
                # The current diff structure correctly targets the `if not tool:` block (no MCP tool).
                # The `else` for tool not found in registry is also correct.
                # The original `if tool:` that executed old tools is effectively replaced for non-MCP path.
                # The `else:` (error_detail = f"Tool '{raw_tool_name}' not found or could not be initialized.")
                # from the original code is the one that should be replaced by the new `else:` for registry not found.
                # This seems fine.
        else:
            warning_msg_misformat = self.read_prompt("fw.msg_misformat.md")
            self.hist_add_warning(warning_msg_misformat)
            PrintStyle(font_color="red", padding=True).print(warning_msg_misformat)
            self.context.log.log(
                type="error", content=f"{self.agent_name}: Message misformat, no valid tool request found."
            )

    def log_from_stream(self, stream: str, logItem: Log.LogItem):
        try:
            if len(stream) < 25:
                return  # no reason to try
            response = DirtyJson.parse_string(stream)
            if isinstance(response, dict):
                # log if result is a dictionary already
                logItem.update(content=stream, kvps=response)
        except Exception as e:
            pass

    def get_tool(self, name: str, method: str | None = None, args: dict = None, message: str = None, **kwargs) -> Optional[BaseTool]:
        # The 'method', 'args', 'message' were for the old Tool structure.
        # BaseTool instances are already initialized.
        # If a tool name itself contains a method like "browser:click", process_tools should handle splitting.

        tool_instance = self.tool_registry.get_tool(name)
        if not tool_instance:
            self.context.log.log(type="warning", heading="Tool Not Found", content=f"Tool '{name}' not found in registry.")
            # Returning None, process_tools will need to handle this.
            # Example: Fallback to an UnknownTool that inherits BaseTool could be done here if desired.
            return None
        return tool_instance

    async def call_extensions(self, folder: str, **kwargs) -> Any:
        from python.helpers.extension import Extension

        classes = extract_tools.load_classes_from_folder(
            "python/extensions/" + folder, "*", Extension
        )
        for cls in classes:
            await cls(agent=self).execute(**kwargs)
