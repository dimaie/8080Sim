# 8080 Simulator Execution & Plugin Architecture

## 1. The Core Debugger and Compiler
The core of the `js-8080-sim` application (`debugger.py` and `ui.py`) is a generic 8080 execution environment. Its primary responsibilities are:
* Compiling assembly text into memory.
* Stepping through instructions and tracking CPU registers/flags.
* Managing breakpoints and highlighting execution lines.
* Providing generic Memory and Stack panel views.

The generic debugger has absolutely no knowledge of hardware specifics such as Memory-Mapped I/O, display rendering, or operating system routines (Monitor ROMs).

## 2. The Plugin System Integration
To support debugging within a complete hardware environment, the debugger provides a delegation interface (`BasePlugin`). Plugins act as hardware wrappers that can override memory reads/writes (for MMIO) and run their own background threads.

The generic UI interrogates the active plugin to decide how to manage compilation and execution states:
* **`is_user_program_mode(start_addr)`:** The debugger asks the plugin if the newly compiled code is a User Program (subroutine) or a system-level override. If it's a User Program, the compiler dynamically preserves the existing memory (keeping the Monitor ROM and video RAM intact).
* **Generic Mode (No Plugin / Monitor Debugging):** If no plugin is active, or the plugin declares it is not in User Program Mode, the debugger wipes memory upon recompilation and executes the code linearly from `start_addr`. The UI completely owns the CPU loop.
* **Emulated Hardware Mode:** If the plugin declares it is in User Program Mode, it spins up a lightweight background thread. This thread continuously executes the CPU natively, keeping the hardware (like a blinking cursor or keyboard buffer) alive while the UI debugger sits idle.

## 3. Context Switching Lifecycle
When a User Program is compiled alongside an active hardware monitor, the debugger and plugin work together to perform a seamless context switch. This allows the generic UI to debug a program as if it were natively launched via a Monitor's 'G' (Go) command.

1. **Intercept (`pre_execute`):** When the user hits **Run**, **Step**, or **Animate**, the UI execution loop halts and invokes `p.pre_execute()`.
2. **Context Save:** The plugin safely suspends its background monitor thread and snapshots the complete CPU state (Registers, SP, PC, Flags).
3. **Bootloader Setup:** The plugin pushes a predefined trap address (e.g., `MAGIC_RETURN = 0xDEAD`) to the CPU Stack and sets the `PC` to the user's compiled `start_addr`.
4. **Execution Hand-off:** Control is passed back to the core debugger. The debugger natively traces the user's code, handling breakpoints and generic UI highlighting, completely unaware that a monitor ROM context is paused in the background.

## 4. Organic Return & State Restoration
When the user program completes its logic, it executes a standard `RET` instruction.

1. **Trap Detection:** The `RET` pops the `MAGIC_RETURN` trap address into the Program Counter.
2. **Execution Halt:** The core debugger's `execute_batch` routine natively accepts an optional `stop_on_addr` parameter. The UI passes the `MAGIC_RETURN` address into this parameter. The moment the `PC` hits it, the debugger intentionally breaks the execution loop.
3. **State Reversion:** The UI detects the halt condition and invokes the plugin's `restore_context()` function. The plugin overwrites the CPU registers with the snapshot captured originally.
4. **Background Resumption:** The plugin unpauses its background hardware thread, waking up the monitor exactly where it left off, seamlessly blinking the prompt and awaiting new input.