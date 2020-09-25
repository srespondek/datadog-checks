# datadog-checks
Custom datadog checks

## Installation

1. Copy `<check>/<check>.py` to the [checks.d](http://docs.datadoghq.com/guides/agent_checks/#directory) directory.
2. Copy `conf.d/<check>.yaml.example` to `conf.d/dd-check-name/<check>.yaml`.
3. Edit `<check>.yaml` with appropriate values.
4. Restart the Datadog agent.
