# Contributing to Agentic Navigator

Thank you for your interest in contributing to Agentic Navigator! We welcome contributions from the community.

## License

By contributing to Agentic Navigator, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentnav.git
   cd agentnav
   ```
3. **Set up your development environment**:
   ```bash
   make setup
   ```
   See [docs/local-development.md](docs/local-development.md) for detailed setup instructions.

## Development Workflow

### 1. Create a Branch

Create a feature branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:

- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation updates
- `refactor/` for code refactoring

### 2. Make Your Changes

- Write clean, readable code that follows the project's style guidelines
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

Before submitting, ensure all tests pass:

```bash
# Run all tests
make test

# Run frontend tests
bun run test

# Run backend tests
pytest backend/tests

# Run linting
bun run lint
bun run format:check
```

**⚠️ CRITICAL: Zero-Tolerance CI Failure Policy**

If any CI check fails during or after your PR submission:

1. **Stop all other work immediately**
2. **Search for an existing open, assigned issue** tracking this failure
3. **If no issue exists, create a new Feature Request immediately** using the template in [docs/ZERO_TOLERANCE_FAILURE_POLICY.md](docs/ZERO_TOLERANCE_FAILURE_POLICY.md)
4. **Assign appropriate priority and owner** to the new FR
5. **Do not merge or bypass the failed check** without explicit maintainer approval

See the complete [Zero-Tolerance Failure Policy](docs/ZERO_TOLERANCE_FAILURE_POLICY.md) for detailed procedures.

### 4. Commit Your Changes

Follow these commit message guidelines:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:

```
Add GPU acceleration for Gemma model inference

- Implement CUDA support for faster inference
- Add GPU memory management
- Update documentation with GPU requirements

Fixes #123
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Submit a Pull Request

1. Go to the [Agentic Navigator repository](https://github.com/stevei101/agentnav)
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the pull request template with:
   - A clear description of the changes
   - Any related issues
   - Screenshots for UI changes
   - Testing performed

## Contribution Guidelines

### PR Discipline and Minimum Viable Commit

**Before submitting a Pull Request**, please read our comprehensive guide on **PR Discipline and Minimum Viable Commit (MVC)** principles:

📖 **[Contribution Guide: PR Discipline](docs/CONTRIBUTION_GUIDE_PR_DISCIPLINE.md)**

Key principles:

- Only commit files that are **consumed** by the application, CI/CD, or IaC
- Remove temporary notes, scratch files, and local configuration
- Optimize `.dockerignore` and `.gitignore` to minimize build context
- Run `make ci` before requesting review

### Code Style

**Frontend (TypeScript/React):**

- Use TypeScript for type safety
- Follow the existing code style
- Use functional components with hooks
- Run `bun run lint` and `bun run format` before committing

**Backend (Python):**

- Follow PEP 8 style guide
- Use type hints
- Run `black`, `isort`, and `ruff` before committing
- Keep functions focused and well-documented

### Testing

- Write unit tests for new functionality
- Ensure all existing tests pass
- Aim for high test coverage
- Test edge cases and error conditions

### Documentation

- Update README.md if adding user-facing features
- Add docstrings to new functions and classes
- Update relevant documentation in the `docs/` directory
- Include code examples where appropriate

### Multi-Agent Architecture

When working with the multi-agent system:

- **Agent Definitions**: Place agent configurations in `backend/agents/`
- **A2A Protocol**: Use the Agent2Agent Protocol for inter-agent communication
- **Firestore**: Store agent state and session data in Firestore
- **ADK Integration**: Follow Google ADK best practices

See [docs/SYSTEM_INSTRUCTION.md](docs/SYSTEM_INSTRUCTION.md) for architectural details.

### Cloud Run Compatibility

Ensure code changes are compatible with Cloud Run:

- Read `PORT` environment variable (Cloud Run sets this automatically)
- Implement `/healthz` endpoint for health checks
- Use `0.0.0.0` as host binding (not `127.0.0.1`)
- Log to stdout/stderr
- Handle SIGTERM gracefully for clean shutdowns

## Reporting Bugs

If you find a bug, please create an issue on GitHub with:

1. **Clear title**: Describe the bug concisely
2. **Description**: Detailed description of the issue
3. **Steps to reproduce**: Minimal steps to reproduce the bug
4. **Expected behavior**: What should happen
5. **Actual behavior**: What actually happens
6. **Environment**: OS, browser, versions, etc.
7. **Screenshots**: If applicable
8. **Logs**: Relevant error messages or logs

**⚠️ CI/CD Failures:** If the bug is a failed GitHub Actions CI check, you **MUST** follow the [Zero-Tolerance Failure Policy](docs/ZERO_TOLERANCE_FAILURE_POLICY.md) and create a Feature Request immediately with full log output and root cause analysis.

## Requesting Features

For feature requests, please create an issue with:

1. **Clear title**: Describe the feature concisely
2. **Problem**: What problem does this feature solve?
3. **Solution**: Describe your proposed solution
4. **Alternatives**: Any alternative solutions considered
5. **Context**: Additional context or use cases

## Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

Please report security vulnerabilities to the maintainers privately. See [docs/SECURITY.md](docs/SECURITY.md) for details.

## Community

- Be respectful and inclusive
- Help others in discussions
- Share knowledge and best practices
- Give constructive feedback
- Celebrate successes together

## Questions?

If you have questions about contributing, feel free to:

- Open an issue with the `question` label
- Check existing documentation in the `docs/` directory
- Review closed issues for similar questions

## Thank You!

Your contributions help make Agentic Navigator better for everyone. We appreciate your time and effort! 🚀
