# Ring Ring 🔔💬

Slack bot that listens to Ring doorbell events and automatically sends video recordings to your Slack team channel. Built with the unofficial (reverse-engineered) [python-ring-doorbell](https://github.com/python-ring-doorbell/python-ring-doorbell) API library.

**NOTE:** At the moment you need to have at least a basic Ring subscription (the cheapest plan) assigned to the device you want to get video clips from. Otherwise, the bot won't be able to retrieve any recordings.

## Development 🛠️

- ### Requirements 📋

  - Python ([version](pyproject.toml#L4))

- ### Setup ⚙️

  - Clone the repository and open a terminal **inside** it.

  - Install the dependencies:

    ```shell
    # Creating a virtual environment is recommended before installing any project dependencies!
    pip install .
    ```

  - Create a `.env` file based on the [`.env.example`](.env.example) file.

  - Be aware that while Ring's authentication gives some leeway for code validity, you'll have to quickly start the bot after
  setting up the Ring OTP environment variable. If you don't have Ring 2FA enabled you **still** need to set this variable, but it can be any value, you won't need to worry about it.

  - Start the app:

    ```shell
    python src/bot.py
    ```

- ### Tooling 🧰

  - Ruff is used as a linter and formatter:

    ```shell
    pip install .[check]
    ruff check --fix
    ruff format

    # To automatically lint and format on every commit install the pre-commit hooks:
    pre-commit install

    # When using pre-commit hooks, commits may fail if files with errors are checked.
    # Changed files must be added to the staged area and commited again to apply fixes.
    # If you run into any issues just manually run the linter commands above to address them.
    ```

## Deployment 🚀

The bot is designed to run continuously as a Docker container.

- Supply the [required environment variables](.env.example) when running the container, just like in development.

- Start the container, e.g using the provided `docker-compose.yaml`:

  ```shell
  docker compose up
  ```

- Serve it using your server configuration of choice!
