import sys
import os
import subprocess
import shlex
import readline
import atexit
from pathlib import Path


# Builtin commands
BUILTIN_COMMANDS = ["echo", "exit", "history", "type", "pwd", "cd"]

# Track history base for append operation
history_base_for_append = 0


class ShellCompleter:
    """Auto-completion for commands"""
    
    def __init__(self):
        self.matches = []
    
    def complete(self, text, state):
        """Generate completions for text"""
        if state == 0:
            # Only complete the first word (command)
            line = readline.get_line_buffer()
            if line.startswith(text):
                self.matches = self._get_matches(text)
            else:
                self.matches = []
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def _get_matches(self, text):
        """Get all matching commands"""
        matches = []
        
        # Check builtin commands
        for cmd in BUILTIN_COMMANDS:
            if cmd.startswith(text):
                matches.append(cmd)
        
        # Check external commands in PATH
        path_env = os.environ.get("PATH", "")
        for directory in path_env.split(os.pathsep):
            try:
                if os.path.isdir(directory):
                    for entry in os.listdir(directory):
                        full_path = os.path.join(directory, entry)
                        if entry.startswith(text) and os.access(full_path, os.X_OK):
                            if entry not in matches:
                                matches.append(entry)
            except (PermissionError, OSError):
                continue
        
        return sorted(matches)


def setup_readline():
    """Setup readline with history and completion"""
    # Setup completion
    completer = ShellCompleter()
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    
    # Setup history
    histfile = os.environ.get("HISTFILE")
    if histfile and os.path.exists(histfile):
        try:
            readline.read_history_file(histfile)
        except Exception:
            pass
    
    # Save history on exit
    def save_history():
        if histfile:
            try:
                readline.write_history_file(histfile)
            except Exception:
                pass
    
    atexit.register(save_history)


def parse_command(command_str):
    """Parse command string handling quotes and escapes"""
    args = []
    current_arg = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    
    while i < len(command_str):
        char = command_str[i]
        
        if char == '\\' and not in_single_quote:
            # Handle backslash escaping
            if in_double_quote:
                # In double quotes, only escape certain characters
                if i + 1 < len(command_str) and command_str[i + 1] in ['"', '\\']:
                    current_arg.append(command_str[i + 1])
                    i += 2
                    continue
                else:
                    current_arg.append('\\')
                    i += 1
            else:
                # Outside quotes, escape next character
                if i + 1 < len(command_str):
                    current_arg.append(command_str[i + 1])
                    i += 2
                    continue
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
        elif char.isspace() and not in_single_quote and not in_double_quote:
            if current_arg:
                args.append(''.join(current_arg))
                current_arg = []
            i += 1
        else:
            current_arg.append(char)
            i += 1
    
    if current_arg:
        args.append(''.join(current_arg))
    
    return args


def handle_echo(args, redirect_stdout=None, append_stdout=False):
    """Handle echo command"""
    output = ' '.join(args[1:]) + '\n'
    
    if redirect_stdout:
        mode = 'a' if append_stdout else 'w'
        try:
            with open(redirect_stdout, mode) as f:
                f.write(output)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
    else:
        sys.stdout.write(output)


def handle_pwd():
    """Handle pwd command"""
    print(os.getcwd())


def handle_cd(args):
    """Handle cd command"""
    if len(args) < 2:
        print("cd: missing argument", file=sys.stderr)
        return
    
    path = args[1]
    if path == "~":
        path = os.environ.get("HOME", os.path.expanduser("~"))
    
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory", file=sys.stderr)
    except Exception as e:
        print(f"cd: {e}", file=sys.stderr)


def handle_type(args):
    """Handle type command"""
    if len(args) < 2:
        print("type: missing file operand", file=sys.stderr)
        return
    
    cmd = args[1]
    
    # Check if builtin
    if cmd in BUILTIN_COMMANDS:
        print(f"{cmd} is a shell builtin")
        return
    
    # Check in PATH
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        full_path = os.path.join(directory, cmd)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            print(f"{cmd} is {full_path}")
            return
    
    print(f"{cmd}: not found", file=sys.stderr)


