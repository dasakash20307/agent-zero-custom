from fnmatch import fnmatch
import json
import os
import re # re was imported twice
import base64
import jinja2
import shutil
import tempfile
import zipfile

from python.helpers.strings import sanitize_string

_jinja_env = None
def get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = jinja2.Environment(
            loader=jinja2.BaseLoader(), # BaseLoader as templates are strings
            undefined=jinja2.StrictUndefined,
            autoescape=False # Prompts are often not HTML
        )
    return _jinja_env

def _read_raw_file_content(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()

def parse_file(_relative_path: str, _backup_dirs: list[str] | None = None, _encoding: str = "utf-8", **kwargs) -> Any: # Original type was Any
    if _backup_dirs is None: _backup_dirs = []

    absolute_path = find_file_in_dirs(_relative_path, _backup_dirs)
    # Read raw content once for is_full_json_template check and for processing
    raw_content = _read_raw_file_content(absolute_path, _encoding)

    content_with_includes = process_includes(raw_content, os.path.dirname(absolute_path), _backup_dirs, _encoding, **kwargs)

    rendered_content_str = replace_placeholders_text(content_with_includes, **kwargs) # Jinja rendering

    # Check if the *original* template structure (raw_content) indicated it's JSON
    # is_full_json_template checks for ```json ... ``` fences.
    if is_full_json_template(raw_content):
        content_to_load = remove_code_fences(rendered_content_str) # remove fences from the rendered string
        try:
            obj = json.loads(content_to_load)
            return obj
        except json.JSONDecodeError as e:
            # Provide more context in case of error
            error_msg = (
                f"Failed to parse rendered content as JSON from '{_relative_path}'. "
                f"Error: {e}. Rendered content (first 200 chars): '{content_to_load[:200]}...'"
            )
            raise ValueError(error_msg) from e
    else:
        # It's a plain text template, remove fences from the rendered string
        return remove_code_fences(rendered_content_str)


def read_file(_relative_path: str, _backup_dirs: list[str] | None = None, _encoding: str = "utf-8", **kwargs) -> str:
    if _backup_dirs is None: _backup_dirs = []

    absolute_path = find_file_in_dirs(_relative_path, _backup_dirs)
    raw_content = _read_raw_file_content(absolute_path, _encoding)

    content_with_includes = process_includes(raw_content, os.path.dirname(absolute_path), _backup_dirs, _encoding, **kwargs)

    final_content = replace_placeholders_text(content_with_includes, **kwargs) # Jinja rendering
    return final_content


def read_file_bin(_relative_path, _backup_dirs=None):
    # init backup dirs
    if _backup_dirs is None:
        _backup_dirs = []

    # get absolute path
    absolute_path = find_file_in_dirs(_relative_path, _backup_dirs)

    # read binary content
    with open(absolute_path, "rb") as f:
        return f.read()


def read_file_base64(_relative_path, _backup_dirs=None):
    # init backup dirs
    if _backup_dirs is None:
        _backup_dirs = []

    # get absolute path
    absolute_path = find_file_in_dirs(_relative_path, _backup_dirs)

    # read binary content and encode to base64
    with open(absolute_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def replace_placeholders_text(_content: str, **kwargs) -> str:
    if not kwargs: # If no kwargs, no templating needed
        return _content
    env = get_jinja_env()
    try:
        template = env.from_string(_content)
        return template.render(**kwargs)
    except jinja2.exceptions.TemplateSyntaxError as e:
        raise ValueError(f"Jinja2 template syntax error: {e}") from e
    except jinja2.exceptions.UndefinedError as e:
        raise ValueError(f"Jinja2 undefined variable: {e}") from e


# def replace_placeholders_json(_content: str, **kwargs):
#     # Superseded by Jinja2 rendering in replace_placeholders_text
#     # Ensure the output of Jinja is a valid JSON string if used for JSON
#     if not kwargs:
#         return _content
#     env = get_jinja_env()
#     template = env.from_string(_content)
#     return template.render(**kwargs)


# def replace_placeholders_dict(_content: dict, **kwargs):
#     # Superseded by Jinja2 rendering before JSON parsing.
#     return _content


def process_includes(_content: str, _base_dir_for_includes: str, _backup_dirs: list[str], _encoding: str = "utf-8", **kwargs_for_include_path_rendering) -> str:
    include_pattern = re.compile(r"{{\s*include\s*['"](.*?)['"]\s*}}")

    processed_paths_stack = kwargs_for_include_path_rendering.get('_processed_paths_stack', [])

    def replace_include(match):
        include_path_template = match.group(1)
        rendered_include_path = include_path_template # Keep it simple: path is literal

        # Try path relative to the current file's directory first
        # Note: os.path.join might behave unexpectedly if rendered_include_path is absolute.
        # Assuming rendered_include_path is always relative for this logic.
        current_file_try_path = os.path.normpath(os.path.join(_base_dir_for_includes, rendered_include_path))

        # Check for recursion
        # Using normpath to ensure consistent path representation (e.g. /a/b vs /a/./b)
        normalized_attempt_path = os.path.normpath(current_file_try_path)
        if os.path.isfile(normalized_attempt_path): # only add to stack if it's a valid file we are about to read
            if normalized_attempt_path in processed_paths_stack:
                raise RecursionError(f"Circular include detected for path: {normalized_attempt_path}. Stack: {' -> '.join(processed_paths_stack)}")


        try:
            if os.path.isfile(current_file_try_path):
                found_abs_path = current_file_try_path
            else:
                found_abs_path = find_file_in_dirs(rendered_include_path, _backup_dirs)

            included_raw_content = _read_raw_file_content(found_abs_path, _encoding)

            # Add current path to stack for the recursive call
            new_stack = processed_paths_stack + [os.path.normpath(found_abs_path)]
            return process_includes(included_raw_content, os.path.dirname(found_abs_path), _backup_dirs, _encoding, **{**kwargs_for_include_path_rendering, '_processed_paths_stack': new_stack})

        except FileNotFoundError:
            return f"Error: Included file '{rendered_include_path}' not found. Looked near '{_base_dir_for_includes}' and in backups: '{_backup_dirs}'."
        except RecursionError as e_rec:
            raise e_rec # Propagate recursion error

    # Iteratively replace includes to handle nested cases (simple approach)
    # A more robust solution would parse the template structure.
    final_content = _content
    for _ in range(10): # Limit iterations to prevent runaway loops
        new_content = include_pattern.sub(replace_include, final_content)
        if new_content == final_content:
            break
        final_content = new_content
    else: # If loop finished due to iterations limit
        if include_pattern.search(final_content):
            # Log or raise an error if includes are still present after max iterations
            # This indicates a complex case not handled, or an error string was injected.
            print(f"Warning: Max include iterations reached or unresolvable include in content starting with: {final_content[:100]}")

    return final_content


def find_file_in_dirs(file_path, backup_dirs):
    """
    This function tries to find the file first in the given file_path,
    and then in the backup_dirs if not found in the original location.
    Returns the absolute path of the found file.
    """
    # Try the original path first
    if os.path.isfile(get_abs_path(file_path)):
        return get_abs_path(file_path)

    # Loop through the backup directories
    for backup_dir in backup_dirs:
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        if os.path.isfile(get_abs_path(backup_path)):
            return get_abs_path(backup_path)

    # If the file is not found, let it raise the FileNotFoundError
    raise FileNotFoundError(
        f"File '{file_path}' not found in the original path or backup directories."
    )


import re


def remove_code_fences(text):
    # Pattern to match code fences with optional language specifier
    pattern = r"(```|~~~)(.*?\n)(.*?)(\1)"

    # Function to replace the code fences
    def replacer(match):
        return match.group(3)  # Return the code without fences

    # Use re.DOTALL to make '.' match newlines
    result = re.sub(pattern, replacer, text, flags=re.DOTALL)

    return result


import re


def is_full_json_template(text):
    # Pattern to match the entire text enclosed in ```json or ~~~json fences
    pattern = r"^\s*(```|~~~)\s*json\s*\n(.*?)\n\1\s*$"
    # Use re.DOTALL to make '.' match newlines
    match = re.fullmatch(pattern, text.strip(), flags=re.DOTALL)
    return bool(match)


def write_file(relative_path: str, content: str, encoding: str = "utf-8"):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    content = sanitize_string(content, encoding)
    with open(abs_path, "w", encoding=encoding) as f:
        f.write(content)


def write_file_bin(relative_path: str, content: bytes):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)


def write_file_base64(relative_path: str, content: str):
    # decode base64 string to bytes
    data = base64.b64decode(content)
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)


def delete_dir(relative_path: str):
    # ensure deletion of directory without propagating errors
    abs_path = get_abs_path(relative_path)
    if os.path.exists(abs_path):
        # first try with ignore_errors=True which is the safest option
        shutil.rmtree(abs_path, ignore_errors=True)

        # if directory still exists, try more aggressive methods
        if os.path.exists(abs_path):
            try:
                # try to change permissions and delete again
                for root, dirs, files in os.walk(abs_path, topdown=False):
                    for name in files:
                        file_path = os.path.join(root, name)
                        os.chmod(file_path, 0o777)
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, 0o777)

                # try again after changing permissions
                shutil.rmtree(abs_path, ignore_errors=True)
            except:
                # suppress all errors - we're ensuring no errors propagate
                pass


