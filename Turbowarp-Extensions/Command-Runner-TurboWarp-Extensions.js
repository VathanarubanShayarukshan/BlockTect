// Name: System Commands
// ID: syscommands
// Description: Run system commands natively in background or get outputs.
// By: You
// License: MIT

(function (Scratch) {
  "use strict";

  const icon = `data:image/svg+xml;,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#1e1e1e"/><text x="8" y="32" font-family="monospace" font-size="24" font-weight="bold" fill="#4af626">&gt;_</text></svg>')}`;

  // Node.js-ஐ எடுக்கும் முறையை மிகவும் துல்லியமாக மாற்றியுள்ளேன்
  const getNodeRequire = () => {
    // 1. Electron / NW.js Packaged Apps-க்காக
    if (typeof require !== 'undefined') {
        return require;
    }
    // 2. Browser Environment-ல் require இருந்தால் (சில பழைய Packagers)
    if (typeof window !== 'undefined' && window.require) {
        return window.require;
    }
    return null;
  };

  class SystemCommandsExt {
    getInfo() {
      return {
        id: 'syscommands',
        name: 'System Commands',
        color1: '#2c3e50', 
        color2: '#1a252f', 
        menuIconURI: icon,
        blocks: [
          {
            opcode: 'runCmd',
            blockType: Scratch.BlockType.COMMAND,
            text: 'run command [CMD]',
            arguments: {
              CMD: {
                type: Scratch.ArgumentType.STRING,
                defaultValue: 'echo "Hello"'
              }
            }
          },
          {
            opcode: 'runCmdOutput',
            blockType: Scratch.BlockType.REPORTER,
            text: 'output of command [CMD]',
            arguments: {
              CMD: {
                type: Scratch.ArgumentType.STRING,
                defaultValue: 'dir'
              }
            }
          },
          {
            opcode: 'runCmdBg',
            blockType: Scratch.BlockType.COMMAND,
            text: 'run background command [CMD]',
            arguments: {
              CMD: {
                type: Scratch.ArgumentType.STRING,
                defaultValue: 'ping 8.8.8.8'
              }
            }
          }
        ]
      };
    }

    runCmd(args) {
      const req = getNodeRequire();
      if (req) {
        try {
          req('child_process').execSync(Scratch.Cast.toString(args.CMD));
        } catch (err) {
          console.error("Command error:", err);
        }
      } else {
        console.warn("Node.js is disabled in this environment.");
      }
    }

    runCmdOutput(args) {
      const req = getNodeRequire();
      if (req) {
        try {
          return req('child_process').execSync(Scratch.Cast.toString(args.CMD)).toString().trim();
        } catch (err) {
          return "Error: " + err.message;
        }
      }
      return "Error: Node.js not found! Enable Node.js in Packager.";
    }

    runCmdBg(args) {
      const req = getNodeRequire();
      if (req) {
        req('child_process').exec(Scratch.Cast.toString(args.CMD));
      }
    }
  }

  Scratch.extensions.register(new SystemCommandsExt());
})(Scratch);