---
name: Good First Issue
about: Create a beginner-friendly issue for new contributors
title: '[Good First Issue] '
labels: good first issue, help wanted, contribution
assignees: ''
---

# Good First Issue: [Brief Title]

**Difficulty:** 🟢 Beginner  
**Estimated Time:** [e.g., 1-2 hours]  
**Prerequisites:** [e.g., Basic TypeScript knowledge, familiarity with React]

## 📋 Issue Description

[Provide a clear, concise description of what needs to be done. Focus on a single, well-defined task that is achievable by someone new to the project.]

## 🎯 Goal

[Explain what the successful completion of this issue will accomplish. What problem does it solve or what improvement does it provide?]

## 🛠️ Technical Context

### Relevant Files

- `path/to/file1.ext` - [Brief description of what this file does]
- `path/to/file2.ext` - [Brief description of what this file does]

### Technologies Used

- [List the specific technologies, frameworks, or tools involved]
- [e.g., React, TypeScript, FastAPI, etc.]

### Architecture Notes

[Provide brief context about how this fits into the overall system architecture. Reference relevant documentation if needed.]

## ✅ Acceptance Criteria

- [ ] [Specific, measurable criterion 1]
- [ ] [Specific, measurable criterion 2]
- [ ] [Specific, measurable criterion 3]
- [ ] All existing tests pass
- [ ] New tests added (if applicable) with **70% or higher code coverage**
- [ ] Code follows project style guidelines (passes `make lint`)
- [ ] Documentation updated (if applicable)

## 📚 Helpful Resources

### Documentation

- [System Instruction](../../docs/SYSTEM_INSTRUCTION.md) - Complete system architecture and conventions
- [Contribution Guide](../../CONTRIBUTING.md) - How to contribute to the project
- [Local Development Setup](../../docs/local-development.md) - Setting up your development environment
- [Copilot Agent Guide](../../docs/COPILOT_AGENT_GUIDE.md) - Using the agentnav-copilot-agent for assistance

### Related Code Examples

- [Link to similar implementation in the codebase]
- [Link to relevant test file for reference]

### External References

- [Link to relevant external documentation, if any]

## 🚀 Getting Started

1. **Set up your development environment:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/agentnav.git
   cd agentnav
   make setup
   ```

2. **Create a feature branch:**

   ```bash
   git checkout -b fix/good-first-issue-[issue-number]
   ```

3. **Run the application locally:**

   ```bash
   # Frontend
   bun install
   bun run dev

   # Backend (if needed)
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   PORT=8080 uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Make your changes** following the acceptance criteria

5. **Test your changes:**

   ```bash
   make ci  # Run all checks (lint + tests)
   ```

6. **Submit a pull request** with a clear description of your changes

## 💡 Implementation Hints

[Provide helpful hints or guidance on how to approach the problem. Don't give away the complete solution, but point contributors in the right direction.]

### Step-by-step Approach:

1. [First step to take]
2. [Second step to take]
3. [Third step to take]

### Things to Keep in Mind:

- [Important consideration 1]
- [Important consideration 2]
- Remember: All new code must have **70% or higher test coverage**
- Use the **agentnav-copilot-agent** (@agentnav-gh-copilot-agent in GitHub) for context-aware assistance

## ❓ Need Help?

- **Ask questions in the comments below** - Don't hesitate to ask for clarification!
- **Use the agentnav-copilot-agent** - Invoke `@agentnav-gh-copilot-agent` in your comments for instant, context-aware guidance on:
  - Project architecture and conventions
  - Code generation following our patterns (RORO, TypeScript, ADK)
  - Testing best practices and coverage requirements
  - Cloud Run deployment considerations
- **Check the documentation** - Most common questions are answered in the docs
- **Join the discussion** - Connect with other contributors in the issue thread

## 🎉 First-Time Contributors

Welcome! This issue is specifically designed for people who are new to the project. We're here to help you make your first contribution. Don't be afraid to ask questions!

### What You'll Learn:

- [Skill or concept 1 you'll learn by completing this issue]
- [Skill or concept 2 you'll learn by completing this issue]
- Working with the agentnav multi-agent architecture
- Following professional code quality standards (70% test coverage, linting, type safety)

---

**Note:** Before starting work, please comment on this issue to let others know you're working on it. This helps prevent duplicate efforts.
