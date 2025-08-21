# AGENTS instructions

## OS tips and tricks

* when interacting with shell check OS, maybe it's windows and you will use cmd or powershell

## Git tips and tricks

* when git commit write messages into commit.txt and delete it after commit
* before doing git stuff create backup branch
* when using git take in my that it can open vim, and you will stuck forever
* after you add changes and complete tasks always do a commit, commit message should be consistent with previous commits messages

## Local build and run

For every task related to building, running, linting, testing e.t.c you should use `task ...` command and Taskfile.

Example task commands:

- `task build` - build all parts of project
- `task lint` - lint all parts of project
- `task lint:fix` - fix lint erros for all parts of project
- `task test`- test all parts of project
- `task flow:build` - build `/flow` container
- `task flow-manager:test -- tests/test_mod.py::test_func` - run specific tests for specified part
- `task kawa:test` - test `/kawa`

**Important**: Do not use `task ...:sh` - you will stuck in this command because it will start bash terminal. If you want to run a command in container use `task ...:sh-exec -- ...` or create new task in related Taskfile.
