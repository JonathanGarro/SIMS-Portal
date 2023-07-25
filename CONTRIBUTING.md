# Contributing

## Setting up a development environment

- Make sure you have an integrated development environment (IDE) installed. Some options include: [Microsoft Visual Studio Code](https://code.visualstudio.com/?wt.mc_id=DX_841432), [Kate](https://kate-editor.org/), or [Pulsar](https://pulsar-edit.dev/).
- Clone the https://github.com/JonathanGarro/SIMS-Portal repository. Suggested to use [GitHub Desktop](https://desktop.github.com/).
- Download and install [Docker](https://www.docker.com/) (note that if you're running macOS you'll need to correctly select either the Intel Chip or Apple Chip version).
- Install PostgreSQL. You can follow this guide: https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/
- Using a virtual environment will keep your Python packages for this project isolated from the packages you might be using elsewhere on your computer for different projects. The full docs are at: https://docs.python.org/3/library/venv.html
	- You want to `cd` into the top of the repo (when you `ls` you should see just the readme and flask_app directory).
	- Then run `python -m venv venv` (the second `venv` is just whatever you want to call the directory locally, but since our `.gitignore` is configured to exclude the folder with that name from the repository you'll want to use `venv`). If you're on macOS and get a "command not found" error, you might need to run `python3 -m venv venv` instead.
	- Run `source venv/bin/activate` to activate the environment. **NOTE:** You will need to activate the environment every time you start in a new terminal window.

## Fetching sensitive environment variables

_Note that this process will likely change as the number of contributors grows and the platform matures._

- Sensitive environment variables are stored using [dotenv](https://www.dotenv.org/) and not committed to GitHub.
- If we have seats on our free Dotenv account, you'll request access from Jonathan and follow the rest of the steps. Otherwise, Jonathan will need to privately transfer the contents to you. Then you can create a `.env` file inside the `./flask_app/` folder and skip the rest of this section.
- On macOS, if you haven't already you'll probably want to install:
	- `oh-my-zsh` - It makes doing things in your terminal shell easier. Follow the instruction at https://ohmyz.sh/
	- `homebrew` - It helps manage the software packages. Follow the instructions at https://brew.sh/ 
- You will need Node.js to run the commands to fetch the file. Suggested that you use a version manager to run Node.js in case your work on different projects that require different versions. Since we're just using it to pull the `.env` file, the version shouldn't matter (LTS or latest should both work)
	- `nvm` is good for just Node.js and can be installed following the instructions at https://github.com/nvm-sh/nvm#about
	- `asdf` is a version manager with plugins for multiple tools (not just Node.js) and can be installed following the instructions at https://asdf-vm.com/guide/introduction.html (you'll need to follow all 6 steps in Getting Started to both install `asdf` and the `asdf-nodejs` plugin)
- When you install Node.js it will also install npm (a command line client for developers to install and publish packages of code), letting you use the [`npx`](https://docs.npmjs.com/cli/v9/commands/npx) command in the next step to run a command from a package fetched remotely. 
- Follow the [dotenv docs](https://www.dotenv.org/docs/dotenv-vault/pull.html) to pull the `.env` file. It should create a populated `.env` file inside of the `flask_app` directory.
	```
	cd flask_app
	npx dotenv-vault login
	npx dotenv-vault@latest pull
	```

## Running the SIMS Portal

- When you’re ready to run the SIMS Portal, use `docker-compose up --build` (it can take several minutes to complete the first time you run the command but should be much faster subsequent times).
- If you want to access the real data in the production database, let Jonathan know. As long as you’re only doing SELECTs and no updates/deletes, it may be useful to test your queries. Access to the database is locked down to specific IP addresses. The process for granting access is [documented here](https://learn-sims.org/docs/sims-portal-documentation/administrator-backend-controls-461/#direct-database-access).

## Populating the local database

- For testing certain functionalities it will be necessary to have data in the tables of your local PostgreSQL database (installed when you setup your development environment, and configured when you ran the `docker-compose` command to start the portal).
- You'll need a program to interact with PostgreSQL. [pgAdmin](https://www.pgadmin.org/) is a FOSS option available on Linux, Unix, macOS and Windows.
- Jonathan can send you files to import. For example `user.csv` and `nationalsociety.csv` files.
- With the portal running, open your PostgreSQL management program and import the files to populate the matching tables. In pgAdmin...
 	- Right click "Servers" in the left hand "Object Explorer" navigation and select "Register" then "Server..." to open a "Register - Server" popup window.
	- Under "General" set "Name" to "SIMS-Portal" (this is only for your own recognition purposes). Under connection set "Host name/address" to "localhost", change "Username" to "simsportal", and set "Password" to "simsportal" (see the `./flask_app/docker-compose.yml` file for these values). You can also turn on "Save password?". Press "Save" in the lower right of the popup window.
	- The "Servers" navigation list should now have "SIMS-Portal" as an entry.
	- Expand "SIMS-Portal" then "Databases" then "simsportal" then "Schemas" then "Tables". 
	- Find the table name that matches the file - for example, "nationalsociety" for `nationalsociety.csv` - right click the table name and select "Import/Export Data..." to open a popup window.
	- Under "General" set the "Filename" to the path to your matching file via the file browser. Check that the "Format" is "csv" and set "Encoding" to "UTF8". Under "Options" turn on "Header" and set "NULL Strings" to "NULL". Under "Columns" you should see "Columns to import" pre-populated with the values from the data file's header row. Press "OK" in the lower right of the popup window.
	- The import attempt should appear as an entry in the "Processes" tab for the database. If it failed, you can click the icon in the column before the PID column to "View details" and troubleshoot.
	- If successful you can test by finding the icon in the top nav bar for the "Query Tool", opening it, and running something like `SELECT * from nationalsociety`. It should show the table contents in the "Data Output" pane. After typing `SELECT * FROM ` (with a trailing space), you can press Control+Space to select from a popup menu of autocomplete suggestions.

## Managing Docker

- When you make changes and want to view them, you'll need to stop the Docker container and rebuild it. 
- When you rebuild a container, the old one stays on your system and takes up disk space. You will want to periodically purge these from Docker to avoid system bloat. To do so, open your terminal and run `docker system prune`, then `y` to confirm (be careful if you are using docker for other projects as this can impact those).
