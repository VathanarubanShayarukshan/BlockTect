const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

const quotePowerShell = (value) => `'${value.replace(/'/g, "''")}'`;

const runPowerShell = (script) => {
  const encodedScript = Buffer.from(script, 'utf16le').toString('base64');
  const result = spawnSync('powershell.exe', [
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy',
    'Bypass',
    '-EncodedCommand',
    encodedScript
  ], {
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error((result.stderr || result.stdout || 'PowerShell ZIP operation failed').trim());
  }
};

const readProjectJson = (projectPath, tempDirectory) => {
  const jsonPath = path.join(tempDirectory, 'project.json');
  const script = `
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead(${quotePowerShell(projectPath)})
try {
  $entry = $archive.GetEntry('project.json')
  if ($null -eq $entry) { throw 'The .sb3 archive does not contain project.json.' }
  $reader = [System.IO.StreamReader]::new($entry.Open())
  try { $json = $reader.ReadToEnd() } finally { $reader.Dispose() }
  [System.IO.File]::WriteAllText(${quotePowerShell(jsonPath)}, $json, [System.Text.Encoding]::UTF8)
} finally {
  $archive.Dispose()
}
`;

  runPowerShell(script);
  const jsonText = fs.readFileSync(jsonPath, 'utf8').replace(/^\uFEFF/, '');
  const project = JSON.parse(jsonText);
  if (!project || !Array.isArray(project.targets) || project.targets.length === 0) {
    throw new Error('project.json is not a valid Scratch 3 project: expected at least one target.');
  }
};

const createOutputFiles = (tempDirectory) => {
  const publicDirectory = path.join(tempDirectory, 'public');
  fs.mkdirSync(publicDirectory);

  fs.writeFileSync(path.join(publicDirectory, 'index.html'), `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Scratch App</title>
  <style>
    * { box-sizing: border-box; }
    html, body { width: 100%; height: 100%; margin: 0; }
    body { display: grid; grid-template-rows: 38px minmax(0, 1fr); background: #171a1f; color: #edf0f2; font: 13px system-ui, sans-serif; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 0 14px; border-bottom: 1px solid #343a42; }
    #bridge-status { color: #a9b1ba; }
    #bridge-status[data-connected="true"] { color: #72d89b; }
    iframe { width: 100%; height: 100%; border: 0; background: #fff; }
  </style>
</head>
<body>
  <header><strong>Scratch App</strong><span id="bridge-status">Connecting to local backend...</span></header>
  <iframe id="scratch-player" title="Scratch project" allow="camera; microphone; fullscreen" allowfullscreen></iframe>
  <script src="/bridge.js"></script>
  <script>
    const projectUrl = new URL('/project.sb3', window.location.origin);
    const playerUrl = new URL('https://turbowarp.org/embed');
    playerUrl.searchParams.set('project_url', projectUrl.href);
    playerUrl.searchParams.set('autoplay', '');
    document.querySelector('#scratch-player').src = playerUrl.href;

    const status = document.querySelector('#bridge-status');
    window.FullStackBridge.onStatusChange((connected) => {
      status.dataset.connected = String(connected);
      status.textContent = connected ? 'Backend connected' : 'Backend disconnected';
    });
  </script>
</body>
</html>
`);

  fs.writeFileSync(path.join(publicDirectory, 'bridge.js'), `(function () {
  const listeners = new Set();
  const statusListeners = new Set();
  let socket;
  let connected = false;

  const updateStatus = (nextStatus) => {
    connected = nextStatus;
    statusListeners.forEach((listener) => listener(connected));
  };

  const connect = () => {
    socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/bridge');
    socket.addEventListener('open', () => updateStatus(true));
    socket.addEventListener('close', () => {
      updateStatus(false);
      window.setTimeout(connect, 1500);
    });
    socket.addEventListener('error', () => socket.close());
    socket.addEventListener('message', (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (error) {
        return;
      }
      listeners.forEach((listener) => listener(message));
    });
  };

  window.FullStackBridge = Object.freeze({
    get connected() { return connected; },
    send(type, payload) {
      if (!connected || typeof type !== 'string') return false;
      socket.send(JSON.stringify({type, payload}));
      return true;
    },
    onMessage(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    onStatusChange(listener) {
      statusListeners.add(listener);
      listener(connected);
      return () => statusListeners.delete(listener);
    }
  });

  connect();
})();
`);

  fs.copyFileSync(path.join(tempDirectory, 'input.sb3'), path.join(publicDirectory, 'project.sb3'));

  fs.writeFileSync(path.join(tempDirectory, 'server.js'), `'use strict';

const path = require('node:path');
const express = require('express');
const {WebSocketServer} = require('ws');

const app = express();
const host = '127.0.0.1';
const port = Number(process.env.PORT || 4173);

app.use((request, response, next) => {
  response.setHeader('Access-Control-Allow-Origin', '*');
  next();
});
app.use(express.static(path.join(__dirname, 'public')));

const server = app.listen(port, host, () => {
  console.log('Full-stack app running at http://' + host + ':' + port);
});

const sockets = new WebSocketServer({server, path: '/bridge', maxPayload: 64 * 1024});
sockets.on('connection', (socket) => {
  socket.on('message', (data) => {
    let message;
    try {
      message = JSON.parse(data.toString());
    } catch (error) {
      return;
    }
    if (!message || typeof message.type !== 'string') return;

    const response = JSON.stringify({type: message.type, payload: message.payload});
    for (const client of sockets.clients) {
      if (client.readyState === 1) client.send(response);
    }
  });
});

process.on('SIGINT', () => server.close(() => process.exit(0)));
`);

  fs.writeFileSync(path.join(tempDirectory, 'package.json'), `${JSON.stringify({
    name: 'scratch-fullstack-app',
    version: '1.0.0',
    private: true,
    description: 'Scratch project frontend with a local Node.js WebSocket bridge.',
    scripts: {start: 'node server.js'},
    dependencies: {express: '^5.1.0', ws: '^8.18.3'}
  }, null, 2)}\n`);

  fs.writeFileSync(path.join(tempDirectory, 'README.md'), `# Scratch Full-Stack App

## Run

1. Install Node.js 18 or newer.
2. Run \`npm install\` in this folder.
3. Run \`npm start\` and open the local URL printed in the terminal.

The project is played in the hosted TurboWarp embed, so an internet connection is required. The WebSocket bridge is a general message relay exposed as \`window.FullStackBridge\` on the frontend. This compiler does not translate Scratch blocks into server-side JavaScript; the project remains a Scratch project played by TurboWarp.
`);
};

const compile = (inputPath, outputPath) => {
  const absoluteInput = path.resolve(inputPath);
  const absoluteOutput = path.resolve(outputPath);
  if (!fs.existsSync(absoluteInput) || !fs.statSync(absoluteInput).isFile()) {
    throw new Error(`Input file not found: ${absoluteInput}`);
  }
  if (path.extname(absoluteInput).toLowerCase() !== '.sb3') {
    throw new Error('Input must be a Scratch .sb3 file.');
  }
  if (absoluteInput.toLowerCase() === absoluteOutput.toLowerCase()) {
    throw new Error('Output ZIP path must be different from the input project path.');
  }

  const tempDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'blocktect-fullstack-'));
  try {
    readProjectJson(absoluteInput, tempDirectory);
    fs.copyFileSync(absoluteInput, path.join(tempDirectory, 'input.sb3'));
    createOutputFiles(tempDirectory);
    fs.rmSync(path.join(tempDirectory, 'project.json'));
    fs.rmSync(path.join(tempDirectory, 'input.sb3'));

    const zipScript = `
$ErrorActionPreference = 'Stop'
Compress-Archive -Path ${quotePowerShell(path.join(tempDirectory, '*'))} -DestinationPath ${quotePowerShell(absoluteOutput)} -Force
`;
    runPowerShell(zipScript);
    console.log(`Created ${absoluteOutput}`);
  } finally {
    fs.rmSync(tempDirectory, {recursive: true, force: true});
  }
};

if (require.main === module) {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error('Usage: node compile-fullstack.js <project.sb3> [output.zip]');
    process.exitCode = 2;
  } else {
    const outputPath = process.argv[3] || path.join(path.dirname(path.resolve(inputPath)), 'fullstack.zip');
    try {
      compile(inputPath, outputPath);
    } catch (error) {
      console.error(`Compiler failed: ${error.message}`);
      process.exitCode = 1;
    }
  }
}

module.exports = {compile};