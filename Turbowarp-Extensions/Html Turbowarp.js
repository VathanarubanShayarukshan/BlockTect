(function (Scratch) {
  'use strict';

  class CustomHTMLExtension {
    getInfo() {
      return {
        id: 'customhtml',
        name: 'HTML Sprites',
        color1: '#2B3A55',
        color2: '#1F2937',
        blocks: [
          // --- Creation ---
          {
            opcode: 'createHtmlTag',
            blockType: Scratch.BlockType.COMMAND,
            text: 'create HTML [HTML] with ID [ID] at x: [X] y: [Y]',
            arguments: {
              HTML: { type: Scratch.ArgumentType.STRING, defaultValue: '<h1>hi</h1>' },
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              X: { type: Scratch.ArgumentType.NUMBER, defaultValue: 0 },
              Y: { type: Scratch.ArgumentType.NUMBER, defaultValue: 0 }
            }
          },

          '---', // Block Separator

          // --- Motion Blocks ---
          {
            opcode: 'setXY',
            blockType: Scratch.BlockType.COMMAND,
            text: 'go to HTML element [ID] x: [X] y: [Y]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              X: { type: Scratch.ArgumentType.NUMBER, defaultValue: 0 },
              Y: { type: Scratch.ArgumentType.NUMBER, defaultValue: 0 }
            }
          },
          {
            opcode: 'changeX',
            blockType: Scratch.BlockType.COMMAND,
            text: 'change HTML element [ID] x by [DX]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              DX: { type: Scratch.ArgumentType.NUMBER, defaultValue: 10 }
            }
          },
          {
            opcode: 'changeY',
            blockType: Scratch.BlockType.COMMAND,
            text: 'change HTML element [ID] y by [DY]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              DY: { type: Scratch.ArgumentType.NUMBER, defaultValue: 10 }
            }
          },
          {
            opcode: 'setDirection',
            blockType: Scratch.BlockType.COMMAND,
            text: 'point HTML element [ID] in direction [DIR]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              DIR: { type: Scratch.ArgumentType.NUMBER, defaultValue: 90 }
            }
          },

          '---',

          // --- Looks & Transform Blocks ---
          {
            opcode: 'setSize',
            blockType: Scratch.BlockType.COMMAND,
            text: 'set HTML element [ID] size to [SIZE] %',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              SIZE: { type: Scratch.ArgumentType.NUMBER, defaultValue: 100 }
            }
          },
          {
            opcode: 'showElement',
            blockType: Scratch.BlockType.COMMAND,
            text: 'show HTML element [ID]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' }
            }
          },
          {
            opcode: 'hideElement',
            blockType: Scratch.BlockType.COMMAND,
            text: 'hide HTML element [ID]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' }
            }
          },
          {
            opcode: 'setStyle',
            blockType: Scratch.BlockType.COMMAND,
            text: 'set style [PROP] of HTML element [ID] to [VALUE]',
            arguments: {
              PROP: { type: Scratch.ArgumentType.STRING, defaultValue: 'color' },
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' },
              VALUE: { type: Scratch.ArgumentType.STRING, defaultValue: 'red' }
            }
          },

          '---',

          // --- Sensing & Data ---
          {
            opcode: 'getElementData',
            blockType: Scratch.BlockType.REPORTER,
            text: 'get property [PROP] from element ID [ID]',
            arguments: {
              PROP: { type: Scratch.ArgumentType.STRING, defaultValue: 'innerText' },
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' }
            }
          },
          {
            opcode: 'deleteElement',
            blockType: Scratch.BlockType.COMMAND,
            text: 'delete HTML element [ID]',
            arguments: {
              ID: { type: Scratch.ArgumentType.STRING, defaultValue: 'header1' }
            }
          }
        ]
      };
    }

    // --- Overlay Container Helper ---
    getOverlayContainer() {
      let stageContainer = null;
      if (Scratch.renderer && Scratch.renderer.canvas && Scratch.renderer.canvas.parentElement) {
        stageContainer = Scratch.renderer.canvas.parentElement;
      } else {
        const canvas = document.querySelector('canvas');
        if (canvas && canvas.parentElement) stageContainer = canvas.parentElement;
      }

      if (!stageContainer) stageContainer = document.body;

      if (getComputedStyle(stageContainer).position === 'static') {
        stageContainer.style.position = 'relative';
      }

      let container = document.getElementById('tw-html-overlay');
      if (!container) {
        container = document.createElement('div');
        container.id = 'tw-html-overlay';
        container.style.position = 'absolute';
        container.style.top = '0px';
        container.style.left = '0px';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.zIndex = '10';
        container.style.pointerEvents = 'none';
        container.style.overflow = 'hidden';
        stageContainer.appendChild(container);
      } else if (container.parentElement !== stageContainer) {
        stageContainer.appendChild(container);
      }
      return container;
    }

    // --- Apply Scratch Stage Coordinates & Transforms ---
    updateTransform(element) {
      const x = parseFloat(element.dataset.x || '0');
      const y = parseFloat(element.dataset.y || '0');
      const size = parseFloat(element.dataset.size || '100') / 100;
      const dir = parseFloat(element.dataset.dir || '90'); // 90 deg in Scratch is 0 deg in CSS
      const rotationCss = dir - 90;

      // Map Scratch centered coordinates (-240 to 240, -180 to 180) to percentage position
      const leftPercent = 50 + (x / 480) * 100;
      const topPercent = 50 - (y / 360) * 100;

      element.style.position = 'absolute';
      element.style.left = `${leftPercent}%`;
      element.style.top = `${topPercent}%`;
      element.style.transform = `translate(-50%, -50%) rotate(${rotationCss}deg) scale(${size})`;
      element.style.transformOrigin = 'center center';
      element.style.margin = '0';
    }

    // --- Block Implementations ---
    createHtmlTag(args) {
      const htmlContent = String(args.HTML);
      const elementId = String(args.ID);
      const container = this.getOverlayContainer();

      const existingElement = document.getElementById(elementId);
      if (existingElement) existingElement.remove();

      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = htmlContent.trim();
      const newElement = tempDiv.firstElementChild || document.createElement('div');
      newElement.id = elementId;
      newElement.style.pointerEvents = 'auto';

      // Store initial sprite metadata
      newElement.dataset.x = String(args.X);
      newElement.dataset.y = String(args.Y);
      newElement.dataset.size = '100';
      newElement.dataset.dir = '90';

      container.appendChild(newElement);
      this.updateTransform(newElement);
    }

    setXY(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return;
      el.dataset.x = String(args.X);
      el.dataset.y = String(args.Y);
      this.updateTransform(el);
    }

    changeX(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return;
      const currentX = parseFloat(el.dataset.x || '0');
      el.dataset.x = String(currentX + Number(args.DX));
      this.updateTransform(el);
    }

    changeY(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return;
      const currentY = parseFloat(el.dataset.y || '0');
      el.dataset.y = String(currentY + Number(args.DY));
      this.updateTransform(el);
    }

    setDirection(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return;
      el.dataset.dir = String(args.DIR);
      this.updateTransform(el);
    }

    setSize(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return;
      el.dataset.size = String(args.SIZE);
      this.updateTransform(el);
    }

    showElement(args) {
      const el = document.getElementById(String(args.ID));
      if (el) el.style.display = '';
    }

    hideElement(args) {
      const el = document.getElementById(String(args.ID));
      if (el) el.style.display = 'none';
    }

    setStyle(args) {
      const el = document.getElementById(String(args.ID));
      if (el) {
        el.style[String(args.PROP)] = String(args.VALUE);
      }
    }

    getElementData(args) {
      const el = document.getElementById(String(args.ID));
      if (!el) return '';
      const prop = String(args.PROP);
      return prop in el ? String(el[prop] ?? '') : '';
    }

    deleteElement(args) {
      const el = document.getElementById(String(args.ID));
      if (el) el.remove();
    }
  }

  Scratch.extensions.register(new CustomHTMLExtension());
})(Scratch);