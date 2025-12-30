[![progress-banner](https://backend.codecrafters.io/progress/shell/30c2d41f-1c18-4564-b167-49875c59ef28)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

["Build Your Own Shell" Challenge](https://app.codecrafters.io/courses/shell/overview).

# Build Your Own Shell (Python)

This repository contains my Python implementation of a POSIX-style shell, inspired by the CodeCrafters **Build Your Own Shell** challenge.

A shell is the program that interprets what you type into the terminal. It reads commands, runs programs, and prints their output. Popular shells include **Bash** and **ZSH**.

In this project, I’m rebuilding those ideas in **Python**, focusing on correctness, clarity, and learning how shells work internally.

---

## What am I building?

I’m building a shell that runs a **REPL (Read–Eval–Print Loop)**, parses user input, executes built-in commands, and launches external programs.

Even at early stages, the shell is already usable: I can type commands, see their output, chain programs together, and navigate the filesystem.

---

## Core features

The foundation of the shell includes:

- Reading and parsing user input
- Running a REPL loop
- Built-in commands such as `pwd`, `cd`, `echo`, `exit`, and `type`
- Locating executables using `$PATH`
- Executing external programs

---

## Advanced features

As the project progresses, the shell supports increasingly realistic behavior:

- Piping and redirection
- Quoting and escaping
- Command history and navigation
- Autocompletion
- Multi-command pipelines
- Persistent history across sessions

By the end, this repository represents a full, non-trivial shell implementation written in Python.

---

## What am I learning?

### Early stages

- How shells read, parse, and execute commands
- How a REPL works internally
- The difference between built-in commands and external programs
- How `$PATH` is used to locate executables
- How processes are spawned and managed

### Later stages

- Parsing complex syntax such as quotes, escapes, and pipelines
- Managing input/output streams for redirection and pipes
- Process orchestration using Python’s subprocess model
- Structuring and refactoring a growing codebase

As the implementation grows, I’m forced to design cleaner abstractions to avoid regressions and make new features easier to add.

---

## Why build a shell in Python?

Building a shell in Python provides a strong bridge between **high-level programming** and **operating system concepts**.

It allows me to:
- Explore how everyday tools actually work
- Apply systems thinking without low-level boilerplate
- Translate OS-level ideas (processes, pipes, file descriptors) into a higher-level language

The result is a project that’s both technically deep and highly practical.

---

## Prerequisites

- Comfortable writing Python
- Familiarity with Git

No prior experience with shells or operating systems is required. Most concepts are learned through experimentation and debugging.

This is not a follow-along tutorial. Progress comes from curiosity, persistence, and understanding failures.

---

## Implemented stages

### Basics
- Print a prompt
- Handle invalid commands
- Implement a REPL
- Implement `exit`
- Implement `echo`
- Implement `type`
- Locate executable files
- Run external programs

### Navigation
- The `pwd` builtin
- The `cd` builtin (absolute paths)
- The `cd` builtin (relative paths)
- The `cd` builtin (home directory)

### Quoting and escaping
- Single quotes
- Double quotes
- Backslash outside quotes
- Backslash within quotes
- Executing quoted executables

### Redirection
- Redirect stdout
- Redirect stderr
- Append stdout
- Append stderr

### Autocompletion
- Built-in completion
- Completion with arguments
- Missing completions
- Executable completion
- Multiple completions
- Partial completions

### Pipelines
- Dual-command pipelines
- Pipelines with built-ins
- Multi-command pipelines

### History
- The `history` builtin
- Listing history
- Limiting history entries
- Up-arrow navigation
- Down-arrow navigation
- Executing commands from history

### History persistence
- Read history from file
- Write history to file
- Append history to file
- Load history on startup
- Save history on exit

---

At the end of this project, I’ll have a clean, readable Python shell implementation that demonstrates a deep understanding of how real shells work under the hood.