def handle_history(args):
    """Handle history command"""
    global history_base_for_append
    
    if len(args) > 1:
        flag = args[1]
        
        if flag == "-r":
            # Read history from file
            if len(args) < 3:
                print("history: -r: option requires an argument", file=sys.stderr)
                return
            try:
                readline.read_history_file(args[2])
            except Exception:
                print(f"history: {args[2]}: cannot read history file", file=sys.stderr)
        
        elif flag == "-w":
            # Write history to file
            if len(args) < 3:
                print("history: -w: option requires an argument", file=sys.stderr)
                return
            try:
                readline.write_history_file(args[2])
            except Exception:
                print(f"history: {args[2]}: cannot write history file", file=sys.stderr)
        
        elif flag == "-a":
            # Append new history to file
            if len(args) < 3:
                print("history: -a: option requires an argument", file=sys.stderr)
                return
            
            current_length = readline.get_current_history_length()
            new_entries = current_length - history_base_for_append
            
            if new_entries > 0:
                try:
                    readline.append_history_file(new_entries, args[2])
                    history_base_for_append = current_length
                except Exception:
                    print(f"history: {args[2]}: cannot append to history file", file=sys.stderr)
        
        elif flag.isdigit():
            # Show last n entries
            n = int(flag)
            total = readline.get_current_history_length()
            start = max(0, total - n)
            
            for i in range(start, total):
                line = readline.get_history_item(i + 1)
                if line:
                    print(f"{i + 1:5d}  {line}")
        else:
            print(f"history: {flag}: invalid option", file=sys.stderr)
    else:
        # Display all history
        total = readline.get_current_history_length()
        for i in range(total):
            line = readline.get_history_item(i + 1)
            if line:
                print(f"{i + 1:5d}  {line}")


def parse_redirections(args):
    """Parse redirection operators from args"""
    redirect_stdout = None
    redirect_stderr = None
    append_stdout = False
    append_stderr = False
    clean_args = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in [">", "1>"]:
            if i + 1 < len(args):
                redirect_stdout = args[i + 1]
                append_stdout = False
                i += 2
                continue
            else:
                print(f"syntax error: expected file after '{arg}'", file=sys.stderr)
                return None
        
        elif arg in [">>", "1>>"]:
            if i + 1 < len(args):
                redirect_stdout = args[i + 1]
                append_stdout = True
                i += 2
                continue
            else:
                print(f"syntax error: expected file after '{arg}'", file=sys.stderr)
                return None
        
        elif arg == "2>":
            if i + 1 < len(args):
                redirect_stderr = args[i + 1]
                append_stderr = False
                i += 2
                continue
            else:
                print(f"syntax error: expected file after '{arg}'", file=sys.stderr)
                return None
        
        elif arg == "2>>":
            if i + 1 < len(args):
                redirect_stderr = args[i + 1]
                append_stderr = True
                i += 2
                continue
            else:
                print(f"syntax error: expected file after '{arg}'", file=sys.stderr)
                return None
        
        clean_args.append(arg)
        i += 1
    
    return {
        'args': clean_args,
        'redirect_stdout': redirect_stdout,
        'redirect_stderr': redirect_stderr,
        'append_stdout': append_stdout,
        'append_stderr': append_stderr
    }