def list_files(relative_path: str, filter: str = "*"):
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    return [file for file in os.listdir(abs_path) if fnmatch(file, filter)]


def make_dirs(relative_path: str):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)


def get_abs_path(*relative_paths):
    return os.path.join(get_base_dir(), *relative_paths)


def exists(*relative_paths):
    path = get_abs_path(*relative_paths)
    return os.path.exists(path)


def get_base_dir():
    # Get the base directory from the current file path
    base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, "../../")))
    return base_dir


def is_in_base_dir(path: str):
    # check if the given path is within the base directory
    base_dir = get_base_dir()
    # normalize paths to handle relative paths and symlinks
    abs_path = os.path.abspath(path)
    # check if the absolute path starts with the base directory
    return os.path.commonpath([abs_path, base_dir]) == base_dir


def get_subdirectories(
    relative_path: str,
    include: str | list[str] = "*",
    exclude: str | list[str] | None = None,
):
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]
    return [
        subdir
        for subdir in os.listdir(abs_path)
        if os.path.isdir(os.path.join(abs_path, subdir))
        and any(fnmatch(subdir, inc) for inc in include)
        and (exclude is None or not any(fnmatch(subdir, exc) for exc in exclude))
    ]


def zip_dir(dir_path: str):
    full_path = get_abs_path(dir_path)
    zip_file_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
    base_name = os.path.basename(full_path)
    with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zip:
        for root, _, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, full_path)
                zip.write(file_path, os.path.join(base_name, rel_path))
    return zip_file_path


def move_file(relative_path: str, new_path: str):
    abs_path = get_abs_path(relative_path)
    new_abs_path = get_abs_path(new_path)
    os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
    os.rename(abs_path, new_abs_path)


def safe_file_name(filename: str) -> str:
    # Replace any character that's not alphanumeric, dash, underscore, or dot with underscore
    import re

    return re.sub(r"[^a-zA-Z0-9-._]", "_", filename)
