import sys

def handle_echo(args, redirect_stdout=None, append_stdout=False, redirect_stderr=None, append_stderr=False):
  output = ' '.join(args[1:]) + '\n'
  if redirect_stderr:
    try:
      open(redirect_stderr, 'a' if append_stderr else 'w').close()
    except Exception as e:
      print(f"Error: {e}", file=sys.stderr)
  if redirect_stdout:
    try:
      with open(redirect_stdout, 'a' if append_stdout else 'w') as f:
        f.write(output)
    except Exception as e:
      print(f"Error: {e}", file=sys.stderr)
  else:
    sys.stdout.write(output)