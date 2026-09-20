# Install

Set the repository up so it can be built and tested locally.

## Read
- `README.md`, setup and prerequisites sections
- `.env.sample`, `.env.example` or equivalent, if present. Never read `.env`.

## Run
- Install dependencies with the tool the repo already uses (`uv sync`, `npm install`, `bun install`, `make install`). Follow the README, do not guess a tool the repo does not use.
- If a sample env file exists and `.env` does not, copy the sample to `.env`. Do not fill in secrets.
- Run the project's test command once, if there is one, to confirm the setup works.

## Report
- What you installed, as a bullet list.
- The exact command that runs the tests.
- What the user must do by hand: secrets to fill in, services to start.
