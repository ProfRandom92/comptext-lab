# Provider Configuration Layer (Phase 7)

`ctxt` supports repository-local and user-supplied configuration files formatted in TOML to define default execution flags, provider profiles, and network policies.

## Config File Resolution

When executing commands, the configuration path is resolved in the following priority order:
1. Custom path specified via the global `--config <path>` command-line option.
2. Default repository-local configuration `comptext.toml` in the working directory.
3. Fallback repository-local configuration `comptext.example.toml` in the working directory.

## TOML Schema Structure

The configuration file supports three main tables:

### 1. `[defaults]`
* **`provider`** (string): The default provider profile name to use when no `--provider` parameter is specified in commands.
* **`dry_run_default`** (boolean): Default dry-run behavior for actions.
* **`proposal_required`** (boolean): Enforces checking proposal artifacts prior to executing code mutations.

### 2. `[providers.<profile-name>]`
* **`kind`** (string): The adapter kind (e.g. `"dummy"`, `"ollama"`, or `"openai-compatible"`).
* **`network`** (boolean, optional): Determines if the provider profile requires active network sockets.
* **`base_url`** (string, optional): Base endpoint for local or direct cloud providers.
* **`auth`** (string, optional): Auth mode metadata description (e.g., `"none"` or `"ollama_signin"`).
* **`auth_env`** (string, optional): The name of the environment variable containing the API credential (never the key itself).
* **`model_suffix`** (string, optional): A suffix to append to requested models.

### 3. `[policy]`
* **`network_default`** (string): Default network gate behavior (e.g. `"deny"`).
* **`allow_provider_network`** (boolean): Restricts provider execution from initializing network connections.
* **`secrets_redaction`** (boolean): Enforces secret redaction on Context Pack artifacts.
* **`apply_requires_confirmation`** (boolean): Forces manual human-in-the-loop confirmation before applying proposals.

---

## Example Usage

### View Available Profiles
```bash
ctxt providers list
```

### View Config Diagnostics
```bash
ctxt doctor
```

### Override Config Path
```bash
ctxt --config path/to/my_config.toml ask "How do I build this project?"
```