def execute_command(args, redirect_stdout=None, redirect_stderr=None, 
                   append_stdout=False, append_stderr=False,
                   stdin_pipe=None, stdout_pipe=None):
    """Execute external command"""
    try:
        # Setup stdin/stdout for piping
        stdin_arg = stdin_pipe if stdin_pipe else None
        stdout_arg = stdout_pipe if stdout_pipe else None
        stderr_arg = None
        
        # Handle file redirections
        if redirect_stdout and not stdout_pipe:
            mode = 'a' if append_stdout else 'w'
            stdout_arg = open(redirect_stdout, mode)
        
        if redirect_stderr:
            mode = 'a' if append_stderr else 'w'
            stderr_arg = open(redirect_stderr, mode)
        
        result = subprocess.run(
            args,
            stdin=stdin_arg,
            stdout=stdout_arg if stdout_arg else None,
            stderr=stderr_arg if stderr_arg else None,
            text=True
        )
        
        # Close file handles if we opened them
        if redirect_stdout and stdout_arg and not stdout_pipe:
            stdout_arg.close()
        if redirect_stderr and stderr_arg:
            stderr_arg.close()
        
        return result.returncode
    
    except FileNotFoundError:
        print(f"{args[0]}: command not found", file=sys.stderr)
        return 127
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def execute_pipeline(command_str):
    """Execute pipeline of commands"""
    commands = [cmd.strip() for cmd in command_str.split('|')]
    num_cmds = len(commands)
    
    processes = []
    prev_pipe = None
    
    for i, cmd in enumerate(commands):
        args = parse_command(cmd)
        if not args:
            continue
        
        # Create pipe for output if not last command
        if i < num_cmds - 1:
            read_pipe, write_pipe = os.pipe()
        else:
            read_pipe, write_pipe = None, None
        
        pid = os.fork()
        
        if pid == 0:
            # Child process
            try:
                # Setup stdin from previous pipe
                if prev_pipe is not None:
                    os.dup2(prev_pipe, sys.stdin.fileno())
                    os.close(prev_pipe)
                
                # Setup stdout to next pipe
                if write_pipe is not None:
                    os.dup2(write_pipe, sys.stdout.fileno())
                    os.close(write_pipe)
                    os.close(read_pipe)
                
                # Handle builtin commands
                if args[0] == "echo":
                    handle_echo(args)
                    sys.exit(0)
                elif args[0] == "exit":
                    sys.exit(0)
                elif args[0] == "pwd":
                    handle_pwd()
                    sys.exit(0)
                elif args[0] == "cd":
                    handle_cd(args)
                    sys.exit(0)
                elif args[0] == "type":
                    handle_type(args)
                    sys.exit(0)
                elif args[0] == "history":
                    handle_history(args)
                    sys.exit(0)
                else:
                    # Execute external command
                    os.execvp(args[0], args)
            except Exception as e:
                print(f"{args[0]}: command not found", file=sys.stderr)
                sys.exit(127)
        
        # Parent process
        if prev_pipe is not None:
            os.close(prev_pipe)
        
        if write_pipe is not None:
            os.close(write_pipe)
        
        prev_pipe = read_pipe
        processes.append(pid)
    
    # Wait for all processes
    for pid in processes:
        os.waitpid(pid, 0)


def main():
    # Setup readline
    setup_readline()
    
    # Flush stdout
    sys.stdout.reconfigure(line_buffering=True)
    
    while True:
        try:
            # Read input
            line = input("$ ")
            
            if not line.strip():
                continue
            
            # Add to history
            readline.add_history(line)
            
            # Check for pipeline
            if '|' in line:
                execute_pipeline(line)
                continue
            
            # Parse command
            args = parse_command(line)
            if not args:
                continue
            
            # Parse redirections
            parsed = parse_redirections(args)
            if parsed is None:
                continue
            
            args = parsed['args']
            redirect_stdout = parsed['redirect_stdout']
            redirect_stderr = parsed['redirect_stderr']
            append_stdout = parsed['append_stdout']
            append_stderr = parsed['append_stderr']
            
            # Handle builtin commands
            if args[0] == "exit":
                # Save history
                histfile = os.environ.get("HISTFILE")
                if histfile:
                    try:
                        readline.write_history_file(histfile)
                    except Exception:
                        pass
                
                # Exit with code if provided
                if len(args) > 1:
                    try:
                        sys.exit(int(args[1]))
                    except ValueError:
                        sys.exit(0)
                else:
                    sys.exit(0)
            
            elif args[0] == "echo":
                handle_echo(args, redirect_stdout, append_stdout)
            
            elif args[0] == "pwd":
                handle_pwd()
            
            elif args[0] == "cd":
                handle_cd(args)
            
            elif args[0] == "type":
                handle_type(args)
            
            elif args[0] == "history":
                handle_history(args)
            
            else:
                # Execute external command
                execute_command(
                    args,
                    redirect_stdout=redirect_stdout,
                    redirect_stderr=redirect_stderr,
                    append_stdout=append_stdout,
                    append_stderr=append_stderr
                )
        
        except EOFError:
            # Handle Ctrl+D
            print()
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print()
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
