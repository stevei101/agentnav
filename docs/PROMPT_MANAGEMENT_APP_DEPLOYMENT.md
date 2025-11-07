# Prompt Vault Deployment (Archived)

> **Status:** November 2025 – The Prompt Management application now lives in the dedicated repository [`stevei101/prompt-vault`](https://github.com/stevei101/prompt-vault).

The content that previously described deploying the Prompt Management App from this
repository has been archived. Provisioning, secrets management, and CI/CD automation
for Prompt Vault are now owned entirely by the new project. Use the following
references instead:

- Prompt Vault README: <https://github.com/stevei101/prompt-vault#readme>
- Prompt Vault Quick Start: <https://github.com/stevei101/prompt-vault/blob/main/QUICK_START.md>
- Shared infrastructure patterns: <https://github.com/stevei101/infrastructure>

## Integration with AgentNav

- AgentNav no longer hosts Supabase credentials nor the Prompt Vault Cloud Run
  blueprint.
- Prompt Vault communicates with AgentNav through the public `/api/prompt-*`
  routes secured by Workload Identity Federation. See
  `services/agentNavigatorClient.ts` in the Prompt Vault repo for the current
  client helper.
- Cursor IDE exports are handled in the standalone
  [`stevei101/cursor-ide`](https://github.com/stevei101/cursor-ide) repository,
  which includes tooling for syncing prompts into Prompt Vault.

## Historical Reference

If you need to review the previous Terraform definitions or Supabase instructions,
consult the git history prior to commit `feat: bootstrap prompt vault repository`
(in the Prompt Vault repo) or the `chore/prettier-ignore-docs` branch history in
AgentNav before the Prompt Vault split.
