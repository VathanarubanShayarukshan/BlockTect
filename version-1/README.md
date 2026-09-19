# 🧊 BlockTect

**Visual Block Programming Tool for Python & HTML - தமிழில்!**

BlockTect is a Scratch-inspired visual block programming environment that lets you build Python applications and HTML web pages using drag-and-drop blocks. All blocks are in Tamil!

![BlockTect](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧊 **Block Editor** | Scratch-style drag & drop block programming |
| 🎨 **11 Block Categories** | Motion, Looks, Control, Events, Sensing, Operators, Variables, HTML Tags, Commands, API, HTML Attributes |
| 🌐 **HTML Tag Builder** | 25+ HTML tags with unique IDs - div, h1, button, canvas, video, audio, and more |
| 🏷️ **Tag Editor** | MS Paint-style visual tag editor |
| 🐍 **Python Code Generation** | Auto-generates Python from blocks |
| 🔌 **API Integration** | HTTP GET/POST, custom APIs, webhooks |
| ⚙️ **System Commands** | Run OS commands, file read/write/delete |
| 📦 **Export as .zip** | Download Python + HTML + .shsb files |
| 📄 **.shsb Format** | Custom BlockTect script format |
| 🔧 **Extensions System** | Load and create custom extensions |
| 👁️ **Live Preview** | Real-time HTML preview |
| 💾 **Project Save/Load** | Save and load your projects |
| 🇮🇳 **Tamil UI** | Full Tamil language interface |

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install requests

# Run BlockTect
python blocktect.py

# Open in browser
# http://127.0.0.1:8080
```

---

## 📖 .shsb Language Specification (RAG Documentation)

### Overview

`.shsb` (BlockTect Script) is a custom scripting language format for BlockTect projects. It stores block programs in a human-readable text format that can be version-controlled, shared, and re-imported.

### File Extension: `.shsb`

### Syntax Rules

```
// This is a comment (starts with //)

BLOCK block_type arg1 arg2 ...      # A single statement block
CONTAINER block_type arg1 arg2 ...  # A container block (has children)
END                                 # Ends a container block
```

### Data Types

| Type | Syntax | Example |
|------|--------|---------|
| String | `"text"` | `"வணக்கம்"` |
| Number | plain number | `42`, `3.14` |
| Variable | `$var_name` | `$my_var` |
| List | `@list_name` | `@my_list` |
| Tag Ref | `#tag_id` | `#myButton` |
| Boolean | `true` / `false` | `true` |

### Events (Hat Blocks)

Events trigger scripts when something happens:

| Event | Syntax | Description |
|-------|--------|-------------|
| Green Flag | `CONTAINER when_green_flag` | When play button clicked |
| Key Pressed | `CONTAINER when_key_pressed space` | When key pressed |
| Clicked | `CONTAINER when_clicked` | When sprite clicked |
| **Page Load** ⭐ | `CONTAINER when_page_load` | When page loads (custom) |
| **Tag Clicked** ⭐ | `CONTAINER when_tag_clicked #myId` | When HTML tag clicked (custom) |
| Broadcast | `CONTAINER when_broadcast "message1"` | When broadcast received |
| Webhook | `CONTAINER webhook event_name` | When webhook called |

### Block Categories

#### 1. இயக்கம் (Motion) - `#4C97FF`
```
BLOCK move_steps 10
BLOCK turn_right 15
BLOCK turn_left 15
BLOCK goto_xy 100 200
BLOCK set_position 50
BLOCK set_y 100
```

#### 2. தோற்றம் (Looks) - `#9966FF`
```
BLOCK say "வணக்கம்!" 2
BLOCK say_forever "வணக்கம்!"
BLOCK show
BLOCK hide
BLOCK set_effect color 50
BLOCK change_effect brightness 25
BLOCK set_size 150
BLOCK change_size 10
```

#### 3. கட்டுப்பாடு (Control) - `#FFAB19`
```
BLOCK wait 1
CONTAINER repeat 10
    BLOCK say "உள்ளே" 1
END
CONTAINER forever
    BLOCK move_steps 10
END
CONTAINER if_then
    BLOCK say "உண்மை" 1
END
BLOCK wait_until true
BLOCK stop_all
```

#### 4. நிகழ்வுகள் (Events) - `#FFBF00`
```
CONTAINER when_green_flag
    BLOCK say "ஆரம்பி" 2
END
CONTAINER when_key_pressed space
    BLOCK say "Space அழுத்தப்பட்டது" 1
END
CONTAINER when_page_load
    BLOCK say "பக்கம் ஏற்றப்பட்டது" 2
END
CONTAINER when_tag_clicked #btn1
    BLOCK say "பொத்தான் கிளிக்" 1
END
BLOCK broadcast "செய்தி1"
```

#### 5. உணர்தல் (Sensing) - `#4CBFE6`
```
BLOCK ask "உன் பெயர் என்ன?"
BLOCK mouse_x       // returns number
BLOCK mouse_y       // returns number
BLOCK key_pressed space  // returns boolean
BLOCK timer          // returns number
BLOCK reset_timer
```

#### 6. செயலிகள் (Operators) - `#59C059` ◆

Diamond-shaped operator blocks:

```
BLOCK op_add 5 3           // 5 + 3 = 8
BLOCK op_subtract 10 4     // 10 - 4 = 6
BLOCK op_multiply 6 7      // 6 × 7 = 42
BLOCK op_divide 15 3       // 15 ÷ 3 = 5
BLOCK op_random 1 10       // random(1, 10)
BLOCK op_gt 5 3            // 5 > 3 → true
BLOCK op_lt 2 8            // 2 < 8 → true
BLOCK op_eq "hello" "hello" // "hello" = "hello" → true
BLOCK op_and true false     // true and false → false
BLOCK op_or true false      // true or false → true
BLOCK op_not true           // not true → false
BLOCK op_join "Hello " "World"  // "Hello World"
BLOCK op_mod 10 3           // 10 % 3 = 1
BLOCK op_round 3.7          // 4
```

#### 7. மாறிகள் (Variables) - `#FF8C1A`
```
BLOCK create_variable "my_var"
BLOCK var_set $my_var 10
BLOCK var_change $my_var 1
BLOCK var_get $my_var         // returns value
BLOCK list_create "my_list"
BLOCK list_add @my_list "item"
BLOCK list_get @my_list 1     // returns item at index
BLOCK list_length @my_list    // returns length
```

#### 8. HTML டேக்ஸ் (HTML Tags) - `#E74C3C` 🌐

Create HTML elements with unique IDs:

```
BLOCK html_div "myDiv"
BLOCK html_h1 "heading1"
BLOCK html_h2 "heading2"
BLOCK html_p "para1"
CONTAINER html_button "btn1"
    BLOCK say "கிளிக் செய்" 1
END
BLOCK html_input "input1" text
BLOCK html_img "img1" "https://via.placeholder.com/150"
CONTAINER html_a "link1" "https://example.com"
    BLOCK say "லிங்க்" 1
END
CONTAINER html_span "span1"
CONTAINER html_ul "list1"
CONTAINER html_li "item1"
CONTAINER html_table "table1"
CONTAINER html_form "form1"
CONTAINER html_video "video1" "video.mp4"
CONTAINER html_audio "audio1" "audio.mp3"
BLOCK html_canvas "canvas1" 400 300
CONTAINER html_select "select1"
CONTAINER html_option "1"
CONTAINER html_label "input1"
CONTAINER html_textarea "textarea1"
CONTAINER html_style "style1"
CONTAINER html_script "script1"
CONTAINER html_nav "nav1"
CONTAINER html_header "header1"
CONTAINER html_footer "footer1"
CONTAINER html_section "section1"
CONTAINER html_article "article1"
CONTAINER html_main "main1"
```

#### 9. கட்டளைகள் (Commands) - `#2C3E50` ⚙️

System-level operations:

```
BLOCK run_command "echo Hello World"
CONTAINER run_python
    BLOCK say "Python குறியீடு" 1
END
CONTAINER run_js
    BLOCK say "JavaScript" 1
END
BLOCK read_file "data.txt"      // returns content
BLOCK write_file "output.txt" "உள்ளடக்கம்"
BLOCK delete_file "temp.txt"
BLOCK create_dir "new_folder"
```

#### 10. API & நீட்டிப்புகள் (API & Extensions) - `#00B894` 🔌

```
BLOCK http_get "https://api.example.com/data"
BLOCK http_post "https://api.example.com/data" "{\"key\":\"value\"}"
BLOCK custom_api GET "https://api.example.com" "{\"Content-Type\":\"application/json\"}"
BLOCK load_extension "my_extension"
BLOCK create_extension "my_extension"
CONTAINER webhook "event_name"
```

#### 11. HTML அடையாளங்கள் (HTML Attributes) - `#6C5CE7` 🏷️

Manipulate HTML elements dynamically:

```
BLOCK set_attr #myDiv "class" "new-class"
BLOCK get_attr #myDiv "class"     // returns attribute value
BLOCK set_text #myDiv "புதிய உரை"
BLOCK set_html #myDiv "<b>bold</b>"
BLOCK set_css #myDiv "color" "red"
BLOCK hide_tag #myDiv
BLOCK show_tag #myDiv
BLOCK tag_var #myDiv $element    // Tag → Variable mapping
```

### Complete .shsb Example

```shsb
// BlockTect .shsb File
// Version: 1.0.0
// My First BlockTect Project

CONTAINER when_page_load
    BLOCK set_text #heading1 "வணக்கம் உலகம்!"
    BLOCK set_css #heading1 "color" "blue"
    CONTAINER html_button "btn1"
        BLOCK set_text #btn1 "கிளிக் செய்"
    END
END

CONTAINER when_tag_clicked #btn1
    BLOCK var_set $counter 0
    CONTAINER repeat 5
        BLOCK var_change $counter 1
        BLOCK set_text #heading1 $counter
    END
END

CONTAINER when_green_flag
    BLOCK http_get "https://api.example.com/data"
    BLOCK say "API அழைக்கப்பட்டது" 2
END
```

---

## 🔧 Block Types

| Shape | Visual | Description |
|-------|--------|-------------|
| `hat` | 🎩 Top-rounded | Event triggers (starts script) |
| `statement` | ▭ Notched | Regular command block |
| `container` | 📦 C-shaped | Holds child blocks |
| `container_conditional` | 🔀 If-shaped | Conditional container |
| `reporter` | ◯ Rounded | Returns a value |
| `boolean` | ◇ Diamond | Returns true/false |
| `reporter_diamond` | ◆ Diamond | Value-returning diamond |
| `boolean_diamond` | ◇ Diamond | Boolean diamond |

---

## 📁 Project Structure

```
BlockTect/
├── blocktect.py              # Main application (single file!)
├── README.md                 # This documentation
├── blocktect_data/
│   ├── projects/             # Saved projects (.blocktect)
│   └── extensions/           # Custom extensions (.json)
├── developer_data/
│   ├── Magiccode 3.0.html    # Reference implementation
│   └── prompt.txt            # Original prompt
└── examples/
    └── example.shsb          # Example .shsb file
```

---

## 🎯 Use Cases

- 🧑‍🏫 **Teaching programming** to Tamil-speaking students
- 🌐 **Quick HTML prototyping** with visual blocks
- 🐍 **Python learning** with Scratch-like simplicity
- 🔌 **API testing** with visual blocks
- 📱 **Web app prototyping** without coding
- 🎮 **Simple games** with motion and looks blocks

---

## 🛠️ Development

### Requirements
- Python 3.8+
- No external dependencies required (uses built-in modules)
- Optional: `requests` library for API blocks

### Run Tests
```bash
python -c "import blocktect; print('✅ BlockTect loaded successfully')"
```

### Test .shsb Parser
```python
from blocktect import SHSBParser

shsb_text = """CONTAINER when_green_flag
    BLOCK say "வணக்கம்" 2
END"""

blocks = SHSBParser.shsb_to_blocks(shsb_text)
print(blocks)  # Parsed blocks JSON
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

- Inspired by [Scratch 3.0](https://scratch.mit.edu/) from MIT
- Reference: [Magiccode 3.0](https://magicbit.cc/magiccodelive/) for microcontroller coding
- Built with ❤️ for Tamil-speaking developers

---

## 🐛 Known Issues

- Internet connection required for `requests` library API blocks
- Some complex Python features may not be representable in blocks yet
- Preview requires blocks with `html_` prefix

---

## 📞 Support

For issues and feature requests, please open an issue on GitHub.

---

**தமிழில் கற்றுக்கொள்ளுங்கள், தமிழில் உருவாக்குங்கள்! 🧊**
