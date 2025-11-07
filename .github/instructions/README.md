# GitHub Copilot Scoped Instructions

This directory contains scoped instruction files for different parts of the agentnav codebase. These files provide detailed, context-specific guidance to GitHub Copilot coding agent when working on different components of the project.

## Structure

Each `.instructions.md` file uses YAML frontmatter to specify which files or directories it applies to:

```yaml
---
applies_to:
  - backend/**/*
  - "*.py"
---
```

## Available Instructions

### 🐍 [backend.instructions.md](./backend.instructions.md)
**Applies to:** `backend/**/*`

Covers:
- Python/FastAPI development
- Google Agent Development Kit (ADK) usage
- Agent2Agent (A2A) Protocol
- Firestore integration
- Cloud Run compatibility requirements
- Backend testing requirements

### ⚛️ [frontend.instructions.md](./frontend.instructions.md)
**Applies to:** `*.tsx`, `*.ts`, `components/**/*`, `hooks/**/*`, `services/**/*`

Covers:
- React/TypeScript development
- Tailwind CSS styling (utility classes only)
- Three.js visualization (r128 constraints)
- State management (no localStorage)
- Frontend testing requirements
- Performance optimization

### 🏗️ [terraform.instructions.md](./terraform.instructions.md)
**Applies to:** `terraform/**/*`, `*.tf`, `scripts/deploy*.sh`

Covers:
- Terraform best practices
- GCP infrastructure components
- Cloud Run service configurations
- Workload Identity Federation (WIF)
- Workload Identity (WI)
- CI/CD pipeline
- Security and monitoring

### ✅ [testing.instructions.md](./testing.instructions.md)
**Applies to:** `**/*test*.py`, `**/*test*.ts`, `tests/**/*`

Covers:
- 70% test coverage mandate (non-negotiable)
- Backend testing with pytest
- Frontend testing with Vitest/React Testing Library
- Integration testing strategies
- Test fixtures and mocks
- Quality gates

## How It Works

When GitHub Copilot coding agent works on a file, it automatically loads the relevant scoped instructions based on the file path patterns in the YAML frontmatter. This provides:

1. **Context-Aware Assistance**: Copilot receives instructions specific to the code being worked on
2. **Modular Documentation**: Easier to maintain and update specific sections
3. **Better Performance**: Copilot can focus on relevant instructions instead of processing all instructions
4. **Clear Separation**: Different concerns are separated into different files

## Main Instructions

The repository also has a main instruction file at [`.github/copilot-instructions.md`](../copilot-instructions.md) that provides a high-level overview of the entire project. The scoped instructions here complement the main file with detailed, component-specific guidance.

## Custom Agents

For specialized tasks, see [`.github/agents/`](../agents/) directory for custom agent profiles.

## Best Practices

When adding new scoped instructions:
1. Use clear YAML frontmatter with specific file patterns
2. Keep instructions focused on a single component or concern
3. Provide code examples for common patterns
4. Document common pitfalls and solutions
5. Reference related files or documentation
6. Keep coverage requirements and quality standards visible

## References

- [GitHub Copilot Coding Agent Best Practices](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
- [Scoped Instructions Documentation](https://github.blog/changelog/2025-07-23-github-copilot-coding-agent-now-supports-instructions-md-custom-instructions/)
