/* eslint-disable max-len */

import bindAll from 'lodash.bindall';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import JSZip from 'jszip';

import downloadBlob from '../lib/download-blob';
import {projectTitleInitialState} from '../reducers/project-title';

const getProjectName = (title, defaultTitle) => {
    const name = title && title.length > 0 ? title : defaultTitle;
    return name.substring(0, 100)
        .replace(/[^a-zA-Z0-9 _-]/g, '_')
        .trim() || 'blocktect-project';
};

// The exported HTML is intentionally self-contained for offline use.
const createHtmlProject = (name, project) => {
    const projectData = JSON.stringify(project).replace(/</g, '\\u003c');
    return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${name}</title>
<style>
body{margin:0;background:#f5f6f8;color:#172033;font-family:system-ui,sans-serif}.app{max-width:780px;margin:28px auto;padding:0 18px}.top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}.top h1{font-size:20px;margin:0}.controls{display:flex;gap:8px}.controls button{border:0;border-radius:7px;padding:8px 14px;color:white;font-weight:700;cursor:pointer}.flag{background:#58b957}.stop{background:#e4572e}.stage-shell{background:#252b36;border-radius:12px;padding:18px;box-shadow:0 12px 28px #17203322}.stage{position:relative;width:min(480px,100%);aspect-ratio:4/3;margin:auto;overflow:hidden;background:linear-gradient(#b9e8ff 0 70%,#8bd36f 70%);background-size:cover;background-position:center;border:4px solid #111827;border-radius:4px}.stage:after{content:"";position:absolute;inset:70% 0 0;background:repeating-linear-gradient(135deg,#7fc765 0 12px,#8bd36f 12px 24px);opacity:.45;pointer-events:none}.sprite{position:absolute;z-index:2;width:64px;height:64px;display:grid;place-items:center;font-size:46px;transform:translate(-50%,-50%);transition:left .25s,top .25s}.sprite img{max-width:64px;max-height:64px}.bubble{position:absolute;z-index:3;top:-34px;left:46px;min-width:80px;max-width:180px;background:white;border:2px solid #172033;border-radius:14px;padding:7px 10px;text-align:left;font-size:13px;box-shadow:2px 2px #172033}.info{display:flex;justify-content:space-between;color:#697386;font-size:12px;margin-top:12px}.empty{padding:120px 10px;text-align:center;color:#64748b}
</style></head><body><main class="app"><header class="top"><h1>${name}</h1><div class="controls"><button class="flag" id="flag">▶ Green Flag</button><button class="stop" id="stop">■ Stop</button></div></header><section class="stage-shell"><div id="stage" class="stage"></div></section><div class="info"><span>BlockTect Scratch Preview</span><span id="status">Ready</span></div></main>
<script>
const project=${projectData};
const stage=document.getElementById('stage');
const status=document.getElementById('status');
const stageTarget=(project.targets||[]).find(target=>target.isStage);
const sprites=(project.targets||[]).filter(target=>!target.isStage);
const nodes=new Map();
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,character=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const inputValue=(block,name,fallback='')=>{const input=block.inputs&&block.inputs[name];if(input){if(Array.isArray(input[1]))return input[1][1]??fallback;return input[1]??fallback;}const field=block.fields&&block.fields[name];return field?field[0]??fallback:fallback;};
const normalizeKey=value=>{const normalized=String(value||'').trim().toLowerCase();if(!normalized||normalized===' ')return 'space';if(normalized==='leftarrow'||normalized==='left arrow'||normalized==='arrowleft')return 'left arrow';if(normalized==='rightarrow'||normalized==='right arrow'||normalized==='arrowright')return 'right arrow';if(normalized==='uparrow'||normalized==='up arrow'||normalized==='arrowup')return 'up arrow';if(normalized==='downarrow'||normalized==='down arrow'||normalized==='arrowdown')return 'down arrow';return normalized;};
const showSpeech=(target,text)=>{const node=nodes.get(target.name);if(!node)return;const bubble=node.querySelector('.bubble');bubble.innerHTML=escapeHtml(text);bubble.hidden=!text;};
const costumePath=target=>{const costume=(target.costumes||[])[target.currentCostume||0];return costume&&costume.md5ext?'assets/'+costume.md5ext:'';};
const render=()=>{stage.innerHTML='';nodes.clear();if(stageTarget){const backdrop=costumePath(stageTarget);if(backdrop)stage.style.backgroundImage='url("'+backdrop+'")';}if(!sprites.length){stage.innerHTML='<div class="empty">No sprites in this project</div>';return;}for(const sprite of sprites){const node=document.createElement('div');node.className='sprite';node.style.left=(240+(Number(sprite.x)||0))+'px';node.style.top=(180-(Number(sprite.y)||0))+'px';const image=costumePath(sprite);node.innerHTML='<div class="bubble" hidden></div>'+(image?'<img src="'+image+'" alt="'+escapeHtml(sprite.name)+'">':'<span aria-label="'+escapeHtml(sprite.name)+'">🐱</span>');stage.appendChild(node);nodes.set(sprite.name,node);}};
const moveSprite=(sprite,steps)=>{const direction=(Number(sprite.direction)||90)*Math.PI/180;sprite.x=(Number(sprite.x)||0)+Math.sin(direction)*steps;sprite.y=(Number(sprite.y)||0)+Math.cos(direction)*steps;const node=nodes.get(sprite.name);if(node){node.style.left=(240+sprite.x)+'px';node.style.top=(180-sprite.y)+'px';}};
const playSound=(sprite,name,wait)=>{const sound=(sprite.sounds||[]).find(item=>item.name===name)||(sprite.sounds||[])[0];if(!sound||!sound.md5ext)return Promise.resolve();const audio=new Audio('assets/'+sound.md5ext);const ended=new Promise(resolve=>{audio.onended=resolve;audio.onerror=resolve;});audio.play().catch(()=>{});return wait?ended:Promise.resolve();};
const runScript=async(sprite,startId)=>{const blocks=sprite.blocks||{};let id=startId;while(id){const block=blocks[id];if(!block)break;const value=inputValue(block,'STEPS',10);if(block.opcode==='looks_say')showSpeech(sprite,inputValue(block,'MESSAGE',''));else if(block.opcode==='motion_movesteps')moveSprite(sprite,Number(value)||0);else if(block.opcode==='motion_gotoxy'){sprite.x=Number(inputValue(block,'X',0));sprite.y=Number(inputValue(block,'Y',0));moveSprite(sprite,0);}else if(block.opcode==='motion_setx'){sprite.x=Number(inputValue(block,'X',0));moveSprite(sprite,0);}else if(block.opcode==='motion_sety'){sprite.y=Number(inputValue(block,'Y',0));moveSprite(sprite,0);}else if(block.opcode==='motion_changexby'){sprite.x=(Number(sprite.x)||0)+Number(inputValue(block,'DX',0));moveSprite(sprite,0);}else if(block.opcode==='motion_changeyby'){sprite.y=(Number(sprite.y)||0)+Number(inputValue(block,'DY',0));moveSprite(sprite,0);}else if(block.opcode==='motion_turnright')sprite.direction=(Number(sprite.direction)||90)+Number(inputValue(block,'DEGREES',15));else if(block.opcode==='motion_turnleft')sprite.direction=(Number(sprite.direction)||90)-Number(inputValue(block,'DEGREES',15));else if(block.opcode==='looks_hide'){const node=nodes.get(sprite.name);if(node)node.hidden=true;}else if(block.opcode==='looks_show'){const node=nodes.get(sprite.name);if(node)node.hidden=false;}else if(block.opcode==='sound_playuntildone')await playSound(sprite,inputValue(block,'SOUND_MENU',''),true);else if(block.opcode==='sound_play')await playSound(sprite,inputValue(block,'SOUND_MENU',''),false);else if(block.opcode==='control_wait')await new Promise(resolve=>setTimeout(resolve,(Number(value)||1)*1000));id=block.next;}};
const runEvent=(key=null)=>{const requestedKey=key?normalizeKey(key):null;for(const sprite of sprites){const blocks=sprite.blocks||{};for(const [id,block] of Object.entries(blocks)){const isFlag=!requestedKey&&block.opcode==='event_whenflagclicked';const keyField=block.fields&&block.fields.KEY_OPTION?block.fields.KEY_OPTION[0]:'';const isKey=requestedKey&&block.opcode==='event_whenkeypressed'&&normalizeKey(keyField)===requestedKey;if(isFlag||isKey)runScript(sprite,id);}}status.textContent=requestedKey?'Key: '+requestedKey:'Running';};
document.getElementById('flag').onclick=()=>runEvent();document.getElementById('stop').onclick=()=>{for(const sprite of sprites){showSpeech(sprite,'');const node=nodes.get(sprite.name);if(node)node.hidden=false;}status.textContent='Stopped';};document.addEventListener('keydown',event=>{const key=event.key===' '? 'space':event.key;runEvent(key);});render();
</script></body></html>`;
};

const createPythonProject = (name, project) => {
    const projectJson = JSON.stringify(JSON.stringify(project));
    return `"""${name} exported from Scratch GUI by BlockTect."""
import sys
import json
from pathlib import Path

from flask import Flask, Response, send_from_directory

PROJECT_JSON = ${projectJson}
PROJECT = json.loads(PROJECT_JSON)


def run():
    print("Running ${name}")
    print(f"Targets: {len(PROJECT.get('targets', []))}")
    Path("${name}.project.json").write_text(json.dumps(PROJECT, ensure_ascii=False, indent=2), encoding="utf-8")


def create_app():
    app = Flask(__name__)
    project_dir = Path(__file__).resolve().parent
    html_path = project_dir / "${name}.html"
    assets_dir = project_dir / "assets"

    @app.get("/")
    def index():
        return Response(html_path.read_text(encoding="utf-8"), mimetype="text/html")

    @app.get("/assets/<path:filename>")
    def serve_asset(filename):
        if not assets_dir.exists():
            return Response("Asset directory not found.", status=404)
        return send_from_directory(str(assets_dir), filename)

    return app


if __name__ == "__main__":
    if "--serve" in sys.argv:
        create_app().run(host="127.0.0.1", port=5000, debug=False)
    else:
        run()
`;
};

const createShsbProject = project => `// BlockTect export from Scratch GUI\nPROJECT_JSON ${JSON.stringify(project)}\n`;
const createWindowsRunner = name => `@echo off\r\npython "%~dp0${name}.py" --serve\r\npause\r\n`;
const createBashRunner = name => `#!/usr/bin/env bash\npython3 "$(dirname "$0")/${name}.py" --serve\n`;

class BlockTectProjectDownloader extends React.Component {
    constructor (props) {
        super(props);
        bindAll(this, ['downloadProject']);
    }

    async downloadProject () {
        const serializedProject = this.props.vm.toJSON();
        const project = typeof serializedProject === 'string' ?
            JSON.parse(serializedProject) : serializedProject;
        const name = this.props.projectName;
        const zip = new JSZip();
        const folder = zip.folder(name);
        const sourceProject = await this.props.vm.saveProjectSb3();
        const sourceZip = await JSZip.loadAsync(sourceProject);
        const mediaEntries = Object.values(sourceZip.files).filter(file => (
            !file.dir && file.name !== 'project.json'
        ));
        await Promise.all(mediaEntries.map(async file => {
            const assetName = file.name.split('/').pop();
            folder.file(`assets/${assetName}`, await file.async('uint8array'));
        }));
        folder.file(`${name}.html`, createHtmlProject(name, project));
        folder.file(`${name}.py`, createPythonProject(name, project));
        folder.file(`${name}.shsb`, createShsbProject(project));
        folder.file(`${name}.project.json`, JSON.stringify(project, null, 2));
        folder.file('run.bat', createWindowsRunner(name));
        folder.file('run.sh', createBashRunner(name));
        folder.file('README.md', `# ${name}\n\nInstall: python -m pip install -r requirements.txt\nLogic test: python ${name}.py\nWeb app: python ${name}.py --serve\nWindows: double-click run.bat\nBash: chmod +x run.sh && ./run.sh\nOpen http://127.0.0.1:5000 in a browser.\n`);
        folder.file('requirements.txt', 'Flask>=3.0,<4.0\n');
        zip.generateAsync({type: 'blob'}).then(content => {
            downloadBlob(`${name}.zip`, content);
        });
    }

    render () {
        return this.props.children(this.props.className, this.downloadProject);
    }
}

BlockTectProjectDownloader.propTypes = {
    children: PropTypes.func,
    className: PropTypes.string,
    projectName: PropTypes.string,
    vm: PropTypes.shape({
        saveProjectSb3: PropTypes.func,
        toJSON: PropTypes.func
    })
};

BlockTectProjectDownloader.defaultProps = {
    className: ''
};

const mapStateToProps = state => ({
    projectName: getProjectName(state.scratchGui.projectTitle, projectTitleInitialState),
    vm: state.scratchGui.vm
});

export default connect(mapStateToProps)(BlockTectProjectDownloader);

/* eslint-enable max-len */
