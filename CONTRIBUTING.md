# Contributing to FluidNC LED Screen Monitor

Thank you for your interest in contributing to FluidNC LED Screen Monitor! This document provides guidelines and steps for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fluidnc-ledscreen.git
   cd fluidnc-ledscreen
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black isort pylint
   ```

## Code Style

This project follows these coding standards:
- Python code is formatted using Black
- Imports are sorted using isort
- Code is linted using pylint
- Maximum line length is 100 characters

Before submitting a PR, run:
```bash
black .
isort .
pylint **/*.py
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Run tests with:
  ```bash
  pytest
  ```

## Pull Request Process

1. Create a new branch for your feature/fix
2. Make your changes
3. Run tests and linting
4. Update documentation if needed
5. Submit a pull request

## Commit Messages

- Use clear, descriptive commit messages
- Reference issues when relevant
- Keep commits focused and atomic

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Keep documentation up to date

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing! 