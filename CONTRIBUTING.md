# Contributing to FitFindr

Thank you for your interest in contributing to FitFindr! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/FitFindr.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use meaningful variable names

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for > 80% code coverage

## Pull Request Process

1. Update README.md with details of changes if needed
2. Update requirements.txt if you add dependencies
3. Ensure all tests pass
4. Request review from maintainers

## Reporting Bugs

- Use GitHub Issues
- Include detailed description
- Provide steps to reproduce
- Include error messages and logs
- Specify your environment (OS, Python version, etc.)

## Feature Requests

- Use GitHub Issues
- Clearly describe the feature
- Explain why it would be useful
- Provide examples if possible

## Questions?

Feel free to open an issue for any questions!
