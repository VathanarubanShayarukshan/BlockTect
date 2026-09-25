# BlockTect 0.3

Scratch போன்ற block programming UI மூலம் Python + HTML project உருவாக்கும் BlockTect பதிப்பு 0.3 இது.

இந்த பதிப்பில் `scratch-gui` கோப்புறைக்குள் Scratch Foundation-ன் open-source Scratch 3 GUI source உள்ளது. BlockTect export வசதி அதே Scratch GUI source-க்குள் இணைக்கப்பட்டுள்ளது.

## 1. தேவைகள்

- Windows 10 அல்லது அதற்குப் பிந்தைய Windows பதிப்பு
- Node.js 18 அல்லது அதற்குப் பிந்தைய Node.js பதிப்பு
- Python 3.9 அல்லது அதற்குப் பிந்தைய Python பதிப்பு (export செய்யப்பட்ட app-களுக்கு)
- நவீன web browser

Python நிறுவப்பட்டுள்ளதா என்பதைச் சரிபார்க்க PowerShell-ல்:

```powershell
python --version
```

Python command வேலை செய்யவில்லை என்றால் Python-ஐ நிறுவி, installation நேரத்தில் `Add Python to PATH` என்பதைத் தேர்ந்தெடுக்கவும்.

Node.js மற்றும் npm உள்ளதா எனச் சரிபார்க்க:

```powershell
node --version
npm --version
```

## 2. Project folder-க்கு செல்லுதல்

PowerShell-ல் workspace folder-க்கு செல்லவும்:

```powershell
cd F:\codings\1My_Apps\BlockTect
```

பிறகு version 0.3 app folder-க்கு செல்லவும்:

```powershell
cd version-0.3\scratch-gui
```

## 3. Scratch GUI-ஐ foreground-ல் இயக்குதல்

```powershell
npm install
npm start
```

Webpack தொடங்கிய பிறகு browser-ல் இதைத் திறக்கவும்:

```text
http://localhost:8601
```

PowerShell window திறந்தே இருக்க வேண்டும். நிறுத்த `Ctrl+C` அழுத்தவும்.

## 4. Scratch GUI-ஐ background-ல் இயக்குதல்

PowerShell-ல் `scratch-gui` folder-ல் இருந்து:

```text
Start-Process -FilePath npm.cmd -ArgumentList 'start' -WorkingDirectory (Get-Location)
```

இப்போது PowerShell prompt திரும்ப வரும். Browser-ல் திறக்கவும்:

```text
http://localhost:8601
```

செயல்முறை இயங்குகிறதா எனச் சரிபார்க்க:

```powershell
Get-Process node
```

Port பதில் தருகிறதா எனச் சரிபார்க்க:

```powershell
Invoke-WebRequest http://localhost:8601
```

Background process-ஐ நிறுத்த:

```powershell
Stop-Process -Name node
```

கணினியில் வேறு Python app-களும் இயங்கினால், அவற்றை நிறுத்தாமல் குறிப்பிட்ட process-ஐ மட்டும் நிறுத்த Process ID பயன்படுத்தவும்:

```powershell
Get-Process node
Stop-Process -Id <PROCESS_ID>
```

## 5. UI பயன்பாடு

### Block சேர்த்தல்

1. இடப்புறத்தில் உள்ள category-ஐப் பார்க்கவும்.
2. தேவையான block-ஐ அழுத்தவும்.
3. Block நடுவில் உள்ள input மதிப்பை மாற்றவும்.
4. `அனைத்தையும் அழி` பொத்தானால் அனைத்து blocks-ஐ நீக்கலாம்.

### Preview

வலப்புற `Live Preview` panel-ல் HTML block-களின் output தானாகக் காட்டப்படும்.

தற்போது preview-ல் ஆதரிக்கப்படும் HTML blocks:

- தலைப்பு
- உரை
- பொத்தான்
- Scratch-style speech message

### Run

`இயக்கவும்` பொத்தானை அழுத்தினால் project-ன் preview மீண்டும் உருவாக்கப்படும்.

### Save

மேலே உள்ள project name-ஐ மாற்றி `சேமி` பொத்தானை அழுத்தவும். Project JSON கோப்புகள் இங்கே சேமிக்கப்படும்:

