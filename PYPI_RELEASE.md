# PyPI Release Guide

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
3. **Author Email**: Already configured in `setup.py`

## Before Publishing

1. **Update Author Email** in `setup.py`: Already set to `tweidevrieze@gmail.com`

2. **Verify Version** in `setup.py` (currently `0.1.0`)

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
   pip install --index-url https://test.pypi.org/simple/ emulo-backtest
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
- Patch: `0.1.0` → `0.1.1` (bug fixes)
- Minor: `0.1.0` → `0.2.0` (new features)
- Major: `0.1.0` → `1.0.0` (breaking changes)

## Notes

- The package name on PyPI will be `emulo-backtest` (hyphenated)
- Installation: `pip install emulo-backtest`
- Import: `from emulo import DomeBacktestClient`

