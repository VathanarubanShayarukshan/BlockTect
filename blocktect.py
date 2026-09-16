#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 BlockTect — Scratch-style Block IDE for Python + HTML webapps
=====================================================================
 A single-file desktop app (tkinter) that lets you build web apps and
 desktop tools using Scratch-like drag & drop blocks. Code is generated
 as real Python (backend) + HTML/CSS/JS (frontend).

 Features
 --------
 * Scratch 3 look & feel (categories, colored blocks, drag & snap)
 * All classic Scratch categories: Events, Control, Motion, Looks,
   Sound, Sensing, Operators, Variables, My Blocks
 * NEW: HTML tag blocks (top 100 tags, unique ids), page-load & click
   events, tag variables  [] -> []  , property access  tag . prop ->
 * NEW: OS command execution, file read/write, external API (GET/POST),
   JSON parsing, arrays, extension packs ([2] button)
 * Preview panel (HTML source + live browser) & Python console
 * Export: .shsb (own language), .zip (py+html+bat/sh), standalone
   run scripts

 CLI usage
 ---------
   python blocktect.py                  # launch the IDE (GUI)
   python blocktect.py export app.shsb  outdir   # headless export
   python blocktect.py run    app.shsb           # headless run
   python blocktect.py info                      # list blocks/packs

 .shsb = "Scratch-Hybrid Script Blocks" (JSON based)
=====================================================================
"""

import json
import os
import re
import sys
import time
import uuid
import zipfile
import shutil
import threading
import subprocess
import webbrowser
import tempfile
import platform

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog, font as tkfont
    HAS_TK = True
except Exception:  # headless
    HAS_TK = False

# ------------------------------------------------------------------
# 0. Constants
# ------------------------------------------------------------------
APP_NAME = "BlockTect"
SHSB_MAGIC = "shsb"
SHSB_VERSION = "1.0"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".blocktect_settings.json")

# Scratch-like category colours
CAT_COLORS = {
    "Events":      "#FFBF00",
    "Control":     "#FFAB19",
    "Motion":      "#4C97FF",
    "Looks":       "#9966FF",
    "Sound":       "#CF63CF",
    "Sensing":     "#5CB1D6",
    "Operators":   "#59C059",
    "Variables":   "#FF8C1A",
    "Arrays":      "#E8732A",
    "HTML":        "#00A8A8",
    "API":         "#00897B",
    "System":      "#616161",
    "My Blocks":   "#FF6680",
    "Math":        "#3CB371",
    "Text":        "#9370DB",
    "Game":        "#FF6B81",
    "IoT":         "#2F9E44",
}

# Ordered category list (shown in the left bar)
CORE_CATEGORIES = [
    "Events", "Control", "Motion", "Looks", "Sound", "Sensing",
    "Operators", "Variables", "Arrays", "HTML", "API", "System",
    "My Blocks",
]

# HTML top-100 most used tags
TOP_TAGS = [
    "html", "head", "body", "title", "meta", "link", "style", "script",
    "div", "span", "p", "a", "img", "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td",
    "form", "input", "button", "select", "option", "textarea", "label",
    "header", "footer", "nav", "main", "section", "article", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "br", "hr", "strong", "em", "b", "i", "u", "small", "sub", "sup",
    "mark", "code", "pre", "blockquote", "figure", "figcaption",
    "video", "audio", "source", "canvas", "iframe", "embed", "object",
    "picture", "svg", "progress", "meter", "details", "summary",
    "dialog", "menu", "fieldset", "legend", "datalist", "output",
    "optgroup", "map", "area", "template", "time", "address", "cite",
    "abbr", "del", "ins", "s", "q", "wbr", "bdi", "bdo", "data",
    "ruby", "rt", "rp", "noscript", "base", "param", "track",
]

STYLE_PROPS = {
    "color", "background", "background-color", "font-size", "font-family",
    "font-weight", "font-style", "text-align", "text-decoration",
    "margin", "margin-top", "margin-left", "margin-right", "margin-bottom",
    "padding", "padding-top", "padding-left", "padding-right", "padding-bottom",
    "border", "border-radius", "display", "position", "top", "left", "right",
    "bottom", "width", "height", "min-width", "min-height", "max-width",
    "max-height", "opacity", "z-index", "overflow", "float", "clear",
    "transform", "transition", "animation", "box-shadow", "cursor",
    "visibility", "line-height", "letter-spacing", "word-spacing", "white-space",
}

TEXT_PROPS = {"text", "intext", "innertext", "innerHTML", "html", "value", "title", "placeholder"}

# Packs (extension system). Each pack adds more blocks.
PACKS = {
    "Math":   {"desc": "Extra math blocks (sqrt, abs, round, pow, max/min)", "blocks": {}},
    "Text":   {"desc": "Text helpers (upper, lower, contains, replace)", "blocks": {}},
    "Game":   {"desc": "Mini game blocks (sprites, random position, score)", "blocks": {}},
    "IoT":    {"desc": "Magicbit-style simulation (LED, sensor, motor, display)", "blocks": {}},
}


# ------------------------------------------------------------------
# 1. Block definitions
#    label: text with {field} placeholders
#    fields: list of (kind, key, default, options)
#        kind = text | dropdown | diamond | tag | color
#    shape: hat | stack | end | reporter | bool
#    py: python template (None = no code)
# ------------------------------------------------------------------
def _dd(options):
    return ("dropdown", None, options[0], options)


def _diamond(placeholder="..."):
    return ("diamond", None, placeholder, None)


def _text(default="", width=None):
    return ("text", None, default, width)


def _tag(default=""):
    return ("tag", None, default, None)


def _color(default="#ff0000"):
    return ("color", None, default, None)


BLOCK_DEFS = {}

# ------------------------- Events -------------------------
BLOCK_DEFS.update({
    "when_loaded": dict(cat="Events", shape="hat",
        label="when page loads",
        fields=[], py=""),
    "when_clicked": dict(cat="Events", shape="hat",
        label="when tag {tag} clicked",
        fields=[_tag()], py=""),
    "when_changed": dict(cat="Events", shape="hat",
        label="when input {tag} changed",
        fields=[_tag()], py=""),
    "when_key": dict(cat="Events", shape="hat",
        label="when key {key} pressed",
        fields=[_dd(["any", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                     "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w",
                     "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8",
                     "9", "Enter", "Space", "ArrowUp", "ArrowDown", "ArrowLeft",
                     "ArrowRight"])], py=""),
    "broadcast": dict(cat="Events", shape="stack",
        label="broadcast {msg}",
        fields=[_text("message")], py="EVENT_QUEUE.append({msg})"),
    "when_receive": dict(cat="Events", shape="hat",
        label="when I receive {msg}",
        fields=[_text("message")], py=""),
})

# ------------------------- Control -------------------------
BLOCK_DEFS.update({
    "wait": dict(cat="Control", shape="stack",
        label="wait {secs} seconds",
        fields=[_text("1")], py="time.sleep(float({secs}))"),
    "repeat": dict(cat="Control", shape="stack",
        label="repeat {n}",
        fields=[_text("10")], py="for _rep in range(int({n})):"),
    "end_repeat": dict(cat="Control", shape="end",
        label="end repeat", fields=[], py=""),
    "forever": dict(cat="Control", shape="stack",
        label="forever", fields=[], py="while True:"),
    "end_forever": dict(cat="Control", shape="end",
        label="end forever", fields=[], py=""),
    "if": dict(cat="Control", shape="stack",
        label="if {cond} then",
        fields=[_diamond("condition")], py="if {cond}:"),
    "else": dict(cat="Control", shape="stack",
        label="else", fields=[], py="else:"),
    "end_if": dict(cat="Control", shape="end",
        label="end if", fields=[], py=""),
    "while": dict(cat="Control", shape="stack",
        label="while {cond}",
        fields=[_diamond("condition")], py="while {cond}:"),
    "end_while": dict(cat="Control", shape="end",
        label="end while", fields=[], py=""),
    "stop_all": dict(cat="Control", shape="stack",
        label="stop all", fields=[], py="return"),
    "stop_script": dict(cat="Control", shape="stack",
        label="stop this script", fields=[], py="return"),
})

# ------------------------- Motion (web animation) ----------
BLOCK_DEFS.update({
    "anim_move": dict(cat="Motion", shape="stack",
        label="move tag {tag} by x {dx} y {dy}",
        fields=[_tag(), _text("10"), _text("0")],
        py="move_tag({tag}, float({dx}), float({dy}))"),
    "anim_goto": dict(cat="Motion", shape="stack",
        label="go to tag {tag} x {x} y {y}",
        fields=[_tag(), _text("0"), _text("0")],
        py="goto_tag({tag}, float({x}), float({y}))"),
    "anim_rotate": dict(cat="Motion", shape="stack",
        label="rotate tag {tag} by {deg} degrees",
        fields=[_tag(), _text("15")],
        py="rotate_tag({tag}, float({deg}))"),
    "anim_glide": dict(cat="Motion", shape="stack",
        label="glide tag {tag} to x {x} y {y} in {s}s",
        fields=[_tag(), _text("0"), _text("0"), _text("1")],
        py="glide_tag({tag}, float({x}), float({y}), float({s}))"),
    "anim_grow": dict(cat="Motion", shape="stack",
        label="change size of tag {tag} by {n}",
        fields=[_tag(), _text("10")],
        py="scale_tag({tag}, float({n}))"),
})

# ------------------------- Looks ----------------------------
BLOCK_DEFS.update({
    "say": dict(cat="Looks", shape="stack",
        label="say {value}",
        fields=[_diamond("text")], py="say({value})"),
    "show_tag": dict(cat="Looks", shape="stack",
        label="show tag {tag}", fields=[_tag()], py="show_tag({tag})"),
    "hide_tag": dict(cat="Looks", shape="stack",
        label="hide tag {tag}", fields=[_tag()], py="hide_tag({tag})"),
    "set_text": dict(cat="Looks", shape="stack",
        label="set text of tag {tag} to {value}",
        fields=[_tag(), _diamond("text")], py="set_text({tag}, {value})"),
    "set_style": dict(cat="Looks", shape="stack",
        label="set style of tag {tag} {prop} to {value}",
        fields=[_tag(), _dd(sorted(STYLE_PROPS)), _diamond("value")],
        py="set_style({tag}, {prop!r}, {value})"),
    "set_color": dict(cat="Looks", shape="stack",
        label="set color of tag {tag} to {color}",
        fields=[_tag(), _color()], py="set_style({tag}, 'color', {color})"),
})

# ------------------------- Sound ----------------------------
BLOCK_DEFS.update({
    "beep": dict(cat="Sound", shape="stack",
        label="play beep {freq} Hz for {ms} ms",
        fields=[_text("880"), _text("200")],
        py="beep(float({freq}), float({ms}))"),
    "play_audio": dict(cat="Sound", shape="stack",
        label="play audio file {path}",
        fields=[_text("sound.mp3")], py="play_audio({path})"),
    "stop_sound": dict(cat="Sound", shape="stack",
        label="stop all sounds", fields=[], py="stop_audio()"),
})

# ------------------------- Sensing --------------------------
BLOCK_DEFS.update({
    "ask": dict(cat="Sensing", shape="stack",
        label="ask {question} and wait",
        fields=[_text("What's your name?")], py="ask_dialog({question})"),
    "read_input": dict(cat="Sensing", shape="reporter",
        label="value of input {tag}", fields=[_tag()],
        py="read_tag({tag})"),
    "key_pressed": dict(cat="Sensing", shape="bool",
        label="key {key} pressed?",
        fields=[_dd(["any", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                     "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w",
                     "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8",
                     "9", "Enter", "Space"])],
        py="key_pressed({key!r})"),
    "tag_exists": dict(cat="Sensing", shape="bool",
        label="tag {tag} exists?",
        fields=[_tag()], py="tag_exists({tag})"),
    "mouse_x": dict(cat="Sensing", shape="reporter",
        label="mouse x", fields=[], py="MOUSE.get('x', 0)"),
    "mouse_y": dict(cat="Sensing", shape="reporter",
        label="mouse y", fields=[], py="MOUSE.get('y', 0)"),
})

# ------------------------- Operators ------------------------
BLOCK_DEFS.update({
    "num": dict(cat="Operators", shape="reporter",
        label="{n}", fields=[_text("0")], py="{n}"),
    "text": dict(cat="Operators", shape="reporter",
        label="{s}", fields=[_text("text")], py="{s}"),
    "var": dict(cat="Operators", shape="reporter",
        label="{var}", fields=[("dropdown", "var", None, [])],
        py="VARS.get({var!r}, 0)"),
    "op": dict(cat="Operators", shape="reporter",
        label="{a} {op} {b}",
        fields=[_diamond("a"), _dd(["+", "-", "*", "/", "%", "**"]), _diamond("b")],
        py="({a} {op} {b})"),
    "join": dict(cat="Operators", shape="reporter",
        label="join {a} {b}",
        fields=[_diamond("a"), _diamond("b")],
        py="(str({a}) + str({b}))"),
    "compare": dict(cat="Operators", shape="bool",
        label="{a} {op} {b}",
        fields=[_diamond("a"), _dd([">", "<", "=", ">=", "<=", "!="]), _diamond("b")],
        py="({a} {op} {b})"),
    "and": dict(cat="Operators", shape="bool",
        label="{a} and {b}",
        fields=[_diamond("a"), _diamond("b")], py="({a} and {b})"),
    "or": dict(cat="Operators", shape="bool",
        label="{a} or {b}",
        fields=[_diamond("a"), _diamond("b")], py="({a} or {b})"),
    "not": dict(cat="Operators", shape="bool",
        label="not {a}", fields=[_diamond("a")], py="(not {a})"),
    "random_int": dict(cat="Operators", shape="reporter",
        label="random {lo} to {hi}",
        fields=[_text("1"), _text("100")],
        py="random.randint(int({lo}), int({hi}))"),
    "len_text": dict(cat="Operators", shape="reporter",
        label="length of {s}", fields=[_diamond("s")], py="len(str({s}))"),
    "letter_of": dict(cat="Operators", shape="reporter",
        label="letter {i} of {s}",
        fields=[_text("1"), _diamond("s")],
        py="(str({s})[{int({i})-1}] if 1 <= int({i}) <= len(str({s})) else '')"),
})

# ------------------------- Variables ------------------------
BLOCK_DEFS.update({
    "make_var": dict(cat="Variables", shape="stack",
        label="make variable {var}", fields=[_text("my var")], py=""),
    "set_var": dict(cat="Variables", shape="stack",
        label="set {var} to {value}",
        fields=[("dropdown", "var", None, []), _diamond("value")],
        py="VARS[{var!r}] = {value}"),
    "change_var": dict(cat="Variables", shape="stack",
        label="change {var} by {n}",
        fields=[("dropdown", "var", None, []), _text("1")],
        py="VARS[{var!r}] = VARS.get({var!r}, 0) + int({n})"),
    "show_var": dict(cat="Variables", shape="stack",
        label="show variable {var}",
        fields=[("dropdown", "var", None, [])],
        py="say('{var} = ' + str(VARS.get({var!r}, 0)))"),
})

# ------------------------- Arrays ---------------------------
BLOCK_DEFS.update({
    "make_array": dict(cat="Arrays", shape="stack",
        label="make array {arr} with {items}",
        fields=[_text("list1"), _text("1, 2, 3")],
        py=None),
    "add_item": dict(cat="Arrays", shape="stack",
        label="add {item} to array {arr}",
        fields=[_diamond("item"), _text("list1")],
        py="ARRS.setdefault({arr!r}, []).append({item})"),
    "get_item": dict(cat="Arrays", shape="reporter",
        label="item {i} of array {arr}",
        fields=[_text("1"), _text("list1")],
        py="(ARRS.get({arr!r}, [])[{int({i})-1}] if 1 <= int({i}) <= len(ARRS.get({arr!r}, [])) else '')"),
    "set_item": dict(cat="Arrays", shape="stack",
        label="set item {i} of array {arr} to {value}",
        fields=[_text("1"), _text("list1"), _diamond("value")],
        py="if 1 <= int({i}) <= len(ARRS.get({arr!r}, [])): ARRS[{arr!r}][int({i})-1] = {value}"),
    "len_array": dict(cat="Arrays", shape="reporter",
        label="length of array {arr}", fields=[_text("list1")],
        py="len(ARRS.get({arr!r}, []))"),
    "remove_item": dict(cat="Arrays", shape="stack",
        label="remove item {i} of array {arr}",
        fields=[_text("1"), _text("list1")],
        py="if 1 <= int({i}) <= len(ARRS.get({arr!r}, [])): del ARRS[{arr!r}][int({i})-1]"),
    "for_each": dict(cat="Arrays", shape="stack",
        label="for each {item} in array {arr}",
        fields=[_text("x"), _text("list1")],
        py="for {item} in ARRS.get({arr!r}, []):"),
    "end_for": dict(cat="Arrays", shape="end",
        label="end for", fields=[], py=""),
})

# ------------------------- HTML -----------------------------
BLOCK_DEFS.update({
    "add_tag": dict(cat="HTML", shape="stack",
        label="add tag {tag} to {parent} as {id}",
        fields=[_dd(TOP_TAGS), _tag("body"), _text("")],
        py=None),
    "append_tag": dict(cat="HTML", shape="stack",
        label="append tag {tag} to {parent}",
        fields=[_tag(), _tag("body")], py=None),
    "set_text_tag": dict(cat="HTML", shape="stack",
        label="set text of tag {tag} to {value}",
        fields=[_tag(), _diamond("value")], py="set_text({tag}, {value})"),
    "set_style_tag": dict(cat="HTML", shape="stack",
        label="set style of tag {tag} {prop} to {value}",
        fields=[_tag(), _dd(sorted(STYLE_PROPS)), _diamond("value")],
        py="set_style({tag}, {prop!r}, {value})"),
    "set_attr_tag": dict(cat="HTML", shape="stack",
        label="set attribute {attr} of tag {tag} to {value}",
        fields=[_text("href"), _tag(), _diamond("value")],
        py="set_attr({tag}, {attr!r}, {value})"),
    "read_tag": dict(cat="HTML", shape="reporter",
        label="value of tag {tag}", fields=[_tag()],
        py="read_tag({tag})"),
    "bind_var": dict(cat="HTML", shape="stack",
        label="{var} [] -> [] tag {tag}",
        fields=[("dropdown", "var", None, []), _tag()],
        py="bind_var({var!r}, {tag})"),
    "tag_prop": dict(cat="HTML", shape="stack",
        label="tag {tag} . {prop} -> {value}",
        fields=[_tag(), _text("intext"), _diamond("value")],
        py="tag_prop({tag}, {prop!r}, {value})"),
    "ask_prompt": dict(cat="HTML", shape="stack",
        label="popup ask {question} store in {var}",
        fields=[_text("Your name?"), ("dropdown", "var", None, [])],
        py="VARS[{var!r}] = ask_dialog({question})"),
})

# ------------------------- API ------------------------------
BLOCK_DEFS.update({
    "api_get": dict(cat="API", shape="reporter",
        label="API GET {url}", fields=[_text("https://api.example.com/data")],
        py="api_get({url})"),
    "api_post": dict(cat="API", shape="stack",
        label="API POST {url} data {data}",
        fields=[_text("https://api.example.com/data"), _text('{"key": "value"}')],
        py="api_post({url}, {data})"),
    "parse_json": dict(cat="API", shape="reporter",
        label="parse JSON {text}", fields=[_diamond("text")],
        py="parse_json({text})"),
    "json_key": dict(cat="API", shape="reporter",
        label="get key {key} of JSON {obj}",
        fields=[_text("name"), _diamond("obj")],
        py="json_key({obj}, {key})"),
})

# ------------------------- System ---------------------------
BLOCK_DEFS.update({
    "run_cmd": dict(cat="System", shape="stack",
        label="run command {cmd}",
        fields=[_text("echo hello")], py="run_cmd({cmd})"),
    "read_file": dict(cat="System", shape="reporter",
        label="read file {path}", fields=[_text("data.txt")],
        py="read_file({path})"),
    "write_file": dict(cat="System", shape="stack",
        label="write file {path} = {content}",
        fields=[_text("data.txt"), _diamond("content")],
        py="write_file({path}, {content})"),
    "append_file": dict(cat="System", shape="stack",
        label="append to file {path} = {content}",
        fields=[_text("data.txt"), _diamond("content")],
        py="append_file({path}, {content})"),
    "print_cmd": dict(cat="System", shape="stack",
        label="print {value}",
        fields=[_diamond("value")], py="say({value})"),
    "comment": dict(cat="System", shape="stack",
        label="// {note}", fields=[_text("comment")], py=""),
})

# ------------------------- My Blocks ------------------------
BLOCK_DEFS.update({
    "define": dict(cat="My Blocks", shape="hat",
        label="define {name}", fields=[_text("my_function")], py=""),
    "end_define": dict(cat="My Blocks", shape="end",
        label="end define", fields=[], py=""),
    "call": dict(cat="My Blocks", shape="stack",
        label="call {name}", fields=[_text("my_function")],
        py="call_fn({name})"),
})

# ------------------------- Pack blocks ----------------------
def _pack_blocks():
    # Math pack
    PACKS["Math"]["blocks"] = {
        "sqrt": dict(cat="Math", shape="reporter", label="sqrt of {a}",
                     fields=[_diamond("a")], py="math.sqrt(float({a}))"),
        "abs": dict(cat="Math", shape="reporter", label="abs of {a}",
                    fields=[_diamond("a")], py="abs({a})"),
        "round": dict(cat="Math", shape="reporter", label="round {a}",
                      fields=[_diamond("a")], py="round({a})"),
        "pow": dict(cat="Math", shape="reporter", label="{a} power {b}",
                    fields=[_diamond("a"), _diamond("b")], py="pow({a}, {b})"),
        "max": dict(cat="Math", shape="reporter", label="max of {a} and {b}",
                    fields=[_diamond("a"), _diamond("b")], py="max({a}, {b})"),
        "min": dict(cat="Math", shape="reporter", label="min of {a} and {b}",
                    fields=[_diamond("a"), _diamond("b")], py="min({a}, {b})"),
    }
    # Text pack
    PACKS["Text"]["blocks"] = {
        "upper": dict(cat="Text", shape="reporter", label="UPPERCASE {s}",
                      fields=[_diamond("s")], py="str({s}).upper()"),
        "lower": dict(cat="Text", shape="reporter", label="lowercase {s}",
                      fields=[_diamond("s")], py="str({s}).lower()"),
        "contains": dict(cat="Text", shape="bool", label="{s} contains {part}?",
                         fields=[_diamond("s"), _diamond("part")], py="(str({part}) in str({s}))"),
        "replace": dict(cat="Text", shape="reporter", label="replace {a} in {s} with {b}",
                        fields=[_diamond("s"), _diamond("a"), _diamond("b")],
                        py="str({s}).replace(str({a}), str({b}))"),
        "trim": dict(cat="Text", shape="reporter", label="trim {s}",
                     fields=[_diamond("s")], py="str({s}).strip()"),
    }
    # Game pack
    PACKS["Game"]["blocks"] = {
        "make_sprite": dict(cat="Game", shape="stack",
                            label="make sprite {name} as {tag}",
                            fields=[_text("player"), _text("div1")], py=None),
        "score_up": dict(cat="Game", shape="stack",
                         label="increase score by {n}", fields=[_text("1")],
                         py="VARS['score'] = VARS.get('score', 0) + {n}; say('score: ' + str(VARS['score']))"),
        "random_pos": dict(cat="Game", shape="stack",
                           label="jump tag {tag} to random position",
                           fields=[_tag()],
                           py="goto_tag({tag}, random.randint(0, 400), random.randint(0, 300))"),
        "game_over": dict(cat="Game", shape="stack",
                          label="game over", fields=[],
                          py="say('GAME OVER! score: ' + str(VARS.get('score', 0)))"),
    }
    # IoT pack (simulation)
    PACKS["IoT"]["blocks"] = {
        "led_on": dict(cat="IoT", shape="stack", label="LED {n} on",
                       fields=[_text("1")], py="sim_led({n}, True)"),
        "led_off": dict(cat="IoT", shape="stack", label="LED {n} off",
                        fields=[_text("1")], py="sim_led({n}, False)"),
        "read_sensor": dict(cat="IoT", shape="reporter", label="read sensor {s}",
                            fields=[_dd(["temperature", "light", "ultrasonic", "button", "potentiometer"])],
                            py="sim_sensor({s!r})"),
        "motor": dict(cat="IoT", shape="stack", label="motor {n} speed {v}",
                      fields=[_text("1"), _text("100")], py="sim_motor({n}, {v})"),
        "display": dict(cat="IoT", shape="stack", label="display {text} on screen",
                        fields=[_diamond("text")], py="sim_display({text})"),
        "buzzer": dict(cat="IoT", shape="stack", label="buzzer {freq} Hz {ms} ms",
                       fields=[_text("440"), _text("200")], py="beep(float({freq}), float({ms}))"),
    }


_pack_blocks()


# ------------------------------------------------------------------
# 2. Small helpers
# ------------------------------------------------------------------
def _uid():
    return uuid.uuid4().hex[:8]


def sanitize_code(value):
    """Render a block field value as a Python literal (string or number)."""
    v = str(value).strip()
    if re.fullmatch(r"[-+]?\d*\.?\d+", v):
        return v
    return json.dumps(v)


def _tag_ids(project_blocks):
    """All tag ids referenced by add_tag blocks (auto + custom)."""
    ids = set()
    for b in project_blocks.values():
        if b.get("type") == "add_tag":
            custom = (b.get("fields") or {}).get("id", "").strip()
            if custom:
                ids.add(custom)
    return sorted(ids)


def _var_names(project_blocks):
    names = set()
    for b in project_blocks.values():
        f = b.get("fields") or {}
        if b.get("type") == "make_var" and f.get("var", "").strip():
            names.add(f["var"].strip())
    return sorted(names)


def _arr_names(project_blocks):
    names = set()
    for b in project_blocks.values():
        f = b.get("fields") or {}
        if b.get("type") == "make_array" and f.get("arr", "").strip():
            names.add(f["arr"].strip())
        elif b.get("type") in ("add_item", "get_item", "set_item", "len_array",
                               "remove_item", "for_each") and f.get("arr", "").strip():
            names.add(f["arr"].strip())
    return sorted(names)


# ------------------------------------------------------------------
# 3. Code generator  (blocks -> index.html + app.py)
# ------------------------------------------------------------------
class TagNode:
    __slots__ = ("name", "tid", "text", "style", "attrs", "children")

    def __init__(self, name, tid):
        self.name = name
        self.tid = tid
        self.text = ""
        self.style = {}
        self.attrs = {}
        self.children = []

    def to_html(self, indent=0):
        pad = "  " * indent
        if self.name in ("br", "hr", "img", "input", "meta", "link", "source",
                         "area", "base", "param", "track", "embed", "wbr"):
            # void / self-closing-ish
            if self.name in ("br", "hr", "wbr"):
                return pad + "<%s>" % self.name
            attrs = self._attrs_str()
            return pad + "<%s%s>" % (self.name, attrs)
        attrs = self._attrs_str()
        open_t = "<%s%s>" % (self.name, attrs)
        if self.text:
            inner = self.text
        else:
            inner = "\n".join(c.to_html(indent + 1) for c in self.children)
            if inner:
                inner = "\n" + inner + "\n" + pad
        return "%s%s%s</%s>" % (pad, open_t, inner, self.name)

    def _attrs_str(self):
        parts = ['id="%s"' % self.tid]
        if self.name == "input" and self.text:
            parts.append('value="%s"' % self._esc(self.text))
        for k, v in sorted(self.attrs.items()):
            if k == "id":
                continue
            parts.append('%s="%s"' % (k, self._esc(v)))
        if self.style:
            style_txt = "; ".join("%s:%s" % (k, v) for k, v in self.style.items())
            parts.append('style="%s"' % self._esc(style_txt))
        return (" " + " ".join(parts)) if parts else ""

    @staticmethod
    def _esc(s):
        return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _is_void(name):
    return name in ("br", "hr", "wbr")


class Generator:
    def __init__(self, project):
        self.project = project
        self.blocks = project.get("blocks", {})
        self.lines = []
        self.indent = 0
        self.tag_counter = 0
        self.root = TagNode("body", "body")
        self.tag_nodes = {"body": self.root}
        self.load_chains = []
        self.click_handlers = []   # (tag, [block ids])
        self.change_handlers = []
        self.key_handlers = []     # (key, [block ids])
        self.receive_handlers = []
        self.defines = {}          # name -> [block ids]
        self.binds = []            # (var, tag)
        self.events_fired = False

    # ---------------- HTML tree ----------------
    def build_html(self):
        self.tag_counter = 0
        self.root = TagNode("body", "body")
        self.tag_nodes = {"body": self.root}
        for b in self.blocks.values():
            f = b.get("fields") or {}
            t = b.get("type")
            if t == "add_tag":
                name = f.get("tag", "div")
                parent_id = (f.get("parent") or "body").strip() or "body"
                custom = (f.get("id") or "").strip()
                tid = custom or self._auto_id(name)
                node = TagNode(name, tid)
                self.tag_nodes[tid] = node
                parent = self.tag_nodes.get(parent_id, self.root)
                parent.children.append(node)
            elif t == "append_tag":
                tid = (f.get("tag") or "").strip()
                parent_id = (f.get("parent") or "body").strip() or "body"
                node = self.tag_nodes.get(tid)
                parent = self.tag_nodes.get(parent_id, self.root)
                if node is not None and node not in parent.children:
                    parent.children.append(node)
            elif t == "set_text_tag":
                tid = (f.get("tag") or "").strip()
                node = self.tag_nodes.get(tid)
                if node is not None:
                    node.text = str(f.get("value") or "")
            elif t == "set_style_tag":
                tid = (f.get("tag") or "").strip()
                node = self.tag_nodes.get(tid)
                if node is not None:
                    node.style[(f.get("prop") or "color")] = str(f.get("value") or "")
            elif t == "set_attr_tag":
                tid = (f.get("tag") or "").strip()
                node = self.tag_nodes.get(tid)
                if node is not None:
                    node.attrs[(f.get("attr") or "data-x")] = str(f.get("value") or "")
        inner = "\n".join(c.to_html(1) for c in self.root.children)
        return self._wrap_html(inner)

    def _auto_id(self, name):
        self.tag_counter += 1
        return "%s%d" % (name, self.tag_counter)

    def _wrap_html(self, body_html):
        js = """\
<script>
function applyActions(acts){
  for(const a of acts){
    const el = document.getElementById(a.id); if(!el) continue;
    if(a.op==='set_text') el.textContent = a.value;
    else if(a.op==='set_style') el.style[a.prop] = a.value;
    else if(a.op==='set_attr') el.setAttribute(a.prop, a.value);
    else if(a.op==='show') el.style.display = '';
    else if(a.op==='hide') el.style.display = 'none';
    else if(a.op==='alert') alert(a.value);
  }
}
async function fire(event, id, key, x, y){
  try{
    const r = await fetch('/api/event', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({event:event, id:id, key:key, x:x, y:y})});
    const d = await r.json(); applyActions(d.actions);
  }catch(e){}
}
document.addEventListener('click', e=>{
  const t = e.target; if(t && t.id) fire('click', t.id, '', e.clientX, e.clientY);
});
document.addEventListener('change', e=>{
  const t = e.target; if(t && t.id) fire('change', t.id);
});
document.addEventListener('keydown', e=>{ fire('key', '', e.key); });
document.addEventListener('mousemove', e=>{
  const t = e.target;
  if(t && t.id){ window._mx = e.clientX; window._my = e.clientY; }
});
</script>"""
        css = "<style>body{font-family:Arial,Helvetica,sans-serif;margin:16px}div,p,button,img,span,a,li{transition:all .2s}</style>"
        return (
            "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>%s</title>\n%s\n</head>\n<body>\n%s\n%s\n</body>\n</html>"
            % (self.project.get("name", "BlockTect App"), css, body_html, js)
        )

    # ---------------- chains ----------------
    def _chain(self, bid):
        """Follow next links from a block id."""
        out = []
        seen = set()
        while bid and bid not in seen:
            seen.add(bid)
            b = self.blocks.get(bid)
            if not b:
                break
            out.append(b)
            bid = b.get("next")
        return out

    def _collect_handlers(self):
        for b in self.blocks.values():
            f = b.get("fields") or {}
            t = b.get("type")
            chain = self._chain(b.get("id"))
            if t == "when_loaded":
                self.load_chains.append(chain)
            elif t == "when_clicked":
                self.click_handlers.append(((f.get("tag") or "*").strip() or "*", chain))
            elif t == "when_changed":
                self.change_handlers.append(((f.get("tag") or "*").strip() or "*", chain))
            elif t == "when_key":
                self.key_handlers.append(((f.get("key") or "any").strip() or "any", chain))
            elif t == "when_receive":
                self.receive_handlers.append(((f.get("msg") or "").strip(), chain))
            elif t == "define":
                self.defines[(f.get("name") or "").strip()] = chain
            elif t == "bind_var":
                v = (f.get("var") or "").strip()
                tag = (f.get("tag") or "").strip()
                if v and tag:
                    self.binds.append((v, tag))

    # ---------------- expression ----------------
    def expr(self, block, ctx):
        t = block.get("type")
        d = BLOCK_DEFS.get(t)
        if not d:
            return "''"
        f = dict(block.get("fields") or {})
        slots = block.get("slots") or {}
        # map field key -> value or nested expr
        vals = {}
        for fkey, fval in f.items():
            vals[fkey] = fval
        for slot_key, child_id in slots.items():
            child = self.blocks.get(child_id)
            if child:
                vals[slot_key] = self.expr(child, ctx)
        py = d.get("py")
        if py is None:
            return "''"
        # sanitize: strings become literals, numbers stay numbers.
        # fields referenced with {key!r} keep their raw value (repr handles it).
        for k, v in list(vals.items()):
            if isinstance(v, str) and ("{%s!r}" % k) not in py:
                vals[k] = sanitize_code(v)
        try:
            return py.format(**vals)
        except Exception:
            return "''"

    # ---------------- python emission ----------------
    def emit(self, code):
        pad = "    " * self.indent
        for line in str(code).split("\n"):
            if line.strip():
                self.lines.append(pad + line)
            else:
                self.lines.append("")

    def gen_chain(self, chain):
        """Generate python for a linear chain, handling control openers/enders."""
        depth_stack = []
        for b in chain:
            t = b.get("type")
            d = BLOCK_DEFS.get(t, {})
            if t in ("end_if", "end_repeat", "end_forever", "end_while", "end_for", "end_define"):
                self.indent = max(0, self.indent - 1)
                continue
            if t == "else":
                self.indent = max(0, self.indent - 1)
                self.emit("else:")
                self.indent += 1
                continue
            py = d.get("py")
            if py is None and t not in ("make_var", "make_array", "make_sprite", "comment", "define"):
                # HTML-structure / special blocks are handled elsewhere
                if t == "make_var":
                    v = (b.get("fields") or {}).get("var", "").strip()
                    if v:
                        self.emit("VARS.setdefault(%s, 0)" % sanitize_code(v))
                elif t == "make_array":
                    f = b.get("fields") or {}
                    self.emit("ARRS.setdefault(%s, [])" % sanitize_code(f.get("arr", "").strip()))
                elif t == "comment":
                    continue
                elif t == "make_sprite":
                    continue
                continue
            if t == "make_var":
                v = (b.get("fields") or {}).get("var", "").strip()
                if v:
                    self.emit("VARS.setdefault(%s, 0)" % sanitize_code(v))
                continue
            if t == "make_array":
                f = b.get("fields") or {}
                arr = sanitize_code(f.get("arr", "").strip())
                items = (f.get("items") or "").strip()
                if items:
                    self.emit("ARRS[%s] = [x.strip() for x in %s.split(',')]" % (arr, sanitize_code(items)))
                else:
                    self.emit("ARRS.setdefault(%s, [])" % arr)
                continue
            if t == "comment":
                continue
            if t == "make_sprite":
                continue
            if t in ("if", "repeat", "forever", "while", "for_each"):
                code = self.expr(b, {})
                if t == "repeat":
                    self.emit("for _rep in range(int(%s)):" % code)
                elif t == "forever":
                    self.emit("while True:")
                elif t == "if":
                    self.emit("if %s:" % code)
                elif t == "while":
                    self.emit("while %s:" % code)
                elif t == "for_each":
                    f = b.get("fields") or {}
                    item = str(f.get("item") or "x").strip() or "x"
                    arr = sanitize_code(str(f.get("arr") or "").strip())
                    self.emit("for %s in ARRS.get(%s, []):" % (item, arr))
                self.indent += 1
                continue
            if t == "define":
                continue
            if t == "call":
                name = (b.get("fields") or {}).get("name", "").strip()
                self.emit("call_fn(%s)" % sanitize_code(name))
                continue
            if t in ("stop_all", "stop_script"):
                self.emit("return")
                continue
            # normal stack block
            self.emit(self.expr(b, {}))

    # ---------------- app.py ----------------
    def generate_app(self):
        self._collect_handlers()
        self.lines = []
        self.indent = 0

        H = []
        A = []
        # header
        H.append("#!/usr/bin/env python3")
        H.append("# Generated by BlockTect (shsb v%s)" % SHSB_VERSION)
        H.append("import json, os, sys, time, math, random, threading, subprocess, webbrowser, urllib.request")
        H.append("from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer")
        H.append("from urllib.parse import urlparse, parse_qs")
        H.append("")
        H.append("PORT = int(os.environ.get('PORT', '8000'))")
        H.append("VARS = {}")
        H.append("ARRS = {}")
        H.append("TAGS = {}")
        H.append("ACTIONS = []")
        H.append("LOGS = []")
        H.append("LAST_KEY = ''")
        H.append("MOUSE = {'x': 0, 'y': 0}")
        H.append("EVENT_QUEUE = []")
        H.append("")

        # runtime helpers
        A.append("def action(op, **kw): ACTIONS.append(dict(op=op, **kw))")
        A.append("def say(v): LOGS.append(str(v)); print('SAY:', v)")
        A.append("def beep(freq, ms): print('BEEP: %.0f Hz %.0f ms' % (freq, ms)); sys.stdout.write('\\a'); sys.stdout.flush()")
        A.append("def play_audio(path): print('PLAY:', path)")
        A.append("def stop_audio(): print('STOP SOUNDS')")
        A.append("def set_text(tid, v): TAGS.setdefault(tid, {})['text'] = str(v); action('set_text', id=tid, value=str(v))")
        A.append("def set_style(tid, p, v): TAGS.setdefault(tid, {})['style'] = dict(TAGS[tid].get('style', {})); TAGS[tid]['style'][p] = str(v); action('set_style', id=tid, prop=p, value=str(v))")
        A.append("def set_attr(tid, p, v): TAGS.setdefault(tid, {})['attrs'] = dict(TAGS[tid].get('attrs', {})); TAGS[tid]['attrs'][p] = str(v); action('set_attr', id=tid, prop=p, value=str(v))")
        A.append("def show_tag(tid): action('show', id=tid)")
        A.append("def hide_tag(tid): action('hide', id=tid)")
        A.append("def read_tag(tid): t = TAGS.get(tid, {}); return t.get('value', t.get('text', ''))")
        A.append("def tag_exists(tid): return tid in TAGS")
        A.append("def key_pressed(k): return (LAST_KEY == k) if k != 'any' else bool(LAST_KEY)")
        A.append("def move_tag(tid, dx, dy): t = TAGS.get(tid, {}); x = float(t.get('x', 0)) + dx; y = float(t.get('y', 0)) + dy; TAGS.setdefault(tid, {})['x'] = x; TAGS.setdefault(tid, {})['y'] = y; action('set_style', id=tid, prop='transform', value='translate(%dpx, %dpx)' % (x, y))")
        A.append("def goto_tag(tid, x, y): TAGS.setdefault(tid, {})['x'] = x; TAGS.setdefault(tid, {})['y'] = y; action('set_style', id=tid, prop='transform', value='translate(%dpx, %dpx)' % (x, y))")
        A.append("def rotate_tag(tid, deg): TAGS.setdefault(tid, {})['rot'] = float(TAGS[tid].get('rot', 0)) + deg; action('set_style', id=tid, prop='transform', value='rotate(%ddeg)' % TAGS[tid]['rot'])")
        A.append("def scale_tag(tid, n): TAGS.setdefault(tid, {})['scale'] = float(TAGS[tid].get('scale', 100)) + n; action('set_style', id=tid, prop='transform', value='scale(%f)' % (TAGS[tid]['scale'] / 100.0))")
        A.append("def glide_tag(tid, x, y, s): action('set_style', id=tid, prop='transition', value='all %ss' % s); goto_tag(tid, x, y)")
        A.append("def run_cmd(c): print('CMD:', c); r = subprocess.run(c, shell=True, capture_output=True, text=True); out = (r.stdout or '') + (r.stderr or ''); LOGS.append(out); print(out); return out.strip()")
        A.append("def read_file(p): f = open(p, 'r', encoding='utf-8'); d = f.read(); f.close(); return d")
        A.append("def write_file(p, c): f = open(p, 'w', encoding='utf-8'); f.write(str(c)); f.close(); print('WROTE:', p)")
        A.append("def append_file(p, c): f = open(p, 'a', encoding='utf-8'); f.write(str(c)); f.close(); print('APPENDED:', p)")
        A.append("def api_get(url): print('GET:', url); return urllib.request.urlopen(url, timeout=10).read().decode('utf-8', 'replace')")
        A.append("def api_post(url, data): print('POST:', url); req = urllib.request.Request(url, data=str(data).encode('utf-8'), method='POST'); return urllib.request.urlopen(req, timeout=10).read().decode('utf-8', 'replace')")
        A.append("def parse_json(s): return json.loads(s)")
        A.append("def json_key(obj, key): return obj.get(key) if isinstance(obj, dict) else None")
        A.append("def ask_dialog(q): import tkinter as tk2, tkinter.simpledialog; return tk2.simpledialog.askstring('BlockTect', q)")
        A.append("def tag_prop(tid, prop, value):")
        A.append("    p = prop.lower()")
        A.append("    if p in ('text', 'intext', 'innertext', 'innerhtml', 'html'): set_text(tid, value)")
        A.append("    elif p in ('value',): set_attr(tid, 'value', value); TAGS.setdefault(tid, {})['value'] = str(value)")
        A.append("    elif p in %s: set_style(tid, p, value)" % sorted(STYLE_PROPS))
        A.append("    else: set_attr(tid, prop, value)")
        A.append("def bind_var(v, tid): VARS[v] = read_tag(tid)")
        A.append("def call_fn(name): return FN_MAP.get(name, lambda: None)()")
        A.append("def sim_led(n, on): print('LED %s %s' % (n, 'ON' if on else 'OFF'))")
        A.append("def sim_sensor(s): import random as _r; return _r.uniform(20, 35) if s == 'temperature' else (_r.randint(0, 1023) if s != 'button' else _r.choice([0, 1]))")
        A.append("def sim_motor(n, v): print('MOTOR %s speed %s' % (n, v))")
        A.append("def sim_display(t): print('DISPLAY:', t)")
        A.append("")

        # tag state from html build
        self.emit("def sync_binds():")
        self.indent = 1
        if self.binds:
            for v, tag in self.binds:
                self.emit("bind_var(%s, %s)" % (sanitize_code(v), sanitize_code(tag)))
        else:
            self.emit("pass")
        self.indent = 0
        self.emit("")

        # event handler functions
        hdr = []

        def handler_fn(name, tag_expr, chains):
            self.emit("def %s(%s):" % (name, tag_expr))
            self.indent = 1
            self.emit("sync_binds()")
            for chain in chains:
                self.gen_chain(chain)
            self.indent = 0
            self.emit("")
            hdr.append(name)

        if self.load_chains:
            handler_fn("on_load", "", self.load_chains)
        if self.click_handlers:
            handler_fn("ev_click", "tag_id", [c for _, c in self.click_handlers])
        if self.change_handlers:
            handler_fn("ev_change", "tag_id", [c for _, c in self.change_handlers])
        if self.key_handlers:
            handler_fn("ev_key", "key", [c for _, c in self.key_handlers])
        if self.receive_handlers:
            handler_fn("ev_receive", "msg", [c for _, c in self.receive_handlers])

        # define functions
        self.lines.append("FN_MAP = {}")
        for name, chain in self.defines.items():
            fn = re.sub(r"\W", "_", name)[:30] or "fn_x"
            self.lines.append("def fn_%s():" % fn)
            self.indent = 1
            self.gen_chain(chain)
            self.indent = 0
            self.lines.append("FN_MAP[%s] = fn_%s" % (sanitize_code(name), fn))
        self.lines.append("")

        # index html
        self.lines.append("INDEX_HTML = %s" % sanitize_code(self.build_html()))
        self.lines.append("")

        # handler dispatch
        click_tags = sorted({t for t, _ in self.click_handlers})
        change_tags = sorted({t for t, _ in self.change_handlers})
        key_keys = sorted({k for k, _ in self.key_handlers})
        self.lines.append("CLICK_TAGS = %s" % click_tags)
        self.lines.append("CHANGE_TAGS = %s" % change_tags)
        self.lines.append("KEY_KEYS = %s" % key_keys)
        self.lines.append("RECV_MSGS = %s" % sorted({m for m, _ in self.receive_handlers}))
        self.lines.append("")
        self.lines.append("def dispatch(ev, tag, key):")
        self.lines.append("    ACTIONS.clear()")
        self.lines.append("    LOGS.clear()")
        self.lines.append("    global LAST_KEY")
        self.lines.append("    LAST_KEY = key or ''")
        self.lines.append("    if ev == 'click' and (tag in CLICK_TAGS or '*' in CLICK_TAGS): ev_click(tag)")
        self.lines.append("    if ev == 'change' and (tag in CHANGE_TAGS or '*' in CHANGE_TAGS): ev_change(tag)")
        self.lines.append("    if ev == 'key' and (key in KEY_KEYS or 'any' in KEY_KEYS): ev_key(key)")
        self.lines.append("    if ev == 'receive' and tag in RECV_MSGS: ev_receive(tag)")
        self.lines.append("    return {'actions': ACTIONS, 'logs': LOGS}")
        self.lines.append("")

        # HTTP server
        self.lines.append("class Handler(BaseHTTPRequestHandler):")
        self.lines.append("    def log_message(self, *a): pass")
        self.lines.append("    def do_GET(self):")
        self.lines.append("        p = urlparse(self.path).path")
        self.lines.append("        if p in ('/', '/index.html'):")
        self.lines.append("            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()")
        self.lines.append("            self.wfile.write(INDEX_HTML.encode('utf-8'))")
        self.lines.append("        else:")
        self.lines.append("            self.send_response(404); self.end_headers()")
        self.lines.append("    def do_POST(self):")
        self.lines.append("        n = int(self.headers.get('Content-Length') or 0)")
        self.lines.append("        raw = self.rfile.read(n) if n else b'{}'")
        self.lines.append("        try: body = json.loads(raw)")
        self.lines.append("        except Exception: body = {}")
        self.lines.append("        ev = body.get('event', ''); tag = body.get('id', ''); key = body.get('key', '')")
        self.lines.append("        try: res = dispatch(ev, tag, key)")
        self.lines.append("        except Exception as e:")
        self.lines.append("            import traceback; traceback.print_exc()")
        self.lines.append("            res = {'actions': [], 'logs': ['ERROR: ' + str(e)]}")
        self.lines.append("        data = json.dumps(res).encode('utf-8')")
        self.lines.append("        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()")
        self.lines.append("        self.wfile.write(data)")
        self.lines.append("")

        # main
        self.lines.append("def main():")
        self.lines.append("    if hasattr(sys, 'argv') and '--no-browser' in sys.argv: pass")
        self.lines.append("    srv = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)")
        self.lines.append("    print('BlockTect app running at http://127.0.0.1:%d/' % PORT)")
        self.lines.append("    print('Press Ctrl+C to stop')")
        self.lines.append("    def _open(): webbrowser.open('http://127.0.0.1:%d/index.html' % PORT)")
        self.lines.append("    threading.Timer(0.6, _open).start()")
        self.lines.append("    if 'on_load' in dir() and callable(globals().get('on_load')): on_load()")
        self.lines.append("    try: srv.serve_forever()")
        self.lines.append("    except KeyboardInterrupt: print('\\nStopped.')")
        self.lines.append("    srv.server_close()")
        self.lines.append("")
        self.lines.append("if __name__ == '__main__': main()")

        return "\n".join(H + A + self.lines)


def generate_project(project, outdir):
    """Generate index.html + app.py into outdir. Returns (html_path, py_path)."""
    os.makedirs(outdir, exist_ok=True)
    g = Generator(project)
    app_py = g.generate_app()
    py_path = os.path.join(outdir, "app.py")
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(app_py)
    # html embedded in app.py; also write standalone
    html = g.build_html()
    html_path = os.path.join(outdir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path, py_path


# ------------------------------------------------------------------
# 4. GUI — block data model & canvas editor
# ------------------------------------------------------------------
class Block:
    def __init__(self, btype, x=0, y=0, bid=None):
        self.id = bid or _uid()
        self.btype = btype
        self.x = x
        self.y = y
        self.fields = {}
        self.next_id = None
        self.prev_id = None
        self.slots = {}
        # canvas items
        self.shape_item = None
        self.label_items = []
        self.widgets = {}
        self.slot_items = {}

    def to_dict(self):
        return {
            "id": self.id, "type": self.btype, "x": self.x, "y": self.y,
            "fields": dict(self.fields), "next": self.next_id,
            "slots": dict(self.slots),
        }

    @staticmethod
    def from_dict(d):
        b = Block(d.get("type", "num"), d.get("x", 0), d.get("y", 0), d.get("id"))
        b.fields = dict(d.get("fields") or {})
        b.next_id = d.get("next")
        b.slots = dict(d.get("slots") or {})
        return b


class Canvas(tk.Canvas):
    """The script area with drag & drop, chaining and reporter docking."""

    def __init__(self, master, app, **kw):
        super().__init__(master, bg="#F9F9F9", highlightthickness=0, **kw)
        self.app = app
        self.blocks = {}  # id -> Block
        self._drag = None
        self._drag_dx = 0
        self._drag_dy = 0
        self._press = None
        self._max_x = 0
        self._max_y = 0
        self._auto_id = 0
        self.font = None
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Button-3>", self._on_right)
        self.bind("<Configure>", lambda e: self._ensure_region())
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")

    # ---------------- view helpers ----------------
    def _ensure_region(self):
        self.configure(scrollregion=(0, 0, max(self._max_x + 40, self.winfo_width()),
                                     max(self._max_y + 40, self.winfo_height())))

    def _on_wheel(self, e):
        if self.winfo_ismapped():
            self.yview_scroll(int(-e.delta / 120), "units")

    def add_block(self, b, at=None):
        if at:
            b.x, b.y = at
        self.blocks[b.id] = b
        self._auto_id += 1
        return b

    def reset(self):
        self.blocks.clear()
        self._drag = None
        self._max_x = 0
        self._max_y = 0
        self.delete("all")
        self._ensure_region()

    # ---------------- geometry ----------------
    def measure(self, b):
        """Estimate width/height of a block."""
        d = BLOCK_DEFS.get(b.btype, {})
        label = d.get("label", "")
        w = 24
        for part in re.split(r"(\{[^}]*\})", label):
            if not part:
                continue
            if part.startswith("{") and part.endswith("}"):
                key = part[1:-1]
                spec = next((f for f in d.get("fields", []) if f[1] == key), None)
                kind = spec[0] if spec else "text"
                if kind == "diamond":
                    w += 40
                elif kind == "dropdown":
                    w += 74
                elif kind == "tag":
                    w += 74
                elif kind == "color":
                    w += 40
                else:
                    w += 66
            else:
                w += self.font.measure(part) if self.font else (10 * len(part))
        return max(w, 120), 30

    def _depth_of(self, b):
        """Control-nesting depth for indentation (follows prev chain)."""
        depth = 0
        cur = b.prev_id
        while cur:
            pb = self.blocks.get(cur)
            if pb and pb.btype in ("if", "repeat", "forever", "while", "for_each", "else"):
                depth += 1
            cur = pb.prev_id if pb else None
        return depth

    # ---------------- rendering ----------------
    def render_all(self):
        self.delete("all")
        self._max_x = 0
        self._max_y = 0
        for b in self.blocks.values():
            if not b.prev_id:
                self._render_chain(b)
        self._ensure_region()

    def _render_chain(self, root):
        b = root
        while b:
            self._render_block(b)
            b = self.blocks.get(b.next_id) if b.next_id else None

    def _render_block(self, b):
        d = BLOCK_DEFS.get(b.btype, {})
        color = CAT_COLORS.get(d.get("cat", "Control"), "#FFAB19")
        shape = d.get("shape", "stack")
        label = d.get("label", "")
        indent = self._depth_of(b) * 22
        x = b.x + indent
        y = b.y
        w, h = self.measure(b)
        pad = 8

        # background shape
        item = None
        if shape == "hat":
            item = self.create_polygon(
                x, y + 10, x + w, y + 10, x + w, y + h,
                x, y + h, fill=color, outline="#3a3a3a", width=1, smooth=True)
        elif shape == "end":
            item = self.create_polygon(
                x, y, x + w, y, x + w, y + h - 8, x, y + h - 8,
                fill=color, outline="#3a3a3a", width=1, smooth=True)
        elif shape == "reporter":
            item = self.create_oval(x, y, x + w, y + h, fill=color, outline="#3a3a3a", width=1)
        elif shape == "bool":
            item = self.create_polygon(
                x + 8, y, x + w - 8, y, x + w, y + h / 2, x + w - 8, y + h, x + 8, y + h, x, y + h / 2,
                fill=color, outline="#3a3a3a", width=1, smooth=True)
        else:
            item = self.create_polygon(
                x + 8, y, x + w - 8, y, x + w, y + 8, x + w, y + h - 8,
                x + w - 8, y + h, x + 8, y + h, x, y + h - 8, x, y + 8,
                fill=color, outline="#3a3a3a", width=1, smooth=True)

        # notch / bump for stack blocks
        if shape == "stack":
            if b.prev_id:
                self.create_polygon(x + w / 2 - 7, y, x + w / 2 + 7, y,
                                    x + w / 2, y + 7, fill="#F9F9F9", outline="")
            if b.next_id:
                self.create_polygon(x + w / 2 - 7, y + h, x + w / 2 + 7, y + h,
                                    x + w / 2, y + h - 7, fill=color, outline="")

        self.tag_bind(item, ("blk", b.id))
        b.shape_item = item
        b.label_items = []
        b.widgets = {}
        b.slot_items = {}

        # label parts + field widgets
        cx = x + 10
        for part in re.split(r"(\{[^}]*\})", label):
            if not part:
                continue
            if part.startswith("{") and part.endswith("}"):
                key = part[1:-1]
                spec = next((f for f in d.get("fields", []) if f[1] == key), None)
                if not spec:
                    continue
                kind, _, default, opt = spec
                if kind == "diamond":
                    slot_id = self.create_polygon(
                        cx, y + h / 2 - 9, cx + 34, y + h / 2, cx, y + h / 2 + 9, cx - 34, y + h / 2,
                        fill="#FFFFFF", outline="#3a3a3a", width=1)
                    self.tag_bind(slot_id, ("slot", b.id, key))
                    b.slot_items[key] = slot_id
                    self.create_text(cx, y + h / 2, text=default or "…", fill="#888888", font=self.font)
                    child_id = b.slots.get(key)
                    if child_id and child_id in self.blocks:
                        cb = self.blocks[child_id]
                        cw, ch = self.measure(cb)
                        cb.x = cx - cw / 2
                        cb.y = y + h / 2 - ch / 2
                        self._render_block(cb)
                    cx += 40
                elif kind == "dropdown":
                    var = tk.StringVar(value=str(b.fields.get(key, default or "")))
                    combo = ttk.Combobox(self, textvariable=var, width=9,
                                         values=list(opt or []), state="readonly", font=self.font)
                    combo.bind("<<ComboboxSelected>>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    combo.bind("<FocusOut>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    self.create_window(cx, y + h / 2, window=combo, anchor="w")
                    b.widgets[key] = combo
                    cx += 80
                elif kind == "tag":
                    var = tk.StringVar(value=str(b.fields.get(key, default or "")))
                    combo = ttk.Combobox(self, textvariable=var, width=9,
                                         values=sorted(self._known_tags()) or [""], font=self.font)
                    combo.bind("<FocusOut>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    combo.bind("<Return>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    self.create_window(cx, y + h / 2, window=combo, anchor="w")
                    b.widgets[key] = combo
                    cx += 80
                elif kind == "color":
                    var = tk.StringVar(value=str(b.fields.get(key, default or "#ff0000")))
                    ent = tk.Entry(self, textvariable=var, width=6, relief="flat", font=self.font)
                    ent.bind("<FocusOut>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    self.create_window(cx, y + h / 2, window=ent, anchor="w")
                    b.widgets[key] = ent
                    cx += 50
                else:  # text
                    var = tk.StringVar(value=str(b.fields.get(key, default or "")))
                    ent = tk.Entry(self, textvariable=var, width=9, relief="flat", font=self.font)
                    ent.bind("<FocusOut>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    ent.bind("<Return>", lambda e, k=key, v=var: self._set_field(b, k, v.get()))
                    self.create_window(cx, y + h / 2, window=ent, anchor="w")
                    b.widgets[key] = ent
                    cx += 70
            else:
                t = self.create_text(cx, y + h / 2, text=part, anchor="w", fill="#2a2a2a", font=self.font)
                b.label_items.append(t)
                cx += self.font.measure(part) if self.font else (10 * len(part))

        self._max_x = max(self._max_x, x + w)
        self._max_y = max(self._max_y, y + h)

    def _known_tags(self):
        return _tag_ids(self.blocks)

    def _set_field(self, b, key, value):
        if b.id not in self.blocks:
            return
        b.fields[key] = value
        self.render_all()
        self.app.after_idle(self.app.refresh_code)

    # ---------------- interaction ----------------
    def _block_at(self, x, y):
        item = self.find_withtag("current")
        if not item:
            return None
        tags = self.gettags(item[0])
        if len(tags) >= 2 and tags[0] == "blk":
            return self.blocks.get(tags[1])
        return None

    def _on_press(self, e):
        item = self.find_withtag("current")
        if not item:
            self._drag = None
            return
        tags = self.gettags(item[0])
        if tags and tags[0] == "blk":
            b = self.blocks.get(tags[1])
            if b:
                self._drag = b
                self._drag_dx = b.x - e.x
                self._drag_dy = b.y - e.y
                # detach from chain
                if b.prev_id:
                    p = self.blocks.get(b.prev_id)
                    if p:
                        p.next_id = None
                    b.prev_id = None
                    self.render_all()
        elif tags and tags[0] == "slot":
            # pick up reporter already docked?
            b = self.blocks.get(tags[2]) if len(tags) > 2 else None
            self._drag = None

    def _on_motion(self, e):
        if self._drag:
            b = self._drag
            dx = (b.x - self._drag_dx)
            # move whole subtree
            b.x = e.x + self._drag_dx
            b.y = e.y + self._drag_dy
            self.render_all()

    def _on_release(self, e):
        if not self._drag:
            return
        b = self._drag
        self._drag = None
        self._snap(b)
        self.render_all()
        self.app.after_idle(self.app.refresh_code)

    def _snap(self, b):
        """Try to chain below a stack block or dock into a diamond slot."""
        # 1) reporter / bool -> try docking into diamond slots
        shape = BLOCK_DEFS.get(b.btype, {}).get("shape", "stack")
        if shape in ("reporter", "bool"):
            best = None
            best_d = 40
            for other in self.blocks.values():
                if other.id == b.id:
                    continue
                for skey, sitem in other.slot_items.items():
                    coords = self.coords(sitem)
                    if not coords:
                        continue
                    sx = sum(coords[0::2]) / (len(coords) / 2)
                    sy = sum(coords[1::2]) / (len(coords) / 2)
                    d = ((b.x - sx) ** 2 + (b.y - sy) ** 2) ** 0.5
                    if d < best_d:
                        best_d = d
                        best = (other, skey)
            if best:
                other, skey = best
                # remove from old slot
                for o in self.blocks.values():
                    if o.slots.get(skey) == b.id:
                        o.slots[skey] = None
                other.slots[skey] = b.id
                b.prev_id = None
                return
        # 2) stack block -> snap below another stack/hat/end block
        if shape in ("stack", "hat"):
            best = None
            best_d = 26
            for other in self.blocks.values():
                if other.id == b.id or other.btype in ("reporter", "bool", "else",):
                    continue
                ox, oy = other.x + self._depth_of(other) * 22, other.y
                _, oh = self.measure(other)
                # bottom center of other vs top of dragged
                d = ((b.x - (ox + 60)) ** 2 + (b.y - (oy + oh)) ** 2) ** 0.5
                if d < best_d:
                    best_d = d
                    best = other
            if best:
                # attach under best's chain end
                end = best
                while end.next_id and end.next_id in self.blocks:
                    end = self.blocks[end.next_id]
                end.next_id = b.id
                b.prev_id = end.id
                b.x = end.x
                b.y = end.y + self.measure(end)[1] + 2
                return

    def _on_right(self, e):
        item = self.find_withtag("current")
        if not item:
            return
        tags = self.gettags(item[0])
        if tags and tags[0] == "blk":
            b = self.blocks.get(tags[1])
            if b:
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label="Edit Tag…", command=lambda: self.app.edit_tag_dialog(b))
                menu.add_command(label="Duplicate", command=lambda: self._duplicate(b))
                menu.add_separator()
                menu.add_command(label="Delete Block", command=lambda: self.delete_block(b))
                menu.tk_popup(e.x_root, e.y_root)

    def _duplicate(self, b):
        nb = Block(b.btype, b.x + 20, b.y + 20)
        nb.fields = dict(b.fields)
        nb.slots = dict(b.slots)
        self.add_block(nb)
        self.render_all()

    def delete_block(self, b):
        if b.prev_id:
            p = self.blocks.get(b.prev_id)
            if p:
                p.next_id = None
        # remove from slots
        for o in self.blocks.values():
            for k, v in list(o.slots.items()):
                if v == b.id:
                    o.slots[k] = None
        self.blocks.pop(b.id, None)
        self.render_all()

    # ---------------- serialization ----------------
    def to_project(self, name="My App"):
        blocks = {bid: blk.to_dict() for bid, blk in self.blocks.items()}
        return {"format": SHSB_MAGIC, "version": SHSB_VERSION, "name": name,
                "blocks": blocks, "created": time.strftime("%Y-%m-%d %H:%M")}

    def load_project(self, proj):
        self.reset()
        for bd in (proj.get("blocks") or {}).values():
            self.add_block(Block.from_dict(bd))
        # fix prev links
        for blk in self.blocks.values():
            nxt = blk.next_id
            if nxt and nxt in self.blocks:
                self.blocks[nxt].prev_id = blk.id
        self.render_all()


# ------------------------------------------------------------------
# 5. GUI — palette
# ------------------------------------------------------------------
class Palette(tk.Canvas):
    def __init__(self, master, app, **kw):
        super().__init__(master, bg="#F9F9F9", highlightthickness=0, width=250, **kw)
        self.app = app
        self.font = None
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<MouseWheel>", lambda e: self.yview_scroll(int(-e.delta / 120), "units"))
        self._drag_type = None
        self._ghost = None
        self._moved = False

    def show_category(self, cat):
        self.delete("all")
        self.configure(scrollregion=(0, 0, 0, 0))
        y = 6
        for btype, d in BLOCK_DEFS.items():
            if d.get("cat") != cat:
                continue
            color = CAT_COLORS.get(cat, "#FFAB19")
            label = d.get("label", btype)
            w = 226
            self.create_rectangle(4, y, 4 + w, y + 30, fill=color, outline="#3a3a3a",
                                  width=1, tags=("pal", btype))
            cx = 14
            for part in re.split(r"(\{[^}]*\})", label):
                if not part:
                    continue
                if part.startswith("{") and part.endswith("}"):
                    key = part[1:-1]
                    spec = next((f for f in d.get("fields", []) if f[1] == key), None)
                    kind = spec[0] if spec else "text"
                    if kind == "diamond":
                        self.create_polygon(cx, y + 15 - 8, cx + 30, y + 15, cx, y + 15 + 8, cx - 30, y + 15,
                                            fill="#FFFFFF", outline="#3a3a3a", width=1, tags=("pal", btype))
                        cx += 36
                    elif kind in ("dropdown", "tag"):
                        self.create_text(cx, y + 15, text="▾", anchor="w", fill="#2a2a2a",
                                         font=self.font, tags=("pal", btype))
                        cx += 18
                    elif kind == "color":
                        self.create_rectangle(cx, y + 9, cx + 20, y + 21, fill="#ffffff",
                                              outline="#3a3a3a", tags=("pal", btype))
                        cx += 26
                    else:
                        self.create_text(cx, y + 15, text="……", anchor="w", fill="#555555",
                                         font=self.font, tags=("pal", btype))
                        cx += 22
                else:
                    self.create_text(cx, y + 15, text=part, anchor="w", fill="#2a2a2a",
                                     font=self.font, tags=("pal", btype))
                    cx += self.font.measure(part) if self.font else (10 * len(part))
            y += 34
        self.configure(scrollregion=(0, 0, 240, y + 10))

    def _press(self, e):
        item = self.find_withtag("current")
        if not item:
            return
        tags = self.gettags(item[0])
        if tags and tags[0] == "pal":
            self._drag_type = tags[1]
            self._moved = False

    def _motion(self, e):
        if not self._drag_type:
            return
        if abs(e.x_root - self._start_root_x) > 4 or abs(e.y_root - self._start_root_y) > 4:
            self._moved = True
        if self._ghost is None and self._moved:
            self._spawn_ghost()
        if self._ghost:
            self._move_ghost(e)

    def _start_root_x(self):
        return 0

    _start_root_x = property(_start_root_x)

    def _spawn_ghost(self):
        app = self.app
        canvas = app.canvas
        # convert pointer to canvas coords
        xr = self.winfo_rootx() - canvas.winfo_rootx() + canvas.canvasx(0)
        yr = self.winfo_rooty() - canvas.winfo_rooty() + canvas.canvasy(0)
        b = Block(self._drag_type)
        canvas.add_block(b, at=(0, 0))
        self._ghost = b
        canvas._drag = b
        canvas._drag_dx = 0
        canvas._drag_dy = 0
        canvas.render_all()
        # now position at pointer
        self._move_ghost(None)

    def _move_ghost(self, e):
        canvas = self.app.canvas
        b = self._ghost
        if e is None:
            # use last event stored
            try:
                e = self._last_e
            except Exception:
                return
        x = e.x_root - canvas.winfo_rootx() + canvas.canvasx(0)
        y = e.y_root - canvas.winfo_rooty() + canvas.canvasy(0)
        b.x = x
        b.y = y
        canvas.render_all()

    def _release(self, e):
        self._last_e = e
        if self._ghost:
            canvas = self.app.canvas
            b = self._ghost
            canvas._drag = b
            canvas._snap(b)
            canvas.render_all()
            self._ghost = None
            canvas._drag = None
            self.app.after_idle(self.app.refresh_code)
        elif self._drag_type and not self._moved:
            # click -> add at default position
            self._click_add()
        self._drag_type = None
        self._moved = False

    def _click_add(self):
        app = self.app
        canvas = app.canvas
        b = Block(self._drag_type)
        x = 60 + (app._new_counter % 10) * 24
        y = 40 + (app._new_counter % 10) * 26
        app._new_counter += 1
        canvas.add_block(b, at=(x, y))
        canvas.render_all()
        app.after_idle(app.refresh_code)


# ------------------------------------------------------------------
# 6. GUI — main application
# ------------------------------------------------------------------
class BlockTectApp:
    def __init__(self, root):
        self.root = root
        self.project_name = "My App"
        self.project_path = None
        self._new_counter = 0
        self.runtime = None      # subprocess for running app
        self.settings = self._load_settings()
        self._apply_packs()

        root.title("%s — Scratch-style block IDE for Python + HTML" % APP_NAME)
        root.geometry("1280x800")
        root.minsize(1000, 640)

        # fonts
        self.base_font = tkfont.nametofont("TkDefaultFont")
        self.block_font = tkfont.Font(family="Segoe UI", size=10)
        self.cat_font = tkfont.Font(family="Segoe UI", size=10)

        self._build_menu()
        self._build_toolbar()
        self._build_layout()

        self.refresh_palette()
        self.new_project()
        self.refresh_code()

    # ---------------- settings / packs ----------------
    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"packs": []}

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f)
        except Exception:
            pass

    def _apply_packs(self):
        for name, pack in PACKS.items():
            if name in self.settings.get("packs", []):
                BLOCK_DEFS.update(pack["blocks"])

    def _build_menu(self):
        m = tk.Menu(self.root)
        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="New Project", accelerator="Ctrl+N", command=self.new_project)
        fm.add_command(label="Open .shsb…", accelerator="Ctrl+O", command=self.open_project)
        fm.add_command(label="Save .shsb", accelerator="Ctrl+S", command=self.save_project)
        fm.add_command(label="Save .shsb As…", command=self.save_project_as)
        fm.add_separator()
        fm.add_command(label="Export .zip (py + html + run scripts)", command=self.export_zip)
        fm.add_command(label="Export run scripts (.bat/.sh)…", command=self.export_run_scripts)
        fm.add_separator()
        fm.add_command(label="Exit", command=self.root.destroy)
        m.add_cascade(label="File", menu=fm)

        rm = tk.Menu(m, tearoff=0)
        rm.add_command(label="Run app (generate + run)", accelerator="F5", command=self.run_app)
        rm.add_command(label="Stop app", command=self.stop_app)
        rm.add_command(label="Preview HTML in browser", command=self.preview_browser)
        m.add_cascade(label="Run", menu=rm)

        vm = tk.Menu(m, tearoff=0)
        vm.add_command(label="Extension Store (more blocks)…", command=self.extension_store)
        m.add_cascade(label="Extensions", menu=vm)

        hm = tk.Menu(m, tearoff=0)
        hm.add_command(label="Guide (.shsb language)", command=self.show_guide)
        hm.add_command(label="About", command=self.show_about)
        m.add_cascade(label="Help", menu=hm)

        self.root.config(menu=m)
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-o>", lambda e: self.open_project())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<F5>", lambda e: self.run_app())

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg="#4C97FF", height=40)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        def btn(text, cmd, bg="#3B7DD8"):
            tk.Button(bar, text=text, command=cmd, bg=bg, fg="white", relief="flat",
                      activebackground="#2F62B0", activeforeground="white",
                      font=("Segoe UI", 9, "bold"), padx=10, cursor="hand2").pack(side="left", padx=3, pady=5)

        btn("➕ New", self.new_project)
        btn("📂 Open", self.open_project)
        btn("💾 Save", self.save_project)
        btn("📦 Export ZIP", self.export_zip)
        btn("▶ Run", self.run_app, "#2EAD57")
        btn("⏹ Stop", self.stop_app, "#D9534F")
        tk.Label(bar, text="   .shsb project: %s" % self.project_name, bg="#4C97FF",
                 fg="white", font=("Segoe UI", 9)).pack(side="left", padx=6)

    def _build_layout(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # left: categories + palette
        left = tk.Frame(main, width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        cats = CORE_CATEGORIES + [c for c in PACKS if c in self.settings.get("packs", [])]
        catbar = tk.Frame(left, bg="#575E75")
        catbar.pack(side="top", fill="x")
        self.cat_buttons = {}
        for cat in cats:
            color = CAT_COLORS.get(cat, "#888888")
            b = tk.Button(catbar, text=cat, anchor="w", relief="flat", bd=0,
                          bg="#575E75", fg="white", activebackground="#4C97FF",
                          activeforeground="white", font=self.cat_font, padx=8, pady=3,
                          command=lambda c=cat: self.select_category(c))
            b.pack(fill="x")
            # color dot
            self.cat_buttons[cat] = b

        # more button [2]
        tk.Button(catbar, text="[2]  More blocks…", anchor="w", relief="flat", bd=0,
                  bg="#4C97FF", fg="white", activebackground="#3B7DD8",
                  activeforeground="white", font=self.cat_font, padx=8, pady=3,
                  command=self.extension_store).pack(fill="x", pady=(6, 0))

        self.palette = Palette(left, self)
        self.palette.font = self.block_font
        self.palette.pack(side="bottom", fill="both", expand=True)

        # center: canvas
        center = tk.Frame(main)
        center.pack(side="left", fill="both", expand=True)
        self.canvas = Canvas(center, self)
        self.canvas.font = self.block_font
        vsb = ttk.Scrollbar(center, orient="vertical", command=self.canvas.yview)
        hsb = ttk.Scrollbar(center, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # right: notebook (Preview / Code / Console)
        right = tk.Frame(main, width=430)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)
        self.notebook = nb

        # Preview tab
        prev = tk.Frame(nb)
        nb.add(prev, text="👁 Preview")
        prev_row = tk.Frame(prev)
        prev_row.pack(fill="x")
        tk.Button(prev_row, text="🌐 Open in Browser", command=self.preview_browser).pack(side="left", padx=4, pady=4)
        tk.Button(prev_row, text="🔄 Refresh", command=self.refresh_code).pack(side="left", padx=4, pady=4)
        self.preview_txt = tk.Text(prev, wrap="none", font=("Courier New", 9))
        self.preview_txt.pack(fill="both", expand=True)

        # Code tab
        code = tk.Frame(nb)
        nb.add(code, text="🐍 Python Code")
        self.code_txt = tk.Text(code, wrap="none", font=("Courier New", 9))
        self.code_txt.pack(fill="both", expand=True)

        # Console tab
        con = tk.Frame(nb)
        nb.add(con, text="🖥 Console")
        self.console_txt = tk.Text(con, wrap="none", font=("Courier New", 9), bg="#1e1e1e", fg="#dcdcdc")
        self.console_txt.pack(fill="both", expand=True)
        self.console_txt.insert("end", "Console ready. Press ▶ Run to start your app.\n")

        # status bar
        self.status = tk.Label(self.root, text="Ready", anchor="w", bg="#e8e8e8", relief="sunken")
        self.status.pack(side="bottom", fill="x")

        self._current_cat = None

    # ---------------- category / palette ----------------
    def select_category(self, cat):
        self._current_cat = cat
        for c, b in self.cat_buttons.items():
            b.config(bg="#4C97FF" if c == cat else "#575E75")
        self.palette.show_category(cat)

    def refresh_palette(self):
        if not hasattr(self, "palette"):
            return
        if self._current_cat and self._current_cat in self.cat_buttons:
            self.palette.show_category(self._current_cat)
        else:
            self.select_category("Events")

    # ---------------- project ops ----------------
    def new_project(self):
        self.canvas.reset()
        self.project_name = "My App"
        self.project_path = None
        self.status.config(text="New project")
        self.refresh_code()

    def save_project(self):
        if self.project_path:
            self._write_shsb(self.project_path)
            self.status.config(text="Saved: %s" % self.project_path)
        else:
            self.save_project_as()

    def save_project_as(self):
        p = filedialog.asksaveasfilename(defaultextension=".shsb",
                                         filetypes=[("BlockTect project", "*.shsb"), ("All files", "*.*")])
        if p:
            self.project_path = p
            self._write_shsb(p)
            self.status.config(text="Saved: %s" % p)

    def _write_shsb(self, path):
        proj = self.canvas.to_project(self.project_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(proj, f, indent=2)

    def open_project(self):
        p = filedialog.askopenfilename(filetypes=[("BlockTect project", "*.shsb"), ("All files", "*.*")])
        if p:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    proj = json.load(f)
                self.canvas.load_project(proj)
                self.project_name = proj.get("name", "My App")
                self.project_path = p
                self.status.config(text="Opened: %s" % p)
                self.refresh_code()
            except Exception as ex:
                messagebox.showerror("Error", "Could not open project:\n%s" % ex)

    # ---------------- generation / preview ----------------
    def refresh_code(self):
        try:
            proj = self.canvas.to_project(self.project_name)
            g = Generator(proj)
            app_py = g.generate_app()
            html = g.build_html()
            self.code_txt.delete("1.0", "end")
            self.code_txt.insert("1.0", app_py)
            self.preview_txt.delete("1.0", "end")
            self.preview_txt.insert("1.0", html)
            self.status.config(text="Generated %d block(s) · %d lines Python" %
                               (len(self.canvas.blocks), app_py.count("\n")))
        except Exception as ex:
            self.status.config(text="Generate error: %s" % ex)

    def _tmp_out(self):
        d = os.path.join(tempfile.gettempdir(), "blocktect_run")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
        return d

    def preview_browser(self):
        try:
            proj = self.canvas.to_project(self.project_name)
            g = Generator(proj)
            html = g.build_html()
            d = self._tmp_out()
            p = os.path.join(d, "index.html")
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
            webbrowser.open("file://" + p)
        except Exception as ex:
            messagebox.showerror("Preview", str(ex))

    def run_app(self):
        self.stop_app()
        try:
            proj = self.canvas.to_project(self.project_name)
            g = Generator(proj)
            app_py = g.generate_app()
            d = self._tmp_out()
            with open(os.path.join(d, "app.py"), "w", encoding="utf-8") as f:
                f.write(app_py)
            self.console_txt.delete("1.0", "end")
            self.console_txt.insert("end", "▶ Starting app…\n")
            env = dict(os.environ, PORT="8765")
            self.runtime = subprocess.Popen(
                [sys.executable, os.path.join(d, "app.py")],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                text=True, bufsize=1)
            threading.Thread(target=self._pump_console, daemon=True).start()
            self.status.config(text="App running on port 8765")
        except Exception as ex:
            messagebox.showerror("Run", str(ex))

    def _pump_console(self):
        try:
            for line in iter(self.runtime.stdout.readline, ""):
                if not line:
                    break
                self.root.after(0, lambda s=line: self._append_console(s))
        except Exception:
            pass

    def _append_console(self, s):
        self.console_txt.insert("end", s)
        self.console_txt.see("end")

    def stop_app(self):
        if self.runtime:
            try:
                self.runtime.terminate()
                self.runtime.wait(timeout=3)
            except Exception:
                try:
                    self.runtime.kill()
                except Exception:
                    pass
            self.runtime = None
            self._append_console("\n■ App stopped.\n")

    # ---------------- tag editor (MS-Paint-like popup) ----------------
    def edit_tag_dialog(self, b):
        if b.btype not in ("add_tag", "append_tag", "set_text_tag", "set_style_tag",
                           "set_attr_tag", "tag_prop"):
            messagebox.showinfo("BlockTect", "This block type has no tag editor.\n"
                                            "Tag editor works on HTML tag blocks.")
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Edit Tag — %s" % b.btype)
        dlg.geometry("420x420")
        dlg.transient(self.root)
        f = b.fields
        entries = {}

        def row(label, key, default, width=30):
            tk.Label(dlg, text=label).pack(anchor="w", padx=10)
            var = tk.StringVar(value=str(f.get(key, default)))
            e = tk.Entry(dlg, textvariable=var, width=width)
            e.pack(fill="x", padx=10, pady=2)
            entries[key] = var

        if b.btype == "add_tag":
            row("Tag type (div, button, input…)", "tag", "div")
            row("Parent tag id (default body)", "parent", "body")
            row("Unique id (empty = auto)", "id", "")
        elif b.btype == "append_tag":
            row("Tag id to move", "tag", "")
            row("Parent tag id", "parent", "body")
        elif b.btype in ("set_text_tag", "set_style_tag", "set_attr_tag", "tag_prop"):
            row("Tag id", "tag", "")
            if b.btype == "set_style_tag":
                row("Style property", "prop", "color")
            elif b.btype == "set_attr_tag":
                row("Attribute", "attr", "href")
            elif b.btype == "tag_prop":
                row("Property (.prop)", "prop", "intext")

        def apply():
            for k, var in entries.items():
                b.fields[k] = var.get()
            dlg.destroy()
            self.canvas.render_all()
            self.refresh_code()

        row_btns = tk.Frame(dlg)
        row_btns.pack(pady=10)
        tk.Button(row_btns, text="Apply", command=apply, width=10).pack(side="left", padx=5)
        tk.Button(row_btns, text="Cancel", command=dlg.destroy, width=10).pack(side="left", padx=5)

    # ---------------- extension store ----------------
    def extension_store(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Extension Store — more blocks")
        dlg.geometry("460x420")
        dlg.transient(self.root)
        tk.Label(dlg, text="Enable extension packs to add more block categories:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=8)
        enabled = set(self.settings.get("packs", []))
        vars_ = {}
        for name, pack in PACKS.items():
            var = tk.BooleanVar(value=name in enabled)
            vars_[name] = var
            frm = tk.Frame(dlg)
            frm.pack(fill="x", padx=12, pady=3)
            tk.Checkbutton(frm, text="%s pack" % name, variable=var,
                           font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(frm, text="  %s — %d blocks" % (pack["desc"], len(pack["blocks"])),
                     fg="#555555", font=("Segoe UI", 9)).pack(anchor="w", padx=20)

        def apply():
            packs = [n for n, v in vars_.items() if v.get()]
            self.settings["packs"] = packs
            self._save_settings()
            # (re)apply blocks
            for name in PACKS:
                BLOCK_DEFS.pop(name, None)  # placeholder; real removal below
            self._apply_packs()
            # rebuild category buttons
            for w in list(self.cat_buttons.values()):
                w.destroy()
            self.cat_buttons.clear()
            self._rebuild_catbar()
            dlg.destroy()
            self.refresh_palette()
            messagebox.showinfo("Extensions", "Packs applied: %s" % (", ".join(packs) or "none"))

        tk.Button(dlg, text="Apply", command=apply, width=12).pack(pady=12)

    def _rebuild_catbar(self):
        catbar = self.catbar_frame
        cats = CORE_CATEGORIES + [c for c in PACKS if c in self.settings.get("packs", [])]
        for cat in cats:
            b = tk.Button(catbar, text=cat, anchor="w", relief="flat", bd=0,
                          bg="#575E75", fg="white", activebackground="#4C97FF",
                          activeforeground="white", font=self.cat_font, padx=8, pady=3,
                          command=lambda c=cat: self.select_category(c))
            b.pack(fill="x")
            self.cat_buttons[cat] = b

    # ---------------- export ----------------
    def _generate_files(self):
        proj = self.canvas.to_project(self.project_name)
        g = Generator(proj)
        app_py = g.generate_app()
        html = g.build_html()
        return proj, app_py, html

    def export_zip(self):
        p = filedialog.asksaveasfilename(defaultextension=".zip",
                                         filetypes=[("ZIP archive", "*.zip")])
        if not p:
            return
        proj, app_py, html = self._generate_files()
        name = re.sub(r"\W+", "_", self.project_name.lower()).strip("_") or "app"
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("app.py", app_py)
            z.writestr("index.html", html)
            z.writestr("%s.shsb" % name, json.dumps(proj, indent=2))
            z.writestr("run.bat", _RUN_BAT)
            z.writestr("run.sh", _RUN_SH)
        self.status.config(text="Exported: %s" % p)
        messagebox.showinfo("Export", "Exported project to:\n%s\n\nContains:\n • app.py\n • index.html\n • %s.shsb\n • run.bat\n • run.sh" % (p, name))

    def export_run_scripts(self):
        p = filedialog.asksaveasfilename(defaultextension=".zip",
                                         filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")])
        if not p:
            return
        proj, app_py, html = self._generate_files()
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("app.py", app_py)
            z.writestr("index.html", html)
            z.writestr("run.bat", _RUN_BAT)
            z.writestr("run.sh", _RUN_SH)
        self.status.config(text="Exported runnable app: %s" % p)
        messagebox.showinfo("Export", "Runnable app exported to %s" % p)

    # ---------------- help ----------------
    def show_guide(self):
        here = os.path.dirname(os.path.abspath(__file__))
        guide = os.path.join(here, "GUIDE.md")
        if os.path.exists(guide):
            webbrowser.open("file://" + guide)
        else:
            messagebox.showinfo("Guide", "GUIDE.md not found next to blocktect.py")

    def show_about(self):
        messagebox.showinfo("BlockTect",
            "BlockTect — Scratch-style block IDE for Python + HTML webapps\n\n"
            "• Drag blocks from the left palette into the canvas\n"
            "• Stack blocks vertically to chain them\n"
            "• Drop oval blocks onto diamond slots for values\n"
            "• ▶ Run generates app.py + index.html and starts a server\n"
            "• Export .shsb / .zip with run scripts\n\n"
            "Your own language: .shsb (Scratch-Hybrid Script Blocks)")


_RUN_BAT = "@echo off\r\nrem BlockTect generated app\r\npython app.py\r\npause\r\n"
_RUN_SH = "#!/bin/sh\n# BlockTect generated app\npython3 app.py\n"


# ------------------------------------------------------------------
# 7. CLI (headless) support
# ------------------------------------------------------------------
def cli_export(args):
    if len(args) < 2:
        print("usage: python blocktect.py export <project.shsb> [outdir]")
        return 2
    src, out = args[0], args[1] if len(args) > 1 else "out"
    with open(src, "r", encoding="utf-8") as f:
        proj = json.load(f)
    html_path, py_path = generate_project(proj, out)
    print("Exported:")
    print("  HTML : %s" % html_path)
    print("  PY   : %s" % py_path)
    print("Run with: python %s" % py_path)
    return 0


def cli_run(args):
    if not args:
        print("usage: python blocktect.py run <project.shsb>")
        return 2
    src = args[0]
    with open(src, "r", encoding="utf-8") as f:
        proj = json.load(f)
    d = tempfile.mkdtemp(prefix="blocktect_cli_")
    generate_project(proj, d)
    py = os.path.join(d, "app.py")
    print("Running %s … (Ctrl+C to stop)" % src)
    try:
        subprocess.call([sys.executable, py])
    except KeyboardInterrupt:
        pass
    return 0


def cli_info():
    print("%s v%s" % (APP_NAME, SHSB_VERSION))
    print("\nCategories & block count:")
    cats = {}
    for btype, d in BLOCK_DEFS.items():
        cats.setdefault(d.get("cat", "?"), []).append(btype)
    for cat, bs in cats.items():
        print("  %-12s %2d blocks" % (cat, len(bs)))
    print("\nExtension packs:")
    for name, pack in PACKS.items():
        print("  %-6s %2d blocks  %s" % (name, len(pack["blocks"]), pack["desc"]))
    print("\nTop HTML tags: %d" % len(TOP_TAGS))
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        cmd = argv[0].lower()
        if cmd == "export":
            return cli_export(argv[1:])
        if cmd == "run":
            return cli_run(argv[1:])
        if cmd == "info":
            return cli_info()
        print("Unknown command: %s" % cmd)
        return 2

    if not HAS_TK:
        print("No display available. Use CLI:  python blocktect.py info | export | run")
        return 1
    root = tk.Tk()
    app = BlockTectApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
