# AGENTS instructions

## OS Compatibility

**Important:** Before executing any shell command, you MUST determine the operating system. The current OS is provided in the initial context.

Based on the OS, use the appropriate commands. Here are some common examples:

| Operation         | Windows (`win32`) | Linux / macOS (`linux`, `darwin`) |
| ----------------- | ----------------- | --------------------------------- |
| **Delete File**   | `del <file>`      | `rm <file>`                       |
| **Delete Directory**| `rmdir /s /q <dir>`| `rm -rf <dir>`                    |
| **Create Directory**| `mkdir <dir>`     | `mkdir -p <dir>`                  |
| **List Files**    | `dir`             | `ls -la`                          |

*   **Shell:**
    *   On Windows, you are likely using `cmd.exe` or `PowerShell`.
    *   On Linux / macOS, you are likely using `bash` or `zsh`.

## Git tips and tricks

* when git commit write messages into commit.txt and delete it after commit
* before doing git stuff create backup branch
* when using git take in my that it can open vim, and you will stuck forever
* after you add changes and complete tasks always do a commit, commit message should be consistent with previous commits messages

## Project Overview

`kawaflow` is a monorepo project for building and managing event-driven, actor-based applications. It consists of three main components:

*   **`kawa`**: A Python framework for building event-driven applications using the actor model. It provides decorators (`@event` and `@actor`) to define events and actors, simplifying the development of concurrent and distributed systems.

*   **`flow-manager`**: A FastAPI application that manages the lifecycle of `flow` containers. It exposes a WebSocket API for creating, stopping, and communicating with flows. The `flow-manager` is responsible for dynamically creating and managing Docker containers that run the user-defined workflows.

*   **`flow`**: A Docker container environment where user-defined workflows, built with the `kawa` framework, are executed. These containers are provisioned and managed by the `flow-manager`.

The overall architecture allows for a decoupled system where workflows are defined using `kawa`, and the `flow-manager` handles the operational aspects of running them in isolated `flow` containers.

## Local build and run

For every task related to building, running, linting, testing e.t.c you should use `task ...` command and Taskfile.

*   **Build the entire project**:
    ```bash
    task build
    ```

*   **Run all tests**:
    ```bash
    task test
    ```

*   **Run linters**:
    ```bash
    task lint
    ```

*   **Fix linting issues**:
    ```bash
    task lint:fix
    ```

You can also run tasks for specific components. For example, to run tests only for the `kawa` component:

```bash
task kawa:test
```

**Important**: Do not use `task ...:sh` - you will stuck in this command because it will start bash terminal. If you want to run a command in container use `task ...:sh-exec -- ...` or create new task in related Taskfile.

## Development Conventions

*   **Task-based workflow**: All common development tasks (building, testing, linting, etc.) are managed through `Taskfile`. Please use the `task` commands for these operations.
*   **Git**: Follow the conventions outlined in this document for git operations.