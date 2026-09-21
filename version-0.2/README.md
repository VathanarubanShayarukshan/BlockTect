# Magiccode 4.0 and Scratch GUI: Version 2 Guide

This folder contains the planning and user documentation for Magiccode version 2.
The editable Scratch block editor used by this project is in a separate checkout:

```text
/workspaces/BlockTect/developer_data/scratch-gui
```

That checkout is the open-source Scratch GUI project. It is a React/Webpack
development application, so run it from its own directory rather than from
`version-2`.

## Quick Start

### Requirements

- Linux, macOS, or Windows with a terminal
- Git
- Node.js and npm
- A modern web browser

The current checkout was tested with Node.js 24 and npm 11. The repository also
contains a `.nvmrc`; use the version specified there if another Node.js version
causes dependency or build errors.

### Start the Scratch GUI

Open a terminal and run:

```bash
cd /workspaces/BlockTect/developer_data/scratch-gui
npm install
npm start
```

`npm install` is needed only when dependencies are missing or after the lockfile
or package contents change. Because `node_modules` is already present in the
current workspace, the server can also be started directly with `npm start`.

When webpack finishes its first compilation, open:

```text
http://localhost:8601/
```

The development server reloads the page when source files change. Keep the
terminal open while using the application. Stop it with `Ctrl+C`.

### Use another port

Port `8601` is the default. If it is already in use, select another port:

```bash
cd /workspaces/BlockTect/developer_data/scratch-gui
PORT=8602 npm start
```

Then open `http://localhost:8602/`.

## What Is Available

The default page is the Scratch GUI playground. The same development server
also builds these example pages:

| Page | URL |
| --- | --- |
| Main GUI | `http://localhost:8601/` |
| Blocks only | `http://localhost:8601/blocks-only.html` |
| Compatibility testing | `http://localhost:8601/compatibility-testing.html` |
| Player | `http://localhost:8601/player.html` |

These pages are development examples, not a production deployment of
Magiccode. Magiccode-specific conversion and download behavior must be added in
the application code that uses this GUI.

## Important Folders

```text
/workspaces/BlockTect/
├── developer_data/
│   ├── Magiccode 3.0.html       # Existing Magiccode reference/app file
│   └── scratch-gui/              # Editable Scratch GUI source
└── version-2/
    ├── README.md                 # This guide
    └── prompt.txt                # Version-2 project requirements
```

Within `scratch-gui`:

```text
src/                              # React, Redux, and Scratch GUI source
src/playground/                   # Development example entry points
src/components/                   # Reusable interface components
src/reducers/                     # Application state reducers
static/                           # Static assets
build/                            # Generated development build output
test/                             # Unit, integration, and smoke tests
package.json                      # Commands and dependencies
webpack.config.js                 # Dev-server and build configuration
```

Do not edit generated files in `build/` when changing the GUI. Edit files under
`src/` and let webpack rebuild them.

## Common Commands

Run all commands from the Scratch GUI directory:

```bash
cd /workspaces/BlockTect/developer_data/scratch-gui
```

| Command | Purpose |
| --- | --- |
| `npm start` | Start the development server on port 8601 |
| `PORT=8602 npm start` | Start on a different port |
| `npm run build` | Create a development build in `build/` |
| `BUILD_MODE=dist npm run build` | Also create the distributable library in `dist/` |
| `npm run clean` | Remove generated `build/` and `dist/` folders |
| `npm run test:lint` | Run ESLint |
| `npm run test:unit` | Run unit tests |
| `npm run test:smoke` | Run smoke tests |
| `npm run test:integration` | Run browser integration tests |
| `npm test` | Run linting, unit tests, build, and integration tests |

## Recommended Development Workflow

1. Start `npm start` in the Scratch GUI directory.
2. Open `http://localhost:8601/` in a browser.
3. Make source changes under `developer_data/scratch-gui/src/`.
4. Refresh the browser if the automatic reload does not update the page.
5. Run the narrowest relevant test, such as `npm run test:unit`.
6. Run `npm test` before sharing a larger change.

## Building Without the Dev Server

To generate the browser build manually:

```bash
cd /workspaces/BlockTect/developer_data/scratch-gui
npm run build
```

The generated files are placed in `build/`. To serve that output without
webpack, use a static server from the GUI directory:

```bash
cd /workspaces/BlockTect/developer_data/scratch-gui/build
python3 -m http.server 8000
```

Open `http://localhost:8000/` after the server starts.

## Testing Notes

Unit tests do not require a browser:

```bash
npm run test:unit
```

Integration tests require a completed build and a compatible Chrome or Chromium
installation. Run:

```bash
npm run build
npm run test:integration
```

For a visible browser during an integration test, set `USE_HEADLESS=no` before
the Jest command. The full `npm test` command can take longer because it runs
linting, unit tests, a build, and integration tests together.

## Troubleshooting

### `npm: command not found`

Install Node.js and npm, reopen the terminal, and check:

```bash
node --version
npm --version
```

### The page does not open

Confirm that the terminal still contains the running `webpack serve` process.
Look for the message showing `http://localhost:8601/`. If the port is busy,
start with `PORT=8602 npm start` and use the matching URL.

### Dependencies are missing or broken

From the GUI directory, reinstall from the lockfile:

```bash
npm ci
```

If the installation fails because of optional platform dependencies, try:

```bash
npm install --no-optional
```

### The build is stale

Clean generated output and build again:

```bash
npm run clean
npm run build
```

### Browserslist warning

The warning about outdated `caniuse-lite` data does not normally prevent the
GUI from starting. It can be refreshed with:

```bash
npx update-browserslist-db@latest
```

## Project Scope

The local Scratch GUI repository is an archived standalone Scratch GUI project;
its upstream README points new development toward the Scratch monorepo. This
workspace keeps the checkout because it provides editable open-source Scratch
blocks and interface code for Magiccode version 2.

The version-2 goal is to support a block-based editor that can export:

- A Scratch-compatible `.sb3` project
- A ZIP containing an HTML user interface
- A Python backend file
- A `requirements.txt` file for backend dependencies

The exact export implementation is application work in this workspace. Starting
the Scratch GUI with the steps above only launches the editable block editor;
it does not automatically generate those Magiccode export files.