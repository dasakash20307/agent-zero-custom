import asyncio
from dataclasses import dataclass
import shlex
import time
import re # For sanitization display
from python.helpers.tool import BaseTool # Changed
from typing import Dict, Any, Literal # Added
from python.helpers import files, rfc_exchange
from python.helpers.print_style import PrintStyle
from python.helpers.shell_local import LocalInteractiveSession
from python.helpers.shell_ssh import SSHInteractiveSession
from python.helpers.docker import DockerContainerManager
from python.helpers.messages import truncate_text
import python.helpers.log as Log # For LogItem type hint

@dataclass
class State:
    shells: dict[int, LocalInteractiveSession | SSHInteractiveSession]
    docker: DockerContainerManager | None


class CodeExecution(BaseTool):

    @property
    def name(self) -> str:
        return "code_execution"

    @property
    def description(self) -> str:
        return "Executes code (Python, Node.js) or terminal commands in a controlled environment. Supports multiple sessions."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "runtime": {
                    "type": "string",
                    "description": "The runtime environment for the code/command.",
                    "enum": ["python", "nodejs", "terminal", "output", "reset"]
                },
                "code": {
                    "type": "string",
                    "description": "The code to execute (for python, nodejs runtimes) or the command (for terminal runtime)."
                },
                "session": {
                    "type": "integer",
                    "description": "The session ID for execution. Defaults to 0. Use different IDs for concurrent tasks.",
                    "default": 0
                },
                "ask_confirmation": {
                    "type": "boolean",
                    "description": "If true, explicitly asks for user confirmation before running potentially risky commands (like 'terminal'). Overrides agent config if true.",
                    "default": False
                }
            },
            "required": ["runtime"]
        }

    def _sanitize_terminal_command(self, command: str) -> str | None:
        if not command:
            return None

        # Disallow common shell metacharacters for command chaining or redirection
        # This is a basic check and not exhaustive.
        disallowed_patterns = [";", "&&", "||", "`", "$(", "<", ">", "|&"]
        for pattern in disallowed_patterns:
            if pattern in command:
                self.agent.context.log.log(type="warning", heading="Unsafe Command Blocked", content=f"Command '{self._sanitize_terminal_command_for_display(command)}' contains unsafe pattern '{pattern}'.")
                return None
        return command

    def _sanitize_terminal_command_for_display(self, command: str) -> str:
        return re.sub(r'[^ -~]', '?', command)

    async def execute(self, **kwargs: Any) -> str:
        runtime = kwargs.get("runtime", "").lower().strip()
        code_to_run = kwargs.get("code")
        session = int(kwargs.get("session", 0))
        ask_confirmation_arg = kwargs.get("ask_confirmation", False)

        log_kvps = {"runtime": runtime, "session": session}
        if code_to_run:
            log_kvps["code_preview"] = truncate_text(agent=self.agent, output=code_to_run, threshold=50)

        main_log_item = self.agent.context.log.log(
            type="code_exe_start",
            heading=f"{self.agent.agent_name}: Tool '{self.name}' called",
            kvps=log_kvps
        )

        await self.agent.handle_intervention()
        await self.prepare_state() # Manages self.state

        if self.agent.config.code_exec_require_confirmation and runtime == "terminal" and not ask_confirmation_arg:
            refusal_msg = "Execution of terminal command requires explicit confirmation from the user. Please include 'ask_confirmation: true' in the tool arguments if the user has confirmed they wish to proceed."
            self.agent.context.log.log(type="warning", heading="Execution Refused (Confirmation)", content=refusal_msg)
            main_log_item.update(content=f"Error: {refusal_msg}")
            return f"Error: {refusal_msg}"

        response_str = ""
        if runtime == "python":
            response_str = await self.execute_python_code(code=code_to_run, session=session)
        elif runtime == "nodejs":
            response_str = await self.execute_nodejs_code(code=code_to_run, session=session)
        elif runtime == "terminal":
            sanitized_command = self._sanitize_terminal_command(code_to_run or "")
            if not sanitized_command:
                main_log_item.update(content="Error: Terminal command contains potentially unsafe characters or patterns and was blocked.")
                return "Error: Terminal command contains potentially unsafe characters or patterns and was blocked."
            response_str = await self.execute_terminal_command(command=sanitized_command, session=session)
        elif runtime == "output":
            response_str = await self.get_terminal_output(session=session, log_item_to_update=main_log_item)
        elif runtime == "reset":
            response_str = await self.reset_terminal(session=session) # log_item_to_update could be added if reset_terminal updates it
        else:
            response_str = self.agent.read_prompt("fw.code.runtime_wrong.md", runtime=runtime)

        if not response_str:
            response_str = self.agent.read_prompt("fw.code.info.md", info=self.agent.read_prompt("fw.code.no_output.md"))

        main_log_item.update( # Update the main log item with the final truncated result
            content=truncate_text(agent=self.agent, output=response_str, threshold=200)
        )
        return response_str

    async def prepare_state(self, reset=False, session=None):
        self.state = self.agent.get_data("_cet_state")
        if not self.state or reset:
            if not self.state and self.agent.config.code_exec_docker_enabled:
                docker = DockerContainerManager(
                    logger=self.agent.context.log, # Changed: pass logger directly
                    name=self.agent.config.code_exec_docker_name,
                    image=self.agent.config.code_exec_docker_image,
                    ports=self.agent.config.code_exec_docker_ports,
                    volumes=self.agent.config.code_exec_docker_volumes,
                )
                docker.start_container()
            else:
                docker = self.state.docker if self.state else None

            shells = {} if not self.state else self.state.shells.copy()
            if session is not None and session in shells:
                shells[session].close()
                del shells[session]
            elif reset and not session:
                for s_id in list(shells.keys()): # Use s_id to avoid confusion with outer session
                    shells[s_id].close()
                shells = {}

            if 0 not in shells: # Default session 0
                if self.agent.config.code_exec_ssh_enabled:
                    pswd = (
                        self.agent.config.code_exec_ssh_pass
                        if self.agent.config.code_exec_ssh_pass
                        else await rfc_exchange.get_root_password()
                    )
                    shell_instance = SSHInteractiveSession( # Renamed to avoid conflict
                        self.agent.context.log,
                        self.agent.config.code_exec_ssh_addr,
                        self.agent.config.code_exec_ssh_port,
                        self.agent.config.code_exec_ssh_user,
                        pswd,
                    )
                else:
                    shell_instance = LocalInteractiveSession()
                shells[0] = shell_instance
                await shell_instance.connect()
            self.state = State(shells=shells, docker=docker)
        self.agent.set_data("_cet_state", self.state)

    async def execute_python_code(self, session: int, code: str | None, reset: bool = False):
        if code is None: return "Error: No Python code provided."
        escaped_code = shlex.quote(code)
        command = f"ipython -c {escaped_code}"
        return await self.terminal_session(session, command, reset)

    async def execute_nodejs_code(self, session: int, code: str | None, reset: bool = False):
        if code is None: return "Error: No Node.js code provided."
        escaped_code = shlex.quote(code)
        command = f"node /exe/node_eval.js {escaped_code}"
        return await self.terminal_session(session, command, reset)

    async def execute_terminal_command(
        self, session: int, command: str, reset: bool = False
    ):
        # Command sanitization is now handled in the main execute method
        return await self.terminal_session(session, command, reset)

    async def terminal_session(self, session: int, command: str, reset: bool = False):
        await self.agent.handle_intervention()
        for i in range(2): # Retry on lost connection
            try:
                if reset: # This reset is for the specific session before command
                    await self.reset_terminal(session=session, reason="Command-specific reset")

                if session not in self.state.shells:
                    if self.agent.config.code_exec_ssh_enabled:
                        pswd = (
                            self.agent.config.code_exec_ssh_pass
                            if self.agent.config.code_exec_ssh_pass
                            else await rfc_exchange.get_root_password()
                        )
                        new_shell = SSHInteractiveSession(
                            self.agent.context.log,
                            self.agent.config.code_exec_ssh_addr,
                            self.agent.config.code_exec_ssh_port,
                            self.agent.config.code_exec_ssh_user,
                            pswd,
                        )
                    else:
                        new_shell = LocalInteractiveSession()
                    self.state.shells[session] = new_shell
                    await new_shell.connect()

                self.state.shells[session].send_command(command)
                PrintStyle(
                    background_color="white", font_color="#1B4F72", bold=True
                ).print(f"{self.agent.agent_name} code execution output for session {session}")
                # Pass None for log_item_to_update as main execute will log final result.
                # Alternatively, get_terminal_output could do its own focused logging.
                return await self.get_terminal_output(session, log_item_to_update=None)
            except Exception as e:
                if i == 0: # Changed from i == 1 to retry once (0 then 1)
                    PrintStyle.error(f"Error in terminal session {session} (attempt {i+1}): {e}")
                    await self.prepare_state(reset=True, session=session) # Reset this specific session
                    continue
                else:
                    self.agent.context.log.log(type="error", heading=f"Terminal Session Error (Session {session})", content=str(e))
                    # Ensure a string is returned for BaseTool compatibility
                    return f"Error during terminal session {session} after retries: {e}"


    async def get_terminal_output(
        self,
        session=0,
        reset_full_output=True,
        first_output_timeout=30,
        between_output_timeout=15,
        max_exec_timeout=180,
        sleep_time=0.1,
        log_item_to_update: Log.LogItem | None = None # Added parameter
    ):
        prompt_patterns = [
            re.compile(r"\(venv\).+[$#] ?$"),
            re.compile(r"root@[^:]+:[^#]+# ?$"),
            re.compile(r"[a-zA-Z0-9_.-]+@[^:]+:[^$#]+[$#] ?$"),
        ]
        start_time = time.time()
        last_output_time = start_time
        full_output = ""
        got_output = False

        while True:
            await asyncio.sleep(sleep_time)
            current_full_output, partial_output = await self.state.shells[session].read_output(
                timeout=3, reset_full_output=reset_full_output
            )
            if reset_full_output: full_output = "" # Ensure full_output starts fresh if reset
            reset_full_output = False

            await self.agent.handle_intervention()
            now = time.time()

            if partial_output:
                PrintStyle(font_color="#85C1E9").stream(partial_output)
                full_output += partial_output # Accumulate full output correctly

                truncated_for_log = truncate_text(agent=self.agent, output=full_output, threshold=10000)
                if log_item_to_update:
                    log_item_to_update.update(content=truncated_for_log)
                # else: # Optional: log separately if no main log item to update
                #    self.agent.context.log.log("debug", f"Terminal Output (Session {session})", truncated_for_log)

                last_output_time = now
                got_output = True

                # Check for shell prompt (using full_output for context)
                # It's better to check the latest lines of the accumulated full_output
                last_lines = full_output.strip().splitlines()[-3:] if full_output.strip() else []
                for line in last_lines:
                    for pat in prompt_patterns:
                        if pat.search(line.strip()):
                            PrintStyle.info(f"Detected shell prompt in session {session}, returning output early.")
                            return full_output.strip()

            if now - start_time > max_exec_timeout:
                sysinfo = self.agent.read_prompt("fw.code.max_time.md", timeout=max_exec_timeout)
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                final_response = (full_output.strip() + "\n\n" + response) if full_output.strip() else response
                PrintStyle.warning(sysinfo)
                if log_item_to_update: log_item_to_update.update(content=final_response)
                return final_response

            if not got_output and (now - start_time > first_output_timeout):
                sysinfo = self.agent.read_prompt("fw.code.no_out_time.md", timeout=first_output_timeout)
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                PrintStyle.warning(sysinfo)
                if log_item_to_update: log_item_to_update.update(content=response)
                return response
            elif got_output and (now - last_output_time > between_output_timeout):
                sysinfo = self.agent.read_prompt("fw.code.pause_time.md", timeout=between_output_timeout)
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                final_response = (full_output.strip() + "\n\n" + response) if full_output.strip() else response
                PrintStyle.warning(sysinfo)
                if log_item_to_update: log_item_to_update.update(content=final_response)
                return final_response

            # If no output and no timeout hit yet, continue loop
            if not partial_output and not got_output and (now - start_time < first_output_timeout) :
                continue
            # If no new partial output but got output before, and no timeout hit yet, continue loop
            if not partial_output and got_output and (now - last_output_time < between_output_timeout):
                continue

            # If there was no partial_output and one of the conditions for returning (timeout/prompt) wasn't met,
            # it implies shell might be closed or not responsive.
            # However, the timeout conditions should catch this. If loop exits here, it means no conditions met.
            # Return accumulated output if any.
            if full_output.strip(): return full_output.strip()


    async def reset_terminal(self, session=0, reason: str | None = None):
        log_message = f"Resetting terminal session {session}..."
        if reason: log_message += f" Reason: {reason}"
        PrintStyle(font_color="#FFA500", bold=True).print(log_message)
        self.agent.context.log.log("info", "Terminal Reset", log_message)

        await self.prepare_state(reset=True, session=session)
        response = self.agent.read_prompt("fw.code.info.md", info=self.agent.read_prompt("fw.code.reset.md"))
        # self.log.update(content=response) # self.log is removed
        # This specific log update needs a log item if it's meant to update a specific one.
        # For a general log of reset completion:
        self.agent.context.log.log("info", f"Terminal Reset Complete (Session {session})", response)
        return response
