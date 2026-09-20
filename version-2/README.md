# Magiccode 4.0 — Block to Code (version-2)

Magiccode 3.0-இன் புதிய பதிப்பு. இது block-based coding app-ஆகும், அதில் blocks-களை drag & drop செய்து, **real Python & HTML code**-ஆக மாற்றலாம்.

## புதிய அம்சங்கள் (pr1)

- **Download ZIP** பொத்தான் → zip கோப்பில் 3 கோப்புகள்:
  1. **`<project>.html`** — app UI (frontend)
  2. **`<project>.py`** — backend logic (Python)
  3. **`requirements.txt`** — தேவையான packages

- **Download .sb3** பொத்தான் → Scratch-போன்ற project file
- Blocks → **real Python code** (தானாக)
- Blocks → **real HTML code** (தானாக)
- Project name-ஐ மாற்றலாம்

## எப்படி இயக்குவது

```bash
cd /workspaces/BlockTect/version-2
python3 -m http.server 8000
```

பிறகு browser-இல் `http://localhost:8000` திறக்கவும்.

## கோப்பு கட்டமைப்பு

```
version-2/
├── index.html      # Magiccode 4.0 app (முக்கிய கோப்பு)
└── README.md       # இந்த கோப்பு
```

## குறிப்பு

- இந்த app **சுயாதீனமானது** — Magiccode 3.0 HTML-இன் வெளிப்புற script கோப்புகளை சார்ந்திருக்காது.
- Blocks-ஐ இழுத்து விடுங்கள், வலது பக்கத்தில் Python / HTML / requirements.txt code தானாக உருவாகும்.
- **Download ZIP** அழுத்தினால் மூன்று கோப்புகளும் zip-ஆக download ஆகும்.