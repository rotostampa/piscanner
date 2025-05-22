# piscanner

install uv

```
brew install uv
```

## run from cli

```run.sh ...```


## format the code

```uv run --isolated --no-project --with black black .```

## fixes

```uv run --isolated --no-project --with ruff ruff check --fix --unsafe-fixes .```