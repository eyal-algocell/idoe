# iDoE Planner - Usage Guide

## Overview

The iDoE (Intensified Design of Experiments) Planner is a MILP-based optimizer that reduces the number of experiments needed for Design of Experiments (DoE) studies by intelligently combining multiple experimental conditions into sequential stages within single experiments.

## Architecture

The codebase is organized following best practices:

```
idoe/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── config.py         # Configuration constants
│   ├── models.py         # Data models
│   ├── optimizer.py      # MILP optimizer implementation
│   └── main.py           # CLI entry point
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Pytest configuration
│   ├── test_config.py    # Config tests
│   ├── test_models.py    # Model tests
│   ├── test_optimizer.py # Optimizer tests
│   └── test_e2e.py       # End-to-end tests
├── Dockerfile            # Application container
├── Dockerfile.test       # Test container
├── docker-compose.yml    # Docker orchestration
├── requirements.txt      # Python dependencies
└── pytest.ini           # Pytest configuration
```

## Running Locally

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Run the Optimizer

```bash
# Basic usage (prints to console)
python -m src.main

# Save results to a file
python -m src.main --output output/results.json

# Verbose mode (shows solver output)
python -m src.main --verbose
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_optimizer.py

# Run with verbose output
pytest -v
```

## Running with Docker

### Build and Run Application

```bash
# Build the application image
docker build -t idoe-app .

# Run the application
docker run --rm -v $(pwd)/output:/app/output idoe-app

# Check the results
cat output/results.json
```

### Build and Run Tests

```bash
# Build the test image
docker build -f Dockerfile.test -t idoe-test .

# Run tests and save results
docker run --rm -v $(pwd)/test-results:/app/test-results idoe-test

# Check test results
cat test-results/status.txt
cat test-results/junit.xml
```

### Using Docker Compose

```bash
# Run the application
docker-compose up app

# Run tests
docker-compose up test

# Run both (in parallel)
docker-compose up

# Clean up
docker-compose down
```

## Output Format

The optimizer produces a JSON file with the following structure:

```json
{
  "status": "Optimal",
  "objective_value": 0.123456,
  "num_experiments_used": 5,
  "num_stages_used": 15,
  "experiments": [
    {
      "experiment_id": 1,
      "stages": [
        {
          "stage": 1,
          "combination": 9,
          "mu_set": 0.1225,
          "temperature": 33.0
        },
        {
          "stage": 2,
          "combination": 6,
          "mu_set": 0.11,
          "temperature": 31.0
        },
        {
          "stage": 3,
          "combination": 6,
          "mu_set": 0.11,
          "temperature": 31.0
        }
      ]
    }
  ]
}
```

## Configuration

You can modify the optimizer parameters by editing [src/config.py](src/config.py):

- `FACTOR_VALUES`: DOE combinations (mu_set, temperature)
- `NUM_STAGES`: Number of stages per experiment (default: 3)
- `DELTA_F_MAX_MU`: Maximum mu_set change between stages (default: 0.03)
- `DELTA_F_MAX_TEMP`: Maximum temperature change between stages (default: 2°C)
- `DELTA_F_MIN_MU`: Minimum mu_set change per experiment (default: 0.01)
- `DELTA_F_MIN_TEMP`: Minimum temperature change per experiment (default: 1°C)

## Constraints

The optimizer implements the following constraints:

- **C1**: One DOE combination per stage of an experiment
- **C2**: Each combination appears at most once at any stage position
- **C3**: Each combination used at most twice per experiment
- **C4**: Each combination used at most twice globally
- **C5**: All combinations must be used at least once
- **C6**: Weighted stage repetition for strategic distribution
- **C7**: Sequential change limits between stages
- **C8**: Minimum variation per experiment

## Testing

The test suite includes:

- **Unit tests**: Test individual components (config, models)
- **Integration tests**: Test the optimizer with various scenarios
- **E2E tests**: Test the complete workflow including CLI and file I/O

Test results are saved in multiple formats:
- `junit.xml`: JUnit format for CI/CD integration
- `coverage.json`: Coverage data in JSON format
- `coverage/`: HTML coverage report
- `status.txt`: Simple status indicator

## Troubleshooting

### Solver Issues

If the solver fails to find a solution:
1. Check that constraints are not over-constrained
2. Adjust delta limits in config.py
3. Enable verbose mode to see solver output

### Docker Issues

If Docker containers fail:
```bash
# Check Docker logs
docker logs idoe-app
docker logs idoe-test

# Rebuild without cache
docker-compose build --no-cache
```

### Test Failures

If tests fail:
```bash
# Run tests with verbose output
pytest -v

# Run a specific test
pytest tests/test_optimizer.py::TestIDOEOptimizer::test_optimize_status_optimal -v
```
