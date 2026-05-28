# Contributing to OnTrack

Thank you for your interest in contributing to OnTrack! Here are some guidelines to help you get started.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone git@github.com:YOUR_USERNAME/OnTrack.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Run tests**: `cd dashboard && python test_components.py`
6. **Commit with clear messages**: `git commit -m "Add feature: description"`
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Create a Pull Request** on the main repository

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add type hints where possible (Python 3.8+)
- Keep functions focused and testable

## Testing

All changes should:
- Pass the existing test suite: `python test_components.py`
- Include tests for new functionality
- Not break any existing tests

## Documentation

- Update README.md if adding features
- Update DEVELOPER_GUIDE.md for architectural changes
- Add docstrings to new functions/classes
- Keep docs in sync with code changes

## Areas for Contribution

### Easy (Good for first-timers)
- Documentation improvements
- Bug fixes with clear reproduction steps
- Code comments and clarification
- Adding more test coverage

### Medium
- New widgets for additional telemetry
- Configuration options and settings
- Performance improvements

### Advanced
- Network protocol improvements
- Cross-platform compatibility
- CI/CD enhancements
- Plugin compatibility with other simulators

## Reporting Bugs

Before creating a bug report:
- Check existing issues
- Test with the latest code
- Provide reproduction steps
- Include your OS, Python version, PyQt6 version

Use the Bug Report template when creating issues.

## Feature Requests

For feature requests:
- Describe the use case
- Explain why it would be useful
- Provide context and examples
- Be open to discussion

Use the Feature Request template when creating issues.

## Code Review

All pull requests will be reviewed by maintainers. Changes might be requested before merging. This is normal and helps maintain code quality.

## License

By contributing to OnTrack, you agree that your contributions will be licensed under the same license as the project.

## Questions?

Feel free to:
- Open a discussion on GitHub
- Check existing documentation (README.md, DEVELOPER_GUIDE.md)
- Create an issue with the "question" label

Thank you for contributing! 🎉
