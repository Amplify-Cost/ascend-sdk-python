# Installation Guide

## Installation Methods

### Method 1: Install from PyPI (Recommended)

Once published to PyPI:

```bash
pip install ascend-ai-sdk
```

### Method 2: Install from Source (Development)

```bash
# Clone repository
git clone https://github.com/ascend-ai/ascend-sdk-python.git
cd ascend-sdk-python

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 3: Install from Local Directory

If you have the SDK source code locally:

```bash
cd /path/to/ascend-sdk-python
pip install .
```

## Requirements

- **Python**: 3.8 or higher
- **Dependencies** (automatically installed):
  - `requests>=2.28.0`
  - `python-dotenv>=1.0.0`

## Verify Installation

```python
import ascend
print(f"Ascend SDK version: {ascend.__version__}")

# Test connection
from ascend import AscendClient
client = AscendClient(api_key="your_key_here")
status = client.test_connection()
print(f"Connection: {status.status}")
```

Expected output:
```
Ascend SDK version: 1.0.0
Connection: connected
```

## Configuration

### Option 1: Environment Variables (Recommended)

```bash
export ASCEND_API_KEY="ascend_prod_your_key_here"
export ASCEND_API_URL="https://pilot.owkai.app"  # Optional
```

### Option 2: .env File

Create a `.env` file in your project root:

```env
ASCEND_API_KEY=ascend_prod_your_key_here
ASCEND_API_URL=https://pilot.owkai.app
ASCEND_DEBUG=false
```

### Option 3: Programmatic Configuration

```python
from ascend import AscendClient

client = AscendClient(
    api_key="ascend_prod_your_key_here",
    base_url="https://pilot.owkai.app",
    timeout=30,
    debug=False
)
```

## Development Installation

For SDK development and testing:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=ascend --cov-report=html

# Type checking
mypy ascend

# Code formatting
black ascend tests
```

## Troubleshooting

### Import Error

```python
ImportError: No module named 'ascend'
```

**Solution**: Ensure SDK is installed:
```bash
pip install ascend-ai-sdk
# or
pip install -e .
```

### API Key Error

```
ValidationError: API key is required
```

**Solution**: Set `ASCEND_API_KEY` environment variable:
```bash
export ASCEND_API_KEY="ascend_prod_..."
```

### Connection Error

```
NetworkError: Failed to connect to Ascend API
```

**Solutions**:
1. Check internet connection
2. Verify API URL is correct
3. Check firewall/proxy settings
4. Ensure SSL certificates are valid

### SSL Certificate Error

```
NetworkError: SSL/TLS certificate verification failed
```

**Solution**: Update certificates:
```bash
pip install --upgrade certifi
```

## Uninstallation

```bash
pip uninstall ascend-ai-sdk
```

## Support

- **Documentation**: https://docs.ascendai.app/sdk/python
- **GitHub Issues**: https://github.com/ascend-ai/ascend-sdk-python/issues
- **Email**: sdk@ascendai.app