```text
version-0.3\scratch-gui\projects\
```

### Login

`உள்நுழை` பொத்தான் தற்போது local UI demonstration ஆக உள்ளது. இது உண்மையான online account server அல்ல.

## 6. Full project download

Scratch GUI-யின் `File` menu-ல் உள்ள `Download Python + HTML project` என்பதைத் தேர்ந்தெடுக்கவும். இது `.sb3` file மட்டும் அல்ல; Python + HTML project-ன் முழு `.zip` package-ஐ உருவாக்கும்.

ZIP-க்குள் இருக்கும் files:

```text
project-name/
├── project-name.py
├── project-name.html
├── project-name.shsb
├── project-name.project.json
├── run.bat
├── run.sh
├── README.md
└── requirements.txt
```

### Export செய்யப்பட்ட project-ஐ இயக்குதல்

ZIP-ஐ extract செய்த பிறகு:

```powershell
cd project-name
python project-name.py
```

இதனால் `Running ...` மற்றும் `Targets: N` logic test output கிடைக்கும். Flask HTML UI-ஐ இயக்க:

```powershell
python -m pip install -r requirements.txt
python project-name.py --serve
```

பிறகு `http://127.0.0.1:5000`-ஐத் திறக்கவும். Windows-ல் `run.bat`, Bash-ல் `./run.sh` பயன்படுத்தலாம்.

HTML file-ஐ browser-ல் நேரடியாகத் திறக்கலாம்:

```text
project-name.html
```

## 7. முக்கிய கோப்புகள்

```text
version-0.3/
├── prompt.txt                 # pr1 திட்ட வழிமுறை
├── README.md                  # இந்த தமிழ் வழிகாட்டி
└── scratch-gui/
    ├── package.json            # Scratch GUI dependencies மற்றும் commands
    ├── src/                    # Scratch GUI React source மற்றும் exporter
    ├── static/                 # Browser static assets
    ├── test/                   # Unit மற்றும் integration tests
    └── webpack.config.js       # Development server மற்றும் build config
```

## 8. API endpoints

| Endpoint | Method | பயன்பாடு |
|---|---|---|
| `/api/blocks` | GET | Block catalog பெறுதல் |
| `/api/projects` | GET | Saved projects பட்டியல் |
| `/api/project/<name>` | GET | ஒரு project-ஐ load செய்தல் |
| `/api/project/save` | POST | Project சேமித்தல் |
| `/api/export` | POST | Full ZIP உருவாக்குதல் |

## 9. Port பிரச்சினை

`8080` port ஏற்கனவே பயன்படுத்தப்பட்டால் app தொடங்காது. அப்போது `app.py`-ல்:

```python
PORT = 8080
```

என்பதை வேறு port ஆக மாற்றவும், உதாரணமாக:

```python
PORT = 8081
```

பிறகு மீண்டும் இயக்கி:

```text
http://127.0.0.1:8081
```

என்பதைத் திறக்கவும்.

## 10. Syntax check

Server-ஐ இயக்குவதற்கு முன் Python syntax சரிபார்க்க:

```powershell
python -m py_compile app.py
```

எந்த output-மும் வரவில்லை என்றால் syntax சரியாக உள்ளது.

## 11. Version 0.3 எல்லை

இந்த பதிப்பு வேலை செய்யும் Python + HTML project builder ஆகும். Scratch GUI source folder இன்னும் தனியாக இணைக்கப்படவில்லை; தற்போது `scratch-gui` என்பது BlockTect-ன் standalone web app folder.

அடுத்த கட்டத்தில் சேர்க்கக்கூடியவை:

- உண்மையான Scratch `.sb3` import/export
- Scratch GUI அல்லது Scratch VM இணைப்பு
- SQLite அல்லது online user login
- Generated Python app-ஐ server-ல் பாதுகாப்பாக run செய்தல்
- கூடுதல் Tamil blocks
- Project load UI button

## 12. விரைவான தொடக்கம்

```powershell
cd F:\codings\1My_Apps\BlockTect\version-0.3\scratch-gui
python app.py
```

பிறகு browser-ல்:

```text
http://127.0.0.1:8080
```
