from dataclasses import dataclass


def classify_element(class_name: str) -> str:
    """Map Android class names to short element type strings."""
    if not class_name:
        return ""
    # Use the simple class name (after last dot)
    simple = class_name.rsplit(".", 1)[-1]
    mapping = {
        "Button": "button",
        "ImageButton": "button",
        "FloatingActionButton": "button",
        "MaterialButton": "button",
        "AppCompatButton": "button",
        "EditText": "input",
        "AutoCompleteTextView": "input",
        "TextInputEditText": "input",
        "AppCompatEditText": "input",
        "CheckBox": "checkbox",
        "AppCompatCheckBox": "checkbox",
        "Switch": "switch",
        "SwitchCompat": "switch",
        "ToggleButton": "switch",
        "RadioButton": "radio",
        "Spinner": "dropdown",
        "SeekBar": "slider",
        "RatingBar": "slider",
        "TextView": "text",
        "AppCompatTextView": "text",
        "ImageView": "image",
        "AppCompatImageView": "image",
        "RecyclerView": "list",
        "ListView": "list",
        "ScrollView": "scroll",
        "TabLayout": "tabs",
        "TabView": "tab",
        "ViewPager": "pager",
        "WebView": "webview",
        "ProgressBar": "progress",
        "Toolbar": "toolbar",
        "SearchView": "search",
    }
    return mapping.get(simple, "")


@dataclass
class ElementNode:
    name: str
    coordinates: 'CenterCord'
    bounding_box: 'BoundingBox'
    element_type: str = ""
    element_class: str = ""

@dataclass
class BoundingBox:
    x1:int
    y1:int
    x2:int
    y2:int

    def to_string(self):
        return f'[{self.x1},{self.y1}][{self.x2},{self.y2}]'

@dataclass
class TreeState:
    interactive_elements:list[ElementNode]

    def to_string(self):
        lines = []
        for index, node in enumerate(self.interactive_elements):
            type_part = f' Type: {node.element_type}' if node.element_type else ''
            lines.append(f'Label: {index}{type_part} Name: {node.name} Coordinates: {node.coordinates.to_string()}')
        return '\n'.join(lines)
    
@dataclass
class CenterCord:
    x: int
    y: int

    def to_string(self):
        return f'({self.x},{self.y})'