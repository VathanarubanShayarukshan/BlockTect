#!/usr/bin/env python3
"""
BlockTect - Scratch-like Block Programming Tool for Python & HTML
Author: BlockTect
Version: 1.0.0
Description: A visual block programming environment to build Python and HTML applications
"""

import http.server
import json
import os
import sys
import socketserver
import webbrowser
import urllib.parse
import zipfile
import io
import base64
import subprocess
import uuid
import shutil
import textwrap
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
PORT = 8080
HOST = "127.0.0.1"
DATA_DIR = Path(__file__).parent / "blocktect_data"
PROJECTS_DIR = DATA_DIR / "projects"
EXTENSIONS_DIR = DATA_DIR / "extensions"
DATA_DIR.mkdir(exist_ok=True, parents=True)
PROJECTS_DIR.mkdir(exist_ok=True, parents=True)
EXTENSIONS_DIR.mkdir(exist_ok=True, parents=True)

# ============================================================
# BLOCK DEFINITIONS
# ============================================================

BLOCK_CATEGORIES = {
    "motion": {
        "name": "இயக்கம் (Motion)",
        "color": "#4C97FF",
        "icon": "➡️",
        "blocks": [
            {"type": "move_steps", "label": "{} அடி நகர்த்து", "args": [{"name": "steps", "type": "number", "default": 10}], "shape": "statement"},
            {"type": "turn_right", "label": "{} டிகிரி வலது திருப்பு", "args": [{"name": "degrees", "type": "number", "default": 15}], "shape": "statement"},
            {"type": "turn_left", "label": "{} டிகிரி இடது திருப்பு", "args": [{"name": "degrees", "type": "number", "default": 15}], "shape": "statement"},
            {"type": "goto_xy", "label": "x: {} y: {} க்கு செல்", "args": [{"name": "x", "type": "number", "default": 0}, {"name": "y", "type": "number", "default": 0}], "shape": "statement"},
            {"type": "set_position", "label": "x: {} ஆக அமை", "args": [{"name": "x", "type": "number", "default": 0}], "shape": "statement"},
            {"type": "set_y", "label": "y: {} ஆக அமை", "args": [{"name": "y", "type": "number", "default": 0}], "shape": "statement"},
        ]
    },
    "looks": {
        "name": "தோற்றம் (Looks)",
        "color": "#9966FF",
        "icon": "🎨",
        "blocks": [
            {"type": "say", "label": "{} என்று {} நொடி சொல்", "args": [{"name": "text", "type": "text", "default": "வணக்கம்!"}, {"name": "seconds", "type": "number", "default": 2}], "shape": "statement"},
            {"type": "say_forever", "label": "{} என்று சொல்", "args": [{"name": "text", "type": "text", "default": "வணக்கம்!"}], "shape": "statement"},
            {"type": "show", "label": "காட்டு", "args": [], "shape": "statement"},
            {"type": "hide", "label": "மறை", "args": [], "shape": "statement"},
            {"type": "set_effect", "label": "{} விளைவை {} ஆக அமை", "args": [{"name": "effect", "type": "dropdown", "options": ["color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", "ghost"], "default": "color"}, {"name": "value", "type": "number", "default": 0}], "shape": "statement"},
            {"type": "change_effect", "label": "{} விளைவை {} மாற்று", "args": [{"name": "effect", "type": "dropdown", "options": ["color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", "ghost"], "default": "color"}, {"name": "value", "type": "number", "default": 25}], "shape": "statement"},
            {"type": "set_size", "label": "அளவை {}% ஆ��� அமை", "args": [{"name": "size", "type": "number", "default": 100}], "shape": "statement"},
            {"type": "change_size", "label": "அளவை {} மாற்று", "args": [{"name": "change", "type": "number", "default": 10}], "shape": "statement"},
        ]
    },
    "control": {
        "name": "கட்டுப்பாடு (Control)",
        "color": "#FFAB19",
        "icon": "🔀",
        "blocks": [
            {"type": "wait", "label": "{} நொடி காத்திரு", "args": [{"name": "seconds", "type": "number", "default": 1}], "shape": "statement"},
            {"type": "repeat", "label": "{} முறை செய்", "args": [{"name": "times", "type": "number", "default": 10}], "shape": "container"},
            {"type": "forever", "label": "எப்போதும் செய்", "args": [], "shape": "container"},
            {"type": "if_then", "label": "உண்மை என்றால்", "args": [], "shape": "container_conditional"},
            {"type": "if_else", "label": "உண்மை என்றால்... இல்லையெனில்", "args": [], "shape": "container_if_else"},
            {"type": "wait_until", "label": "{} வரை காத்திரு", "args": [{"name": "condition", "type": "boolean", "default": "true"}], "shape": "statement"},
            {"type": "stop_all", "label": "அனைத்தையும் நிறுத்து", "args": [], "shape": "statement"},
            {"type": "stop_script", "label": "இந்த ஸ்கிரிப்டை நிறுத்து", "args": [], "shape": "statement"},
        ]
    },
    "events": {
        "name": "நிகழ்வுகள் (Events)",
        "color": "#FFBF00",
        "icon": "⚡",
        "blocks": [
            {"type": "when_green_flag", "label": "🏴 கொடி அழுத்தப்பட்டால்", "args": [], "shape": "hat"},
            {"type": "when_key_pressed", "label": "{} விசை அழுத்தப்பட்டால்", "args": [{"name": "key", "type": "dropdown", "options": ["space", "up", "down", "left", "right", "a", "b", "c", "d", "any"], "default": "space"}], "shape": "hat"},
            {"type": "when_clicked", "label": "இது கிளிக் செய்யப்பட்டால்", "args": [], "shape": "hat"},
            {"type": "when_page_load", "label": "பக்கம் ஏற்றப்படும்போது", "args": [], "shape": "hat", "custom": True},
            {"type": "when_tag_clicked", "label": "[{}] டேக் கிளிக் செய்யப்பட்டால்", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}], "shape": "hat", "custom": True},
            {"type": "broadcast", "label": "{} ஐ ஒளிபரப்பு", "args": [{"name": "message", "type": "text", "default": "செய்தி1"}], "shape": "statement"},
            {"type": "when_broadcast", "label": "{} பெற்றால்", "args": [{"name": "message", "type": "text", "default": "செய்தி1"}], "shape": "hat"},
        ]
    },
    "sensing": {
        "name": "உணர்தல் (Sensing)",
        "color": "#4CBFE6",
        "icon": "📡",
        "blocks": [
            {"type": "ask", "label": "{} என்று கேட்டு காத்திரு", "args": [{"name": "question", "type": "text", "default": "உன் பெயர் என்ன?"}], "shape": "statement"},
            {"type": "mouse_x", "label": "மவுஸ் x நிலை", "args": [], "shape": "reporter"},
            {"type": "mouse_y", "label": "மவுஸ் y நிலை", "args": [], "shape": "reporter"},
            {"type": "key_pressed", "label": "{} விசை அழுத்தப்பட்டுள்ளதா?", "args": [{"name": "key", "type": "dropdown", "options": ["space", "up", "down", "left", "right", "a", "b", "c", "d", "any"], "default": "space"}], "shape": "boolean"},
            {"type": "timer", "label": "டைமர்", "args": [], "shape": "reporter"},
            {"type": "reset_timer", "label": "டைமரை மீட்டமை", "args": [], "shape": "statement"},
        ]
    },
    "operators": {
        "name": "செயலிகள் (Operators)",
        "color": "#59C059",
        "icon": "🔣",
        "blocks": [
            {"type": "op_add", "label": "{} + {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 0}], "shape": "reporter_diamond"},
            {"type": "op_subtract", "label": "{} - {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 0}], "shape": "reporter_diamond"},
            {"type": "op_multiply", "label": "{} × {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 0}], "shape": "reporter_diamond"},
            {"type": "op_divide", "label": "{} ÷ {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 1}], "shape": "reporter_diamond"},
            {"type": "op_random", "label": "{} முதல் {} வரை சீரற்ற", "args": [{"name": "min", "type": "number", "default": 1}, {"name": "max", "type": "number", "default": 10}], "shape": "reporter_diamond"},
            {"type": "op_gt", "label": "{} > {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 0}], "shape": "boolean_diamond"},
            {"type": "op_lt", "label": "{} < {}", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 0}], "shape": "boolean_diamond"},
            {"type": "op_eq", "label": "{} = {}", "args": [{"name": "a", "type": "text", "default": ""}, {"name": "b", "type": "text", "default": ""}], "shape": "boolean_diamond"},
            {"type": "op_and", "label": "{} மற்றும் {}", "args": [{"name": "a", "type": "boolean", "default": True}, {"name": "b", "type": "boolean", "default": True}], "shape": "boolean_diamond"},
            {"type": "op_or", "label": "{} அல்லது {}", "args": [{"name": "a", "type": "boolean", "default": True}, {"name": "b", "type": "boolean", "default": True}], "shape": "boolean_diamond"},
            {"type": "op_not", "label": "{} இல்லை", "args": [{"name": "a", "type": "boolean", "default": True}], "shape": "boolean_diamond"},
            {"type": "op_join", "label": "{} இணை {}", "args": [{"name": "a", "type": "text", "default": "ஹலோ "}, {"name": "b", "type": "text", "default": "உலகம்"}], "shape": "reporter_diamond"},
            {"type": "op_mod", "label": "{} % {} மீதி", "args": [{"name": "a", "type": "number", "default": 0}, {"name": "b", "type": "number", "default": 1}], "shape": "reporter_diamond"},
            {"type": "op_round", "label": "{} ஐ தோராயமாக்கு", "args": [{"name": "a", "type": "number", "default": 0}], "shape": "reporter_diamond"},
        ]
    },
    "variables": {
        "name": "மாறிகள் (Variables)",
        "color": "#FF8C1A",
        "icon": "📦",
        "blocks": [
            {"type": "var_set", "label": "{} ஐ {} ஆக அமை", "args": [{"name": "var", "type": "variable", "default": "my_var"}, {"name": "value", "type": "text", "default": "0"}], "shape": "statement"},
            {"type": "var_change", "label": "{} ஐ {} மாற்று", "args": [{"name": "var", "type": "variable", "default": "my_var"}, {"name": "value", "type": "number", "default": 1}], "shape": "statement"},
            {"type": "var_get", "label": "{}", "args": [{"name": "var", "type": "variable", "default": "my_var"}], "shape": "reporter"},
            {"type": "create_variable", "label": "{} மாறியை உருவாக்கு", "args": [{"name": "name", "type": "text", "default": "my_var"}], "shape": "statement"},
            {"type": "list_create", "label": "{} பட்டியலை உருவாக்கு", "args": [{"name": "name", "type": "text", "default": "my_list"}], "shape": "statement"},
            {"type": "list_add", "label": "{} பட்டியலில் {} சேர்", "args": [{"name": "list", "type": "variable", "default": "my_list"}, {"name": "value", "type": "text", "default": ""}], "shape": "statement"},
            {"type": "list_get", "label": "{} பட்டியலின் {} வது உருப்படி", "args": [{"name": "list", "type": "variable", "default": "my_list"}, {"name": "index", "type": "number", "default": 1}], "shape": "reporter"},
            {"type": "list_length", "label": "{} பட்டியலின் நீளம்", "args": [{"name": "list", "type": "variable", "default": "my_list"}], "shape": "reporter"},
        ]
    },
    "html_tags": {
        "name": "HTML டேக்ஸ் (HTML Tags)",
        "color": "#E74C3C",
        "icon": "🌐",
        "blocks": [
            {"type": "html_div", "label": "<div id='{}'>...</div>", "args": [{"name": "id", "type": "text", "default": "myDiv"}], "shape": "container"},
            {"type": "html_h1", "label": "<h1 id='{}'>...</h1>", "args": [{"name": "id", "type": "text", "default": "heading1"}], "shape": "container"},
            {"type": "html_h2", "label": "<h2 id='{}'>...</h2>", "args": [{"name": "id", "type": "text", "default": "heading2"}], "shape": "container"},
            {"type": "html_p", "label": "<p id='{}'>...</p>", "args": [{"name": "id", "type": "text", "default": "para1"}], "shape": "container"},
            {"type": "html_button", "label": "<button id='{}'>...</button>", "args": [{"name": "id", "type": "text", "default": "btn1"}], "shape": "container"},
            {"type": "html_input", "label": "<input id='{}' type='{}' />", "args": [{"name": "id", "type": "text", "default": "input1"}, {"name": "type", "type": "dropdown", "options": ["text", "number", "email", "password", "color", "date", "range"], "default": "text"}], "shape": "statement"},
            {"type": "html_img", "label": "<img id='{}' src='{}' />", "args": [{"name": "id", "type": "text", "default": "img1"}, {"name": "src", "type": "text", "default": "https://via.placeholder.com/150"}], "shape": "statement"},
            {"type": "html_a", "label": "<a id='{}' href='{}'>...</a>", "args": [{"name": "id", "type": "text", "default": "link1"}, {"name": "href", "type": "text", "default": "#"}], "shape": "container"},
            {"type": "html_span", "label": "<span id='{}'>...</span>", "args": [{"name": "id", "type": "text", "default": "span1"}], "shape": "container"},
            {"type": "html_ul", "label": "<ul id='{}'>...</ul>", "args": [{"name": "id", "type": "text", "default": "list1"}], "shape": "container"},
            {"type": "html_li", "label": "<li id='{}'>...</li>", "args": [{"name": "id", "type": "text", "default": "item1"}], "shape": "container"},
            {"type": "html_table", "label": "<table id='{}'>...</table>", "args": [{"name": "id", "type": "text", "default": "table1"}], "shape": "container"},
            {"type": "html_form", "label": "<form id='{}'>...</form>", "args": [{"name": "id", "type": "text", "default": "form1"}], "shape": "container"},
            {"type": "html_video", "label": "<video id='{}' src='{}'>...</video>", "args": [{"name": "id", "type": "text", "default": "video1"}, {"name": "src", "type": "text", "default": "video.mp4"}], "shape": "container"},
            {"type": "html_audio", "label": "<audio id='{}' src='{}'>...</audio>", "args": [{"name": "id", "type": "text", "default": "audio1"}, {"name": "src", "type": "text", "default": "audio.mp3"}], "shape": "container"},
            {"type": "html_canvas", "label": "<canvas id='{}' width='{}' height='{}'></canvas>", "args": [{"name": "id", "type": "text", "default": "canvas1"}, {"name": "w", "type": "number", "default": 400}, {"name": "h", "type": "number", "default": 300}], "shape": "statement"},
            {"type": "html_select", "label": "<select id='{}'>...</select>", "args": [{"name": "id", "type": "text", "default": "select1"}], "shape": "container"},
            {"type": "html_option", "label": "<option value='{}'>...</option>", "args": [{"name": "value", "type": "text", "default": "1"}], "shape": "container"},
            {"type": "html_label", "label": "<label for='{}'>...</label>", "args": [{"name": "for_id", "type": "text", "default": "input1"}], "shape": "container"},
            {"type": "html_textarea", "label": "<textarea id='{}'>...</textarea>", "args": [{"name": "id", "type": "text", "default": "textarea1"}], "shape": "container"},
            {"type": "html_style", "label": "<style id='{}'>...</style>", "args": [{"name": "id", "type": "text", "default": "style1"}], "shape": "container"},
            {"type": "html_script", "label": "<script id='{}'>...</script>", "args": [{"name": "id", "type": "text", "default": "script1"}], "shape": "container"},
            {"type": "html_nav", "label": "<nav id='{}'>...</nav>", "args": [{"name": "id", "type": "text", "default": "nav1"}], "shape": "container"},
            {"type": "html_header", "label": "<header id='{}'>...</header>", "args": [{"name": "id", "type": "text", "default": "header1"}], "shape": "container"},
            {"type": "html_footer", "label": "<footer id='{}'>...</footer>", "args": [{"name": "id", "type": "text", "default": "footer1"}], "shape": "container"},
            {"type": "html_section", "label": "<section id='{}'>...</section>", "args": [{"name": "id", "type": "text", "default": "section1"}], "shape": "container"},
            {"type": "html_article", "label": "<article id='{}'>...</article>", "args": [{"name": "id", "type": "text", "default": "article1"}], "shape": "container"},
            {"type": "html_main", "label": "<main id='{}'>...</main>", "args": [{"name": "id", "type": "text", "default": "main1"}], "shape": "container"},
        ]
    },
    "command": {
        "name": "கட்டளைகள் (Commands)",
        "color": "#2C3E50",
        "icon": "⚙️",
        "blocks": [
            {"type": "run_command", "label": "கட்டளை இயக்கு: {}", "args": [{"name": "cmd", "type": "text", "default": "echo Hello"}], "shape": "statement"},
            {"type": "run_python", "label": "Python குறியீடு இயக்கு", "args": [], "shape": "container"},
            {"type": "run_js", "label": "JavaScript குறியீடு இயக்கு", "args": [], "shape": "container"},
            {"type": "read_file", "label": "{} கோப்பை படி", "args": [{"name": "path", "type": "text", "default": "data.txt"}], "shape": "reporter"},
            {"type": "write_file", "label": "{} கோப்பில் {} எழுது", "args": [{"name": "path", "type": "text", "default": "output.txt"}, {"name": "content", "type": "text", "default": ""}], "shape": "statement"},
            {"type": "delete_file", "label": "{} கோப்பை நீக்கு", "args": [{"name": "path", "type": "text", "default": "temp.txt"}], "shape": "statement"},
            {"type": "create_dir", "label": "{} கோப்புறையை உருவாக்கு", "args": [{"name": "path", "type": "text", "default": "new_folder"}], "shape": "statement"},
        ]
    },
    "api": {
        "name": "API & நீட்டிப்புகள் (API & Extensions)",
        "color": "#00B894",
        "icon": "🔌",
        "blocks": [
            {"type": "http_get", "label": "GET {} ஐ அழை", "args": [{"name": "url", "type": "text", "default": "https://api.example.com/data"}], "shape": "reporter"},
            {"type": "http_post", "label": "POST {} க்கு {} அனுப்பு", "args": [{"name": "url", "type": "text", "default": "https://api.example.com/data"}, {"name": "body", "type": "text", "default": '{"key": "value"}'}], "shape": "reporter"},
            {"type": "custom_api", "label": "தனிப்பயன் API: {} {} {} ஆக", "args": [{"name": "method", "type": "dropdown", "options": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"}, {"name": "url", "type": "text", "default": "https://api.example.com"}, {"name": "headers", "type": "text", "default": '{"Content-Type": "application/json"}'}], "shape": "reporter"},
            {"type": "load_extension", "label": "{} நீட்டிப்பை ஏற்று", "args": [{"name": "ext_name", "type": "text", "default": "my_extension"}], "shape": "statement"},
            {"type": "create_extension", "label": "{} நீட்டிப்பை உருவாக்கு", "args": [{"name": "ext_name", "type": "text", "default": "my_extension"}], "shape": "statement"},
            {"type": "webhook", "label": "வெப்ஹூக்: {} அழைக்கப்படும்போது", "args": [{"name": "event", "type": "text", "default": "webhook_event"}], "shape": "hat"},
        ]
    },
    "html_attr": {
        "name": "HTML அடையாளங்காட்டிகள்",
        "color": "#6C5CE7",
        "icon": "🏷️",
        "blocks": [
            {"type": "set_attr", "label": "{} டேக்கின் {} அடையாளத்தை {} ஆக அமை", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "attr", "type": "text", "default": "class"}, {"name": "value", "type": "text", "default": "new-class"}], "shape": "statement"},
            {"type": "get_attr", "label": "{} டேக்கின் {} அடையாளத்தைப் பெறு", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "attr", "type": "text", "default": "class"}], "shape": "reporter"},
            {"type": "set_text", "label": "{} டேக்கின் உரையை {} ஆக அமை", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "text", "type": "text", "default": "புதிய உரை"}], "shape": "statement"},
            {"type": "set_html", "label": "{} டேக்கின் HTML ஐ {} ஆக அமை", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "html", "type": "text", "default": "<b>bold</b>"}], "shape": "statement"},
            {"type": "set_css", "label": "{} டேக்கின் CSS {} ஐ {} ஆக அமை", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "property", "type": "text", "default": "color"}, {"name": "value", "type": "text", "default": "red"}], "shape": "statement"},
            {"type": "hide_tag", "label": "{} டேக்கை மறை", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}], "shape": "statement"},
            {"type": "show_tag", "label": "{} டேக்கை காட்டு", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}], "shape": "statement"},
            {"type": "tag_var", "label": "{} -> {} (டேக்கை மாறியாக அமை)", "args": [{"name": "tag_id", "type": "tag_selector", "default": ""}, {"name": "var_name", "type": "text", "default": "element"}], "shape": "statement"},
        ]
    }
}

# ============================================================
# .shsb LANGUAGE DEFINITION
# ============================================================

SHSB_SPEC = {
    "name": "BlockTect .shsb Language",
    "version": "1.0.0",
    "extension": ".shsb",
    "description": "BlockTect Script format - a visual block programming language for Python & HTML",
    "syntax": {
        "block": "BLOCK block_type [args...]",
        "container": "CONTAINER block_type [args...]",
        "end": "END",
        "comment": "// comment",
        "variable": "$var_name",
        "list": "@list_name",
        "tag_ref": "#tag_id",
        "string": '"text"',
        "number": "123",
        "boolean": "true|false"
    },
    "events": [
        "when_green_flag",
        "when_key_pressed",
        "when_clicked",
        "when_page_load",
        "when_tag_clicked",
        "when_broadcast",
        "webhook"
    ],
    "operators": {
        "arithmetic": ["+", "-", "*", "/", "%"],
        "comparison": [">", "<", "=", "!=", ">=", "<="],
        "logical": ["and", "or", "not"],
        "string": ["join", "length", "substring"]
    }
}


# ============================================================
# SHSB PARSER & GENERATOR
# ============================================================

class SHSBParser:
    """Parser for .shsb format files"""
    
    @staticmethod
    def blocks_to_shsb(blocks_json):
        """Convert blocks JSON to .shsb text format"""
        lines = ["// BlockTect .shsb File", f"// Version: {SHSB_SPEC['version']}", "// Generated by BlockTect", ""]
        
        for block in blocks_json:
            block_type = block.get("type", "unknown")
            args = block.get("args", [])
            children = block.get("children", [])
            
            if block.get("shape") in ("container", "container_conditional", "container_if_else", "hat"):
                shape_prefix = "CONTAINER"
            else:
                shape_prefix = "BLOCK"
            
            args_str = " ".join(str(a) for a in args)
            lines.append(f"{shape_prefix} {block_type} {args_str}")
            
            if children:
                for child in children:
                    child_type = child.get("type", "unknown")
                    child_args = child.get("args", [])
                    child_args_str = " ".join(str(a) for a in child_args)
                    lines.append(f"  BLOCK {child_type} {child_args_str}")
                lines.append("END")
        
        return "\n".join(lines)
    
    @staticmethod
    def shsb_to_blocks(shsb_text):
        """Convert .shsb text format to blocks JSON"""
        blocks = []
        current_block = None
        stack = []
        
        for line in shsb_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            if parts[0] == "BLOCK" and len(parts) >= 2:
                block = {
                    "type": parts[1],
                    "args": parts[2:] if len(parts) > 2 else [],
                    "children": []
                }
                if current_block:
                    current_block["children"].append(block)
                else:
                    blocks.append(block)
            
            elif parts[0] == "CONTAINER" and len(parts) >= 2:
                block = {
                    "type": parts[1],
                    "args": parts[2:] if len(parts) > 2 else [],
                    "children": [],
                    "shape": "container"
                }
                if current_block:
                    stack.append(current_block)
                    current_block["children"].append(block)
                else:
                    blocks.append(block)
                current_block = block
            
            elif parts[0] == "END":
                if stack:
                    current_block = stack.pop()
                else:
                    current_block = None
        
        return blocks


# ============================================================
# CODE GENERATORS
# ============================================================

class CodeGenerator:
    """Generate Python/HTML code from blocks"""
    
    @staticmethod
    def generate_python(blocks, var_name="main"):
        """Generate Python code from blocks"""
        code = []
        code.append("#!/usr/bin/env python3")
        code.append("# Generated by BlockTect")
        code.append("")
        code.append("import time")
        code.append("import random")
        code.append("import os")
        code.append("import json")
        code.append("import requests")
        code.append("")
        
        # Track variables
        variables = set()
        html_elements = {}
        
        def process_blocks(block_list, indent=0):
            lines = []
            for block in block_list:
                btype = block.get("type", "")
                args = block.get("args", [])
                children = block.get("children", [])
                ind = "    " * indent
                
                if btype == "when_green_flag":
                    lines.append(f"def {var_name}():")
                    indent += 1
                    lines.extend(process_blocks(children, indent))
                    indent -= 1
                    lines.append("")
                    lines.append(f'if __name__ == "__main__":')
                    lines.append(f"    {var_name}()")
                
                elif btype == "say":
                    text = args[0] if len(args) > 0 else ""
                    seconds = args[1] if len(args) > 1 else "2"
                    lines.append(f"{ind}print({text})")
                    lines.append(f"{ind}time.sleep({seconds})")
                
                elif btype == "wait":
                    lines.append(f"{ind}time.sleep({args[0]})")
                
                elif btype == "repeat":
                    times = args[0] if args else "10"
                    lines.append(f"{ind}for _ in range(int({times})):")
                    lines.extend(process_blocks(children, indent + 1))
                
                elif btype == "forever":
                    lines.append(f"{ind}while True:")
                    lines.extend(process_blocks(children, indent + 1))
                
                elif btype == "if_then":
                    lines.append(f"{ind}if {args[0] if args else 'True'}:")
                    lines.extend(process_blocks(children, indent + 1))
                
                elif btype == "op_add":
                    return f"({args[0]} + {args[1]})"
                elif btype == "op_subtract":
                    return f"({args[0]} - {args[1]})"
                elif btype == "op_multiply":
                    return f"({args[0]} * {args[1]})"
                elif btype == "op_divide":
                    return f"({args[0]} / {args[1]})"
                
                elif btype == "var_set":
                    variables.add(args[0])
                    lines.append(f"{ind}{args[0]} = {args[1]}")
                
                elif btype == "var_change":
                    variables.add(args[0])
                    lines.append(f"{ind}{args[0]} += {args[1]}")
                
                elif btype == "var_get":
                    return args[0]
                
                elif btype == "run_command":
                    lines.append(f"{ind}os.system({args[0]})")
                
                elif btype == "read_file":
                    return f"open({args[0]}).read()"
                
                elif btype == "write_file":
                    lines.append(f"{ind}with open({args[0]}, 'w') as f:")
                    lines.append(f"{ind}    f.write({args[1]})")
                
                elif btype == "http_get":
                    lines.append(f"{ind}response = requests.get({args[0]})")
                    lines.append(f"{ind}data = response.json()")
                
                elif btype == "http_post":
                    lines.append(f"{ind}response = requests.post({args[0]}, json={args[1]})")
                    lines.append(f"{ind}data = response.json()")
                
                elif btype.startswith("op_"):
                    # Operator blocks return expressions
                    pass
                
                elif children:
                    lines.extend(process_blocks(children, indent))
            
            return lines
        
        generated = process_blocks(blocks)
        
        # Add variable declarations at top
        var_decls = []
        for v in variables:
            var_decls.append(f"{v} = None")
        if var_decls:
            code.extend(var_decls)
            code.append("")
        
        code.extend(generated)
        return "\n".join(code)
    
    @staticmethod
    def generate_html(blocks):
        """Generate HTML code from blocks"""
        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append('<html lang="ta">')
        html_parts.append("<head>")
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append("    <title>BlockTect Generated Page</title>")
        html_parts.append("    <style>")
        html_parts.append("        * { box-sizing: border-box; margin: 0; padding: 0; }")
        html_parts.append("        body { font-family: Arial, sans-serif; padding: 20px; }")
        html_parts.append("    </style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        def process_blocks(block_list, indent=1):
            lines = []
            for block in block_list:
                btype = block.get("type", "")
                args = block.get("args", [])
                children = block.get("children", [])
                ind = "    " * indent
                
                if btype.startswith("html_"):
                    tag_name = btype.replace("html_", "")
                    tag_id = args[0] if args else ""
                    
                    # Build attributes
                    attrs = f' id="{tag_id}"'
                    if btype == "html_input" and len(args) > 1:
                        attrs += f' type="{args[1]}"'
                    if btype == "html_img" and len(args) > 1:
                        attrs += f' src="{args[1]}"'
                    if btype == "html_a" and len(args) > 1:
                        attrs += f' href="{args[1]}"'
                    if btype == "html_video" and len(args) > 1:
                        attrs += f' src="{args[1]}"'
                    if btype == "html_audio" and len(args) > 1:
                        attrs += f' src="{args[1]}"'
                    if btype == "html_canvas" and len(args) > 1:
                        attrs += f' width="{args[1]}" height="{args[2] if len(args) > 2 else 300}"'
                    if btype == "html_label" and args:
                        attrs += f' for="{args[0]}"'
                    if btype == "html_option" and args:
                        attrs += f' value="{args[0]}"'
                    if btype == "html_textarea" and args:
                        pass
                    
                    if btype in ("html_input", "html_img", "html_canvas"):
                        lines.append(f"{ind}<{tag_name}{attrs} />")
                    elif children:
                        lines.append(f"{ind}<{tag_name}{attrs}>")
                        lines.extend(process_blocks(children, indent + 1))
                        lines.append(f"{ind}</{tag_name}>")
                    else:
                        lines.append(f"{ind}<{tag_name}{attrs}></{tag_name}>")
            
            return lines
        
        html_parts.extend(process_blocks(blocks))
        html_parts.append("</body>")
        html_parts.append("</html>")
        return "\n".join(html_parts)
    
    @staticmethod
    def generate_shsb(blocks):
        """Generate .shsb format"""
        return SHSBParser.blocks_to_shsb(blocks)


# ============================================================
# PROJECT MANAGER
# ============================================================

class ProjectManager:
    """Manage projects - save, load, export"""
    
    @staticmethod
    def save_project(name, data):
        """Save a project"""
        project_path = PROJECTS_DIR / f"{name}.blocktect"
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return str(project_path)
    
    @staticmethod
    def load_project(name):
        """Load a project"""
        project_path = PROJECTS_DIR / f"{name}.blocktect"
        if project_path.exists():
            with open(project_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    @staticmethod
    def list_projects():
        """List all projects"""
        projects = []
        for f in PROJECTS_DIR.glob("*.blocktect"):
            projects.append(f.stem)
        return projects
    
    @staticmethod
    def export_zip(name, blocks):
        """Export project as .zip with Python and HTML files"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add Python file
            py_code = CodeGenerator.generate_python(blocks)
            zf.writestr(f"{name}.py", py_code)
            
            # Add HTML file
            html_code = CodeGenerator.generate_html(blocks)
            zf.writestr(f"{name}.html", html_code)
            
            # Add .shsb file
            shsb_code = CodeGenerator.generate_shsb(blocks)
            zf.writestr(f"{name}.shsb", shsb_code)
            
            # Add README
            readme = f"""# {name}
Generated by BlockTect

## Files
- {name}.py - Python source code
- {name}.html - HTML source code
- {name}.shsb - BlockTect script format

## How to Run
### Python:
    python {name}.py

### HTML:
    Open {name}.html in a browser

### SHSB:
    Use BlockTect to load the .shsb file
"""
            zf.writestr("README.txt", readme)
        
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode()


# ============================================================
# HTML UI - THE COMPLETE FRONTEND
# ============================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ta">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlockTect - Visual Block Programming</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; overflow: hidden; height: 100vh; background: #F9F9F9; }

/* ===== MENU BAR ===== */
.menu-bar {
    background: linear-gradient(135deg, #4C97FF, #9966FF);
    color: white;
    padding: 8px 20px;
    display: flex;
    align-items: center;
    gap: 20px;
    height: 50px;
    -webkit-app-region: drag;
    user-select: none;
}
.menu-bar .logo { font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
.menu-bar .logo span { font-size: 24px; }
.menu-bar .menu-items { display: flex; gap: 5px; -webkit-app-region: no-drag; }
.menu-bar .menu-items button {
    background: rgba(255,255,255,0.15); border: none; color: white;
    padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 13px;
    transition: all 0.2s;
}
.menu-bar .menu-items button:hover { background: rgba(255,255,255,0.3); }
.menu-bar .project-name {
    margin-left: auto; font-size: 14px; opacity: 0.9;
    -webkit-app-region: no-drag;
}
.menu-bar .project-name input {
    background: rgba(255,255,255,0.2); border: none; color: white;
    padding: 4px 10px; border-radius: 4px; font-size: 14px; width: 150px;
}
.menu-bar .project-name input::placeholder { color: rgba(255,255,255,0.6); }

/* ===== MAIN LAYOUT ===== */
.main-container {
    display: flex;
    height: calc(100vh - 50px);
}

/* ===== CATEGORY SIDEBAR ===== */
.category-sidebar {
    width: 80px;
    background: #FFFFFF;
    border-right: 1px solid #E0E0E0;
    overflow-y: auto;
    flex-shrink: 0;
}
.category-item {
    padding: 12px 5px;
    text-align: center;
    cursor: pointer;
    font-size: 10px;
    border-bottom: 1px solid #F0F0F0;
    transition: all 0.2s;
    color: #575E75;
}
.category-item:hover { background: #E9EEF2; color: #4C97FF; }
.category-item.active { background: #E9EEF2; color: #4C97FF; }
.category-item .icon { font-size: 22px; display: block; margin-bottom: 3px; }
.category-item .label { font-size: 9px; line-height: 1.2; }

/* ===== BLOCKS PANEL ===== */
.blocks-panel {
    width: 260px;
    background: #F9F9F9;
    border-right: 1px solid #E0E0E0;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
}
.blocks-panel .panel-header {
    padding: 12px 15px;
    font-weight: bold;
    font-size: 14px;
    border-bottom: 1px solid #E0E0E0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.blocks-panel .panel-header .color-dot {
    width: 12px; height: 12px; border-radius: 50%; display: inline-block;
}
.blocks-list {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
}
/* ===== BLOCK ELEMENTS ===== */
.block-item {
    background: white;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    cursor: grab;
    font-size: 12px;
    border-left: 4px solid;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    transition: all 0.2s;
    user-select: none;
    position: relative;
    min-height: 38px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
}
.block-item:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}
.block-item:active { cursor: grabbing; }
.block-item .block-input {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    width: 60px;
    background: #f5f5f5;
    outline: none;
}
.block-item .block-input:focus { border-color: #4C97FF; background: white; }
.block-item .block-select {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 2px 4px;
    font-size: 11px;
    background: #f5f5f5;
    outline: none;
}
.block-item.hat-block {
    border-radius: 8px 8px 4px 4px;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(50% + 10px) calc(100% - 8px), 50% 100%, calc(50% - 10px) calc(100% - 8px), 0 calc(100% - 8px));
}
.block-item.reporter-block {
    border-radius: 20px;
    display: inline-flex;
    padding: 6px 16px;
}
.block-item.boolean-block {
    border-radius: 4px;
    display: inline-flex;
    padding: 6px 16px;
    transform: rotate(45deg);
}
.block-item.boolean-block > * { transform: rotate(-45deg); }
.block-item.diamond-block {
    clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
    padding: 20px 30px;
    display: inline-flex;
}
.block-item.container-block {
    border-bottom: 3px solid;
    border-radius: 8px 8px 4px 4px;
}

/* ===== WORKSPACE ===== */
.workspace {
    flex: 1;
    background: #FFFFFF;
    position: relative;
    overflow: hidden;
}
.workspace-canvas {
    width: 100%;
    height: 100%;
    position: relative;
    background-image: 
        linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px);
    background-size: 20px 20px;
}
.workspace-block {
    position: absolute;
    min-width: 150px;
    z-index: 10;
    cursor: move;
}
.workspace-block .block-content {
    background: white;
    border-radius: 8px;
    border-left: 4px solid;
    padding: 10px 14px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.12);
    font-size: 12px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    min-height: 38px;
}
.workspace-block .block-content:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
.workspace-block .delete-btn {
    position: absolute;
    top: -8px;
    right: -8px;
    width: 20px;
    height: 20px;
    background: #E74C3C;
    color: white;
    border: 2px solid white;
    border-radius: 50%;
    font-size: 10px;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 20;
}
.workspace-block:hover .delete-btn { display: flex; }
.workspace-block .children-area {
    margin-top: 5px;
    margin-left: 20px;
    border-left: 2px dashed #ddd;
    padding-left: 10px;
    min-height: 10px;
}

/* ===== RIGHT PANEL ===== */
.right-panel {
    width: 380px;
    background: #1E1E1E;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    border-left: 1px solid #333;
}
.right-panel .tabs {
    display: flex;
    background: #252526;
    border-bottom: 1px solid #333;
}
.right-panel .tabs button {
    flex: 1;
    padding: 10px;
    background: transparent;
    border: none;
    color: #999;
    cursor: pointer;
    font-size: 12px;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}
.right-panel .tabs button.active {
    color: #4C97FF;
    border-bottom-color: #4C97FF;
    background: #2A2A2A;
}
.right-panel .tab-content {
    flex: 1;
    overflow: auto;
    padding: 0;
}
.right-panel .tab-content pre {
    padding: 15px;
    font-size: 13px;
    line-height: 1.5;
    color: #D4D4D4;
    font-family: 'Consolas', 'Courier New', monospace;
    white-space: pre-wrap;
    margin: 0;
}
.right-panel .preview-frame {
    width: 100%;
    height: 100%;
    border: none;
    background: white;
}

/* ===== TAG EDITOR ===== */
.tag-editor-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}
.tag-editor-overlay.active { display: flex; }
.tag-editor {
    background: white;
    border-radius: 12px;
    width: 700px;
    max-height: 80vh;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.tag-editor .editor-header {
    padding: 15px 20px;
    background: #4C97FF;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.tag-editor .editor-header h3 { font-size: 16px; }
.tag-editor .editor-header .close-btn {
    background: none; border: none; color: white; font-size: 24px; cursor: pointer;
}
.tag-editor .editor-body {
    padding: 20px;
    max-height: calc(80vh - 60px);
    overflow-y: auto;
}
.tag-editor .editor-body .toolbar {
    display: flex;
    gap: 5px;
    margin-bottom: 15px;
    flex-wrap: wrap;
}
.tag-editor .editor-body .toolbar button {
    padding: 6px 12px;
    border: 1px solid #ddd;
    background: #f5f5f5;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
}
.tag-editor .editor-body .toolbar button:hover { background: #e0e0e0; }
.tag-editor .editor-body .tag-canvas {
    width: 100%;
    height: 300px;
    border: 2px dashed #ddd;
    border-radius: 8px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    background: white;
}
.tag-editor .editor-body .tag-props {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}
.tag-editor .editor-body .tag-props label {
    font-size: 12px;
    color: #666;
    display: block;
    margin-bottom: 3px;
}
.tag-editor .editor-body .tag-props input,
.tag-editor .editor-body .tag-props select {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 13px;
}

/* ===== EXTENSIONS BUTTON ===== */
.extensions-btn {
    position: fixed;
    bottom: 20px;
    right: 400px;
    z-index: 100;
}
.extensions-btn button {
    width: 50px; height: 50px;
    border-radius: 50%;
    background: #6C5CE7;
    color: white;
    border: none;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(108,92,231,0.4);
    transition: all 0.2s;
}
.extensions-btn button:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(108,92,231,0.6);
}

/* ===== TOAST NOTIFICATIONS ===== */
.toast {
    position: fixed;
    bottom: 80px;
    right: 420px;
    background: #333;
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 2000;
    display: none;
    animation: slideIn 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
@keyframes slideIn {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #aaa; }

/* ===== BOTTOM TOOLBAR ===== */
.bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: #2C2C2C;
    color: #999;
    display: flex;
    align-items: center;
    padding: 0 20px;
    font-size: 12px;
    z-index: 100;
    gap: 20px;
}
.bottom-bar .status { display: flex; align-items: center; gap: 6px; }
.bottom-bar .status .dot { width: 8px; height: 8px; border-radius: 50%; background: #59C059; display: inline-block; }
</style>
</head>
<body>

<!-- ===== MENU BAR ===== -->
<div class="menu-bar">
    <div class="logo"><span>🧊</span> BlockTect</div>
    <div class="menu-items">
        <button onclick="newProject()">✨ புதியது</button>
        <button onclick="saveProject()">💾 சேமி</button>
        <button onclick="loadProject()">📂 திற</button>
        <button onclick="exportZip()">📦 ஏற்றுமதி</button>
        <button onclick="runProject()">▶️ இயக்கு</button>
        <button onclick="showTagEditor()">🏷️ டேக் எடிட்டர்</button>
    </div>
    <div class="project-name">
        <input id="projectName" value="என்_ப்ராஜெக்ட்" placeholder="திட்டத்தின் பெயர்">
    </div>
</div>

<!-- ===== MAIN CONTAINER ===== -->
<div class="main-container">
    <!-- Category Sidebar -->
    <div class="category-sidebar" id="categorySidebar"></div>

    <!-- Blocks Panel -->
    <div class="blocks-panel" id="blocksPanel">
        <div class="panel-header" id="panelHeader">
            <span class="color-dot" id="catColorDot"></span>
            <span id="catName">தேர்வு செய்க</span>
        </div>
        <div class="blocks-list" id="blocksList"></div>
    </div>

    <!-- Workspace -->
    <div class="workspace" id="workspace">
        <div class="workspace-canvas" id="workspaceCanvas">
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:#bbb;pointer-events:none;">
                <div style="font-size:48px;margin-bottom:10px;">🧊</div>
                <div style="font-size:16px;">தொகுதிகளை இங்கு இழுத்து விடவும்</div>
                <div style="font-size:12px;margin-top:5px;">இடது பக்கத்திலிருந்து blocks-ஐ drag செய்யவும்</div>
            </div>
        </div>
    </div>

    <!-- Right Panel -->
    <div class="right-panel" id="rightPanel">
        <div class="tabs">
            <button class="active" onclick="switchTab('code')">Python</button>
            <button onclick="switchTab('html')">HTML</button>
            <button onclick="switchTab('shsb')">.shsb</button>
            <button onclick="switchTab('preview')">👁️ முன்னோட்டம்</button>
        </div>
        <div class="tab-content" id="tabCode">
            <pre id="codePreview">// Blocks-ஐ இணைக்கவும்\n// குறியீடு தானாக உருவாக்கப்படும்</pre>
        </div>
        <div class="tab-content" id="tabHtml" style="display:none;">
            <pre id="htmlPreview">// Blocks-ஐ இணைக்கவும்\n// HTML தானாக உருவாக்கப்படும்</pre>
        </div>
        <div class="tab-content" id="tabShsb" style="display:none;">
            <pre id="shsbPreview">// .shsb format preview</pre>
        </div>
        <div class="tab-content" id="tabPreview" style="display:none;">
            <iframe class="preview-frame" id="previewFrame" srcdoc="<html><body style='display:flex;align-items:center;justify-content:center;height:100vh;color:#999;font-family:sans-serif;'><p>Blocks-ஐ இணைத்து முன்னோட்டத்தை பார்க்கவும்</p></body></html>"></iframe>
        </div>
    </div>
</div>

<!-- ===== TAG EDITOR OVERLAY ===== -->
<div class="tag-editor-overlay" id="tagEditorOverlay">
    <div class="tag-editor">
        <div class="editor-header">
            <h3>🏷️ HTML டேக் எடிட்டர் - MS Paint Style</h3>
            <button class="close-btn" onclick="closeTagEditor()">&times;</button>
        </div>
        <div class="editor-body">
            <div class="toolbar">
                <button onclick="addTextTag()">A உரை</button>
                <button onclick="addShapeTag('rect')">▬ செவ்வகம்</button>
                <button onclick="addShapeTag('circle')">● வட்டம்</button>
                <button onclick="addShapeTag('line')">╱ கோடு</button>
                <button onclick="setTagColor()">🎨 நிறம்</button>
                <button onclick="setTagFont()">🔤 எழுத்துரு</button>
                <button onclick="setTagBold()">B தடிமன்</button>
                <button onclick="deleteSelectedTag()">🗑️ நீக்கு</button>
            </div>
            <div class="tag-canvas" id="tagCanvas">
                <canvas id="tagEditorCanvas" width="650" height="280"></canvas>
            </div>
            <div class="tag-props">
                <div>
                    <label>டேக் ஐடி</label>
                    <input id="tagIdInput" value="myTag" placeholder="தனிப்பட்ட ஐடி">
                </div>
                <div>
                    <label>டேக் வகை</label>
                    <select id="tagTypeSelect">
                        <option value="div">div</option>
                        <option value="span">span</option>
                        <option value="button">button</option>
                        <option value="p">p</option>
                        <option value="h1">h1</option>
                        <option value="h2">h2</option>
                        <option value="input">input</option>
                        <option value="img">img</option>
                        <option value="a">a</option>
                        <option value="label">label</option>
                    </select>
                </div>
                <div>
                    <label>CSS வகுப்பு</label>
                    <input id="tagClassInput" value="" placeholder="my-class">
                </div>
                <div>
                    <label>உரை / உள்ளடக்கம்</label>
                    <input id="tagContentInput" value="" placeholder="டேக் உள்ளடக்கம்">
                </div>
            </div>
            <div style="margin-top:15px;text-align:right;">
                <button onclick="applyTagToBlocks()" style="padding:8px 20px;background:#4C97FF;color:white;border:none;border-radius:6px;cursor:pointer;">✅ பயன்படுத்து</button>
            </div>
        </div>
    </div>
</div>

<!-- ===== TOAST ===== -->
<div class="toast" id="toast"></div>

<!-- ===== EXTENSIONS BUTTON ===== -->
<div class="extensions-btn">
    <button onclick="showExtensions()" title="நீட்டிப்புகள்">🔌</button>
</div>

<!-- ===== BOTTOM STATUS BAR ===== -->
<div class="bottom-bar">
    <div class="status"><span class="dot"></span> தயார்</div>
    <div id="blockCount">0 தொகுதிகள்</div>
    <div id="projectStatus">சேமிக்கப்படவில்லை</div>
</div>

<script>
// ============================================================
// BLOCKTECT CORE ENGINE
// ============================================================

let workspaceBlocks = [];
let blockIdCounter = 0;
let selectedCategory = 'motion';
let currentProject = null;
let tagEditorElements = [];
let tagEditorSelected = null;

const CATEGORIES = {
    motion: { name: 'இயக்கம்', icon: '➡️', color: '#4C97FF' },
    looks: { name: 'தோற்றம்', icon: '🎨', color: '#9966FF' },
    control: { name: 'கட்டுப்பாடு', icon: '🔀', color: '#FFAB19' },
    events: { name: 'நிகழ்வுகள்', icon: '⚡', color: '#FFBF00' },
    sensing: { name: 'உணர்தல்', icon: '📡', color: '#4CBFE6' },
    operators: { name: 'செயலிகள்', icon: '🔣', color: '#59C059' },
    variables: { name: 'மாறிகள்', icon: '📦', color: '#FF8C1A' },
    html_tags: { name: 'HTML டேக்ஸ்', icon: '🌐', color: '#E74C3C' },
    command: { name: 'கட்டளைகள்', icon: '⚙️', color: '#2C3E50' },
    api: { name: 'API & நீட்டிப்புகள்', icon: '🔌', color: '#00B894' },
    html_attr: { name: 'HTML அடையாளங்கள்', icon: '🏷️', color: '#6C5CE7' }
};

// Block definitions from server
let BLOCKS_DATA = {};

// ============================================================
// INITIALIZATION
// ============================================================

async function init() {
    await loadBlockDefinitions();
    renderCategorySidebar();
    selectCategory('motion');
    updateCodePreview();
}

async function loadBlockDefinitions() {
    try {
        const resp = await fetch('/api/blocks');
        const data = await resp.json();
        BLOCKS_DATA = data;
        // Build CATEGORIES from server data (name, color, icon)
        Object.entries(data).forEach(([key, cat]) => {
            if (!CATEGORIES[key]) CATEGORIES[key] = {};
            CATEGORIES[key].name = cat.name || CATEGORIES[key].name;
            CATEGORIES[key].color = cat.color || CATEGORIES[key].color;
            CATEGORIES[key].icon = cat.icon || CATEGORIES[key].icon;
        });
    } catch(e) {
        console.error('Failed to load blocks:', e);
    }
}

// ============================================================
// CATEGORY SIDEBAR
// ============================================================

function renderCategorySidebar() {
    const sidebar = document.getElementById('categorySidebar');
    sidebar.innerHTML = '';
    Object.entries(CATEGORIES).forEach(([key, cat]) => {
        const item = document.createElement('div');
        item.className = 'category-item' + (key === selectedCategory ? ' active' : '');
        item.innerHTML = `<span class="icon">${cat.icon}</span><span class="label">${cat.name}</span>`;
        item.onclick = () => selectCategory(key);
        sidebar.appendChild(item);
    });
}

function selectCategory(key) {
    selectedCategory = key;
    document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.category-item')[Object.keys(CATEGORIES).indexOf(key)]?.classList.add('active');
    
    const cat = CATEGORIES[key];
    document.getElementById('catColorDot').style.background = cat.color;
    document.getElementById('catName').textContent = cat.name;
    
    renderBlocks(key);
}

// ============================================================
// BLOCKS PANEL
// ============================================================

function renderBlocks(categoryKey) {
    const list = document.getElementById('blocksList');
    list.innerHTML = '';
    
    // BLOCKS_DATA[categoryKey] is {name, color, icon, blocks: [...]}
    const catData = BLOCKS_DATA[categoryKey] || {};
    const blocks = catData.blocks || [];
    blocks.forEach((block, idx) => {
        const el = document.createElement('div');
        el.className = 'block-item';
        el.style.borderLeftColor = CATEGORIES[categoryKey]?.color || '#999';
        
        if (block.shape === 'hat') el.classList.add('hat-block');
        if (block.shape === 'reporter' || block.shape === 'reporter_diamond') el.classList.add('reporter-block');
        if (block.shape === 'boolean' || block.shape === 'boolean_diamond') el.classList.add('boolean-block');
        if (block.shape === 'container' || block.shape === 'container_conditional' || block.shape === 'container_if_else') el.classList.add('container-block');
        
        // Build block label with inputs
        const label = block.label || block.type;
        const parts = label.split(/(\{\})/g);
        let argIndex = 0;
        
        parts.forEach(part => {
            if (part === '{}') {
                if (block.args && block.args[argIndex]) {
                    const arg = block.args[argIndex];
                    if (arg.type === 'dropdown' || arg.type === 'tag_selector') {
                        const select = document.createElement('select');
                        select.className = 'block-select';
                        if (arg.options) {
                            arg.options.forEach(opt => {
                                const optEl = document.createElement('option');
                                optEl.value = opt;
                                optEl.textContent = opt;
                                select.appendChild(optEl);
                            });
                        }
                        el.appendChild(select);
                    } else if (arg.type === 'variable') {
                        const select = document.createElement('select');
                        select.className = 'block-select';
                        ['my_var', 'my_list', 'counter', 'name'].forEach(v => {
                            const opt = document.createElement('option');
                            opt.value = v;
                            opt.textContent = v;
                            select.appendChild(opt);
                        });
                        el.appendChild(select);
                    } else {
                        const input = document.createElement('input');
                        input.className = 'block-input';
                        input.type = arg.type === 'number' ? 'number' : 'text';
                        input.value = arg.default !== undefined ? arg.default : '';
                        input.placeholder = arg.name || '';
                        el.appendChild(input);
                    }
                    argIndex++;
                }
            } else {
                el.appendChild(document.createTextNode(part));
            }
        });
        
        el.draggable = true;
        el.dataset.blockType = block.type;
        el.dataset.category = categoryKey;
        el.dataset.shape = block.shape || 'statement';
        
        el.ondragstart = (e) => {
            e.dataTransfer.setData('text/plain', JSON.stringify({
                type: block.type,
                category: categoryKey,
                shape: block.shape || 'statement',
                label: block.label,
                args: block.args || []
            }));
        };
        
        list.appendChild(el);
    });
}

// ============================================================
// WORKSPACE - DRAG & DROP
// ============================================================

const workspace = document.getElementById('workspaceCanvas');

workspace.addEventListener('dragover', (e) => {
    e.preventDefault();
});

workspace.addEventListener('drop', (e) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('text/plain');
    if (!data) return;
    
    try {
        const blockDef = JSON.parse(data);
        const rect = workspace.getBoundingClientRect();
        const x = e.clientX - rect.left - 75;
        const y = e.clientY - rect.top - 20;
        addBlockToWorkspace(blockDef, x, y);
    } catch(err) {
        console.error('Drop error:', err);
    }
});

function addBlockToWorkspace(blockDef, x, y) {
    const id = 'block_' + (++blockIdCounter);
    const cat = CATEGORIES[blockDef.category] || { color: '#999', icon: '📦' };
    
    const blockEl = document.createElement('div');
    blockEl.className = 'workspace-block';
    blockEl.id = id;
    blockEl.style.left = x + 'px';
    blockEl.style.top = y + 'px';
    
    const content = document.createElement('div');
    content.className = 'block-content';
    content.style.borderLeftColor = cat.color;
    
    // Build label
    const label = blockDef.label || blockDef.type;
    const parts = label.split(/(\{\})/g);
    let argIndex = 0;
    const argsValues = [];
    
    parts.forEach(part => {
        if (part === '{}') {
            if (blockDef.args && blockDef.args[argIndex]) {
                const arg = blockDef.args[argIndex];
                if (arg.type === 'dropdown' || arg.type === 'tag_selector') {
                    const select = document.createElement('select');
                    select.className = 'block-select';
                    select.dataset.argName = arg.name;
                    if (arg.options) {
                        arg.options.forEach(opt => {
                            const optEl = document.createElement('option');
                            optEl.value = opt;
                            optEl.textContent = opt;
                            select.appendChild(optEl);
                        });
                    }
                    content.appendChild(select);
                    argsValues.push(arg.default || '');
                } else if (arg.type === 'variable') {
                    const select = document.createElement('select');
                    select.className = 'block-select';
                    select.dataset.argName = arg.name;
                    ['my_var', 'my_list', 'counter', 'name'].forEach(v => {
                        const opt = document.createElement('option');
                        opt.value = v;
                        opt.textContent = v;
                        select.appendChild(opt);
                    });
                    content.appendChild(select);
                    argsValues.push(arg.default || '');
                } else {
                    const input = document.createElement('input');
                    input.className = 'block-input';
                    input.type = arg.type === 'number' ? 'number' : 'text';
                    input.value = arg.default !== undefined ? arg.default : '';
                    input.placeholder = arg.name || '';
                    input.dataset.argName = arg.name;
                    content.appendChild(input);
                    argsValues.push(input.value);
                }
                argIndex++;
            }
        } else {
            content.appendChild(document.createTextNode(part));
        }
    });
    
    // Children area for container blocks
    if (blockDef.shape === 'container' || blockDef.shape === 'container_conditional' || blockDef.shape === 'container_if_else') {
        const childrenArea = document.createElement('div');
        childrenArea.className = 'children-area';
        childrenArea.dataset.parentId = id;
        content.appendChild(childrenArea);
        
        childrenArea.addEventListener('dragover', (e) => e.preventDefault());
        childrenArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const data = e.dataTransfer.getData('text/plain');
            if (!data) return;
            try {
                const childBlock = JSON.parse(data);
                const childRect = childrenArea.getBoundingClientRect();
                const cx = 10;
                const cy = e.clientY - childRect.top;
                addChildBlock(id, childBlock, cx, cy);
            } catch(err) { console.error(err); }
        });
    }
    
    // Delete button
    const delBtn = document.createElement('div');
    delBtn.className = 'delete-btn';
    delBtn.innerHTML = '×';
    delBtn.onclick = () => removeBlock(id);
    blockEl.appendChild(delBtn);
    
    blockEl.appendChild(content);
    
    // Make draggable
    makeBlockDraggable(blockEl);
    
    workspace.appendChild(blockEl);
    workspaceBlocks.push({
        id: id,
        type: blockDef.type,
        category: blockDef.category,
        shape: blockDef.shape,
        x: x,
        y: y,
        children: []
    });
    
    updateBlockCount();
    updateCodePreview();
}

function addChildBlock(parentId, blockDef, x, y) {
    const parent = document.getElementById(parentId);
    if (!parent) return;
    
    const childrenArea = parent.querySelector('.children-area');
    if (!childrenArea) return;
    
    const id = 'block_' + (++blockIdCounter);
    const cat = CATEGORIES[blockDef.category] || { color: '#999' };
    
    const blockEl = document.createElement('div');
    blockEl.className = 'workspace-block';
    blockEl.id = id;
    blockEl.style.position = 'relative';
    blockEl.style.left = '0';
    blockEl.style.top = '0';
    blockEl.style.marginBottom = '5px';
    
    const content = document.createElement('div');
    content.className = 'block-content';
    content.style.borderLeftColor = cat.color;
    
    const label = blockDef.label || blockDef.type;
    const parts = label.split(/(\{\})/g);
    let argIndex = 0;
    
    parts.forEach(part => {
        if (part === '{}') {
            if (blockDef.args && blockDef.args[argIndex]) {
                const arg = blockDef.args[argIndex];
                if (arg.type === 'dropdown' || arg.type === 'tag_selector') {
                    const select = document.createElement('select');
                    select.className = 'block-select';
                    if (arg.options) {
                        arg.options.forEach(opt => {
                            const optEl = document.createElement('option');
                            optEl.value = opt;
                            optEl.textContent = opt;
                            select.appendChild(optEl);
                        });
                    }
                    content.appendChild(select);
                } else if (arg.type === 'variable') {
                    const select = document.createElement('select');
                    select.className = 'block-select';
                    ['my_var', 'my_list', 'counter', 'name'].forEach(v => {
                        const opt = document.createElement('option');
                        opt.value = v;
                        opt.textContent = v;
                        select.appendChild(opt);
                    });
                    content.appendChild(select);
                } else {
                    const input = document.createElement('input');
                    input.className = 'block-input';
                    input.type = arg.type === 'number' ? 'number' : 'text';
                    input.value = arg.default !== undefined ? arg.default : '';
                    input.placeholder = arg.name || '';
                    content.appendChild(input);
                }
                argIndex++;
            }
        } else {
            content.appendChild(document.createTextNode(part));
        }
    });
    
    const delBtn = document.createElement('div');
    delBtn.className = 'delete-btn';
    delBtn.innerHTML = '×';
    delBtn.onclick = () => removeBlock(id);
    blockEl.appendChild(delBtn);
    blockEl.appendChild(content);
    childrenArea.appendChild(blockEl);
    
    // Update data
    const parentBlock = workspaceBlocks.find(b => b.id === parentId);
    if (parentBlock) {
        parentBlock.children = parentBlock.children || [];
        parentBlock.children.push({
            id: id,
            type: blockDef.type,
            category: blockDef.category,
            shape: blockDef.shape
        });
    }
    
    updateBlockCount();
    updateCodePreview();
}

function removeBlock(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
    workspaceBlocks = workspaceBlocks.filter(b => b.id !== id);
    updateBlockCount();
    updateCodePreview();
}

function makeBlockDraggable(el) {
    let isDragging = false;
    let startX, startY, origX, origY;
    
    el.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
        if (e.target.closest('.delete-btn')) return;
        
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        origX = parseInt(el.style.left) || 0;
        origY = parseInt(el.style.top) || 0;
        el.style.zIndex = 100;
        el.style.cursor = 'grabbing';
        
        const onMove = (me) => {
            if (!isDragging) return;
            const dx = me.clientX - startX;
            const dy = me.clientY - startY;
            el.style.left = (origX + dx) + 'px';
            el.style.top = (origY + dy) + 'px';
        };
        
        const onUp = () => {
            isDragging = false;
            el.style.cursor = '';
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            
            // Update position in data
            const block = workspaceBlocks.find(b => b.id === el.id);
            if (block) {
                block.x = parseInt(el.style.left) || 0;
                block.y = parseInt(el.style.top) || 0;
            }
            updateCodePreview();
        };
        
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
}

// ============================================================
// CODE GENERATION
// ============================================================

function collectBlocksData() {
    const blocks = [];
    document.querySelectorAll('.workspace-canvas > .workspace-block').forEach(el => {
        const blockData = getBlockData(el);
        if (blockData) blocks.push(blockData);
    });
    return blocks;
}

function getBlockData(el) {
    const content = el.querySelector('.block-content');
    if (!content) return null;
    
    const type = workspaceBlocks.find(b => b.id === el.id)?.type || 'unknown';
    const args = [];
    const children = [];
    
    content.querySelectorAll('.block-input, .block-select').forEach(input => {
        args.push(input.value);
    });
    
    const childrenArea = content.querySelector('.children-area');
    if (childrenArea) {
        childrenArea.querySelectorAll(':scope > .workspace-block').forEach(child => {
            const childData = getBlockData(child);
            if (childData) children.push(childData);
        });
    }
    
    return { type, args, children };
}

function updateCodePreview() {
    const blocks = collectBlocksData();
    generatePython(blocks);
    generateHtml(blocks);
    generateShsb(blocks);
    updatePreview(blocks);
}

async function generatePython(blocks) {
    try {
        const resp = await fetch('/api/generate/python', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks })
        });
        const data = await resp.json();
        document.getElementById('codePreview').textContent = data.code || '// Error generating code';
    } catch(e) {
        document.getElementById('codePreview').textContent = '// Error: ' + e.message;
    }
}

async function generateHtml(blocks) {
    try {
        const resp = await fetch('/api/generate/html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks })
        });
        const data = await resp.json();
        document.getElementById('htmlPreview').textContent = data.code || '<!-- Error generating HTML -->';
    } catch(e) {
        document.getElementById('htmlPreview').textContent = '<!-- Error: ' + e.message + ' -->';
    }
}

async function generateShsb(blocks) {
    try {
        const resp = await fetch('/api/generate/shsb', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks })
        });
        const data = await resp.json();
        document.getElementById('shsbPreview').textContent = data.code || '// Error generating .shsb';
    } catch(e) {
        document.getElementById('shsbPreview').textContent = '// Error: ' + e.message;
    }
}

function updatePreview(blocks) {
    const frame = document.getElementById('previewFrame');
    const htmlBlocks = blocks.filter(b => b.type.startsWith('html_'));
    if (htmlBlocks.length > 0) {
        // Generate preview HTML
        let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:Arial,sans-serif;padding:20px;}</style></head><body>';
        htmlBlocks.forEach(b => {
            const tag = b.type.replace('html_', '');
            const id = b.args[0] || '';
            const attrs = ` id="${id}"`;
            let inner = '';
            if (b.children && b.children.length > 0) {
                inner = b.children.map(c => c.args[0] || '').join(' ');
            }
            if (['input', 'img', 'canvas'].includes(tag)) {
                html += `  <${tag}${attrs} />\n`;
            } else {
                html += `  <${tag}${attrs}>${inner}</${tag}>\n`;
            }
        });
        html += '</body></html>';
        frame.srcdoc = html;
    } else {
        frame.srcdoc = "<html><body style='display:flex;align-items:center;justify-content:center;height:100vh;color:#999;font-family:sans-serif;'><p>HTML blocks-ஐ பயன்படுத்த�� முன்னோட்டம் பார்க்கவும்</p></body></html>";
    }
}

// ============================================================
// TAB SWITCHING
// ============================================================

function switchTab(tab) {
    document.querySelectorAll('.right-panel .tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.right-panel .tab-content').forEach(c => c.style.display = 'none');
    
    const tabMap = { code: 'tabCode', html: 'tabHtml', shsb: 'tabShsb', preview: 'tabPreview' };
    const tabEl = document.getElementById(tabMap[tab]);
    if (tabEl) tabEl.style.display = 'block';
    
    const btnIndex = ['code', 'html', 'shsb', 'preview'].indexOf(tab);
    document.querySelectorAll('.right-panel .tabs button')[btnIndex]?.classList.add('active');
}

// ============================================================
// PROJECT OPERATIONS
// ============================================================

async function saveProject() {
    const name = document.getElementById('projectName').value;
    const blocks = collectBlocksData();
    
    try {
        const resp = await fetch('/api/project/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, data: { blocks, name } })
        });
        const result = await resp.json();
        showToast('💾 ப்ராஜெக்ட் சேமிக்கப்பட்டது: ' + name);
        document.getElementById('projectStatus').textContent = 'சேமிக்கப்பட்டது';
    } catch(e) {
        showToast('❌ சேமிப்பதில் பிழை: ' + e.message);
    }
}

async function loadProject() {
    const name = prompt('திட்டத்தின் பெயரை உள்ளிடவும்:');
    if (!name) return;
    
    try {
        const resp = await fetch('/api/project/load/' + encodeURIComponent(name));
        const data = await resp.json();
        if (data.error) {
            showToast('❌ திட்டம் கிடைக்கவில்லை');
            return;
        }
        // Clear workspace and load
        clearWorkspace();
        if (data.blocks) {
            data.blocks.forEach(b => {
                addBlockToWorkspace(b, b.x || 100, b.y || 100);
            });
        }
        document.getElementById('projectName').value = name;
        showToast('📂 திட்டம் திறக்கப்பட்டது: ' + name);
    } catch(e) {
        showToast('❌ திறப்பதில் பிழை: ' + e.message);
    }
}

async function exportZip() {
    const name = document.getElementById('projectName').value;
    const blocks = collectBlocksData();
    
    try {
        const resp = await fetch('/api/export/zip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, blocks })
        });
        const data = await resp.json();
        
        // Download the zip
        const link = document.createElement('a');
        link.download = name + '.zip';
        link.href = 'data:application/zip;base64,' + data.zip;
        link.click();
        showToast('📦 ஏற்றுமதி செய்யப்பட்டது: ' + name + '.zip');
    } catch(e) {
        showToast('❌ ஏற்றுமதியில் பிழை: ' + e.message);
    }
}

async function runProject() {
    const blocks = collectBlocksData();
    try {
        const resp = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks })
        });
        const data = await resp.json();
        showToast('▶️ ' + (data.message || 'இயக்கப்பட்டது'));
    } catch(e) {
        showToast('❌ இயக்குவதில் பிழை: ' + e.message);
    }
}

function newProject() {
    if (workspaceBlocks.length > 0) {
        if (!confirm('தற்போதைய ப்ராஜெக்ட் இழக்கப்படும். புதியதாக தொடங்கவா?')) return;
    }
    clearWorkspace();
    document.getElementById('projectName').value = 'என்_ப்ராஜெக்ட்';
    document.getElementById('projectStatus').textContent = 'சேமிக்கப்படவில்லை';
    showToast('✨ புதிய ப்ராஜெக்ட் தொடங்கப்பட்டது');
}

function clearWorkspace() {
    document.querySelectorAll('.workspace-canvas > .workspace-block').forEach(el => el.remove());
    workspaceBlocks = [];
    updateBlockCount();
    updateCodePreview();
}

// ============================================================
// TAG EDITOR
// ============================================================

function showTagEditor() {
    document.getElementById('tagEditorOverlay').classList.add('active');
    initTagCanvas();
}

function closeTagEditor() {
    document.getElementById('tagEditorOverlay').classList.remove('active');
}

let tagCanvasCtx = null;

function initTagCanvas() {
    const canvas = document.getElementById('tagEditorCanvas');
    tagCanvasCtx = canvas.getContext('2d');
    tagCanvasCtx.fillStyle = 'white';
    tagCanvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    tagCanvasCtx.strokeStyle = '#f0f0f0';
    tagCanvasCtx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 20) {
        tagCanvasCtx.beginPath();
        tagCanvasCtx.moveTo(x, 0);
        tagCanvasCtx.lineTo(x, canvas.height);
        tagCanvasCtx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 20) {
        tagCanvasCtx.beginPath();
        tagCanvasCtx.moveTo(0, y);
        tagCanvasCtx.lineTo(canvas.width, y);
        tagCanvasCtx.stroke();
    }
    
    tagCanvasCtx.fillStyle = '#999';
    tagCanvasCtx.font = '14px Arial';
    tagCanvasCtx.textAlign = 'center';
    tagCanvasCtx.fillText('டேக் டிசைனை இங்கே வரையவும் (Paint போல)', canvas.width/2, canvas.height/2);
}

function addTextTag() {
    const canvas = document.getElementById('tagEditorCanvas');
    const ctx = tagCanvasCtx;
    const text = prompt('உரையை உள்ளிடவும்:', 'என் உரை');
    if (!text) return;
    
    ctx.fillStyle = '#333';
    ctx.font = '24px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(text, 50 + Math.random() * 100, 50 + Math.random() * 100);
    
    tagEditorElements.push({ type: 'text', content: text, x: 50, y: 50 });
}

function addShapeTag(shape) {
    const canvas = document.getElementById('tagEditorCanvas');
    const ctx = tagCanvasCtx;
    const x = 50 + Math.random() * 200;
    const y = 50 + Math.random() * 150;
    
    ctx.strokeStyle = '#4C97FF';
    ctx.lineWidth = 3;
    
    if (shape === 'rect') {
        ctx.strokeRect(x, y, 100, 60);
        ctx.fillStyle = 'rgba(76,151,255,0.1)';
        ctx.fillRect(x, y, 100, 60);
    } else if (shape === 'circle') {
        ctx.beginPath();
        ctx.arc(x + 30, y + 30, 30, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = 'rgba(76,151,255,0.1)';
        ctx.fill();
    } else if (shape === 'line') {
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + 80, y + 60);
        ctx.stroke();
    }
}

function setTagColor() {
    const color = prompt('நிறத்தை உள்ளிடவும் (hex, rgb அல்லது பெயர்):', '#FF5733');
    if (color) {
        tagCanvasCtx.fillStyle = color;
        tagCanvasCtx.strokeStyle = color;
    }
}

function setTagFont() {
    const font = prompt('எழுத்துரு அளவை உள்ளிடவும் (px):', '24px Arial');
    if (font) {
        tagCanvasCtx.font = font;
    }
}

function setTagBold() {
    tagCanvasCtx.font = 'bold ' + tagCanvasCtx.font;
}

function deleteSelectedTag() {
    tagCanvasCtx.clearRect(0, 0, 650, 280);
    initTagCanvas();
    tagEditorElements = [];
}

function applyTagToBlocks() {
    const tagId = document.getElementById('tagIdInput').value || 'myTag';
    const tagType = document.getElementById('tagTypeSelect').value;
    const tagClass = document.getElementById('tagClassInput').value;
    const tagContent = document.getElementById('tagContentInput').value;
    
    // Add an HTML block to workspace
    const blockDef = {
        type: 'html_' + tagType,
        category: 'html_tags',
        shape: 'statement',
        label: '<' + tagType + " id='" + tagId + "'>...</" + tagType + '>',
        args: [
            { name: 'id', type: 'text', default: tagId },
            { name: 'class', type: 'text', default: tagClass }
        ]
    };
    
    addBlockToWorkspace(blockDef, 100 + Math.random() * 200, 100 + Math.random() * 200);
    showToast('🏷️ டேக் சேர்க்கப்பட்டது: #' + tagId);
    closeTagEditor();
}

// ============================================================
// EXTENSIONS
// ============================================================

async function showExtensions() {
    const extName = prompt('நீட்டிப்பின் பெயரை உள்ளிடவும் (புதிதாக உருவாக்க / ஏற்ற):', 'my_extension');
    if (!extName) return;
    
    try {
        const resp = await fetch('/api/extension/load/' + encodeURIComponent(extName));
        const data = await resp.json();
        if (data.error) {
            // Create new extension
            const createResp = await fetch('/api/extension/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: extName })
            });
            const result = await createResp.json();
            showToast('🔌 நீட்டிப்பு உருவாக்கப்பட்டது: ' + extName);
        } else {
            showToast('🔌 நீட்டிப்பு ஏற்றப்பட்டது: ' + extName);
        }
    } catch(e) {
        showToast('❌ நீட்டிப்பு பிழை: ' + e.message);
    }
}

// ============================================================
// UTILITIES
// ============================================================

function updateBlockCount() {
    const count = document.querySelectorAll('.workspace-canvas > .workspace-block').length;
    document.getElementById('blockCount').textContent = count + ' தொகுதிகள்';
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
"""


# ============================================================
# HTTP REQUEST HANDLER
# ============================================================

class BlockTectHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for BlockTect API and UI"""
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/":
            self.send_html(HTML_TEMPLATE)
        elif path == "/api/blocks":
            self.send_json(BLOCK_CATEGORIES)
        elif path.startswith("/api/project/load/"):
            name = urllib.parse.unquote(path.split("/api/project/load/")[1])
            project = ProjectManager.load_project(name)
            if project:
                self.send_json(project)
            else:
                self.send_json({"error": "Project not found"}, 404)
        elif path.startswith("/api/extension/load/"):
            name = urllib.parse.unquote(path.split("/api/extension/load/")[1])
            ext_path = EXTENSIONS_DIR / f"{name}.json"
            if ext_path.exists():
                with open(ext_path) as f:
                    self.send_json(json.load(f))
            else:
                self.send_json({"error": "Extension not found"}, 404)
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body) if body else {}
        
        if path == "/api/generate/python":
            blocks = data.get("blocks", [])
            code = CodeGenerator.generate_python(blocks)
            self.send_json({"code": code})
        
        elif path == "/api/generate/html":
            blocks = data.get("blocks", [])
            code = CodeGenerator.generate_html(blocks)
            self.send_json({"code": code})
        
        elif path == "/api/generate/shsb":
            blocks = data.get("blocks", [])
            code = CodeGenerator.generate_shsb(blocks)
            self.send_json({"code": code})
        
        elif path == "/api/project/save":
            name = data.get("name", "project")
            project_data = data.get("data", {})
            path = ProjectManager.save_project(name, project_data)
            self.send_json({"success": True, "path": path})
        
        elif path == "/api/export/zip":
            name = data.get("name", "project")
            blocks = data.get("blocks", [])
            zip_b64 = ProjectManager.export_zip(name, blocks)
            self.send_json({"zip": zip_b64})
        
        elif path == "/api/run":
            blocks = data.get("blocks", [])
            # Generate and optionally run
            py_code = CodeGenerator.generate_python(blocks)
            temp_file = DATA_DIR / "temp_run.py"
            with open(temp_file, "w") as f:
                f.write(py_code)
            try:
                result = subprocess.run([sys.executable, str(temp_file)], 
                                      capture_output=True, text=True, timeout=10)
                output = result.stdout + result.stderr
                self.send_json({"message": "✅ இயக்கப்பட்டது", "output": output})
            except subprocess.TimeoutExpired:
                self.send_json({"message": "⏱️ நேரம் முடிந்தது"})
            except Exception as e:
                self.send_json({"message": f"❌ பிழை: {str(e)}"})
        
        elif path == "/api/extension/create":
            name = data.get("name", "extension")
            ext_data = {
                "name": name,
                "version": "1.0.0",
                "blocks": []
            }
            with open(EXTENSIONS_DIR / f"{name}.json", "w") as f:
                json.dump(ext_data, f, indent=2)
            self.send_json({"success": True, "message": f"Extension '{name}' created"})
        
        else:
            self.send_error(404, "Not Found")
    
    def send_html(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(content.encode()))
        self.end_headers()
        self.wfile.write(content.encode())
    
    def send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(content.encode()))
        self.end_headers()
        self.wfile.write(content.encode())
    
    def log_message(self, format, *args):
        # Quieter logging
        pass


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """Start BlockTect server"""
    print("""
    ╔═══════════════════════════════════════════╗
    ║           🧊 BlockTect v1.0.0             ║
    ║   Visual Block Programming for Python     ║
    ║          & HTML - தமிழில்!                ║
    ╚═══════════════════════════════════════════╝
    """)
    
    print(f"  🌐 Server: http://{HOST}:{PORT}")
    print(f"  📂 Projects: {PROJECTS_DIR}")
    print(f"  🔌 Extensions: {EXTENSIONS_DIR}")
    print(f"\n  ▶️  Open browser and start coding!")
    print(f"  Press Ctrl+C to stop\n")
    
    # Open browser
    webbrowser.open(f"http://{HOST}:{PORT}")
    
    # Start server
    server = socketserver.TCPServer((HOST, PORT), BlockTectHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 BlockTect நிறுத்தப்பட்டது. மீண்டும் சந்திப்போம்!")
        server.server_close()


if __name__ == "__main__":
    main()
