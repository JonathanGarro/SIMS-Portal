# Contributing

## Setting up a development environment

- Make sure you have an integrated development environment (IDE) installed. Some options include: [Microsoft Visual Studio Code](https://code.visualstudio.com/?wt.mc_id=DX_841432), [Kate](https://kate-editor.org/), or [Pulsar](https://pulsar-edit.dev/).
- Clone the https://github.com/JonathanGarro/SIMS-Portal repository. Suggested to use [GitHub Desktop](https://desktop.github.com/).
- Download and install [Docker](https://www.docker.com/) (note that if you're running macOS you'll need to correctly select either the Intel Chip or Apple Chip version).
- Sensitive environment variables are stored using [dotenv](https://www.dotenv.org/) and not committed to GitHub.
  - You'll need to request account access from Jonathan.
  - To pull the .env file from dotenv you'll need to install [Node.js](https://nodejs.org/). Suggested to use [asdf](https://asdf-vm.com/) or [nvm](https://github.com/nvm-sh/nvm#readme) - both of which allow you to easily manage and use different versions of Node.js for different projects.
  - When you install Node.js it will also install npm (a command line client for developers to install and publish packages of code), letting you use the [`npx`](https://docs.npmjs.com/cli/v9/commands/npx) command  in the next step to run a command from a package fetched remotely.
  - Follow the [dotenv docs](https://www.dotenv.org/docs/dotenv-vault/pull.html) to pull the `.env` file. It should create a `.env` file inside of the `flask_app` directory.
    ```
    cd flask_app
    npx dotenv-vault@latest pull
    ```
- Using a virtual environment will keep your Python packages for this project isolated from the packages you might be using elsewhere on your computer for different projects. The full docs are at: https://docs.python.org/3/library/venv.html
  - You want to `cd` into the top of the repo (when you `ls` you should see just the readme and flask_app directory).
  - Then run `python -m venv venv` (the second `venv` is just whatever you want to call the directory locally, but since our `.gitignore` is configured to exclude the folder with that name from the repository you'll want to use `venv`). If you're on macOS and get a "command not found" error, you might need to run `python3 -m venv venv` instead.
  - Run `source venv/bin/activate` to activate the environment.

- Install PostgreSQL. You can follow this guide: https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/
- When you’re ready to run the SIMS Portal, use `docker-compose up --build` (it can take several minutes to complete the first time you run the command but should be much faster subsequent times).
- If you want to access the real data in the production database, let Jonathan know. As long as you’re only doing SELECTs and no updates/deletes, it may be useful to test your queries. Access to the database is locked down to specific IP addresses. The process for granting access is [documented here](https://learn-sims.org/docs/sims-portal-documentation/administrator-backend-controls/#direct-database-access).

## Managing Docker

- When you make changes and want to view them, you'll need to stop the Docker container and rebuild it. 
- When you rebuild a container, the old one stays on your system and takes up disk space. You will want to periodically purge these from Docker to avoid system bloat. To do so, open your terminal and run `docker system prune`, then `y` to confirm (be careful if you are using docker for other projects as this can impact those).

