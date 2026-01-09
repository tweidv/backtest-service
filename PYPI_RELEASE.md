# PyPI Release Guide

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
3. **Author Email**: Update `setup.py` with your email address (currently placeholder)

## Before Publishing

1. **Update Author Email** in `setup.py`:
   ```python
   author_email="your-email@example.com",  # Replace with your actual email
   ```

2. **Verify Version** in `setup.py` (currently `0.3.0`)

3. **Test the Build** (already done):
   ```bash
   python -m build
   ```

4. **Check Package Contents**:
   ```bash
   python -m twine check dist/*
   ```

## Publishing to PyPI

### Test PyPI (Recommended First Step)

1. Create account at https://test.pypi.org/account/register/
2. Upload to Test PyPI:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```
3. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ backtest-service
   ```

### Production PyPI

Once tested, upload to production PyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

## Post-Release

1. **Create GitHub Release**: Tag the version and create a release on GitHub
2. **Update Documentation**: Update any docs that reference installation instructions
3. **Announce**: Share the release on relevant channels

## Version Bumping

For future releases, update the version in `setup.py`:
- Patch: `0.3.0` → `0.3.1` (bug fixes)
- Minor: `0.3.0` → `0.4.0` (new features)
- Major: `0.3.0` → `1.0.0` (breaking changes)

## Notes

- The package name on PyPI will be `backtest-service` (hyphenated)
- Installation: `pip install backtest-service`
- Import: `from backtest_service import DomeBacktestClient`

