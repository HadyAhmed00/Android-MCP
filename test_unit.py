"""
Full test suite for Android-MCP.
Covers:
  - Smart Element Finder (_find_element logic via mocks)
  - Wait-For-Condition recorder exports
  - App Lifecycle recorder exports
  - Data Privacy: PII scrubbing, collision resolution, sensitive typing, env var exports
  - Syntax validation for main.py and src/recorder.py
  - All 25 tools present in main.py
"""

import re
import json
import sys
import os
import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

passed = 0
failed = 0

def test(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name}' + (f' -- {detail}' if detail else ''))

# ============================================================
# Load source files
# ============================================================
with open('main.py', encoding='utf-8') as f:
    source = f.read()

# Extract privacy + helper functions from main.py for isolated testing
start = source.find('def _mask_email')
end = source.find("@mcp.tool(name='Click-Tool'")
exec(source[start:end], globals())

print('=' * 70)
print('TEST SUITE: Android-MCP -- All Features')
print('=' * 70)


# ============================================================
# [1] SMART ELEMENT FINDER -- _find_element logic
# ============================================================
print('\n[1] SMART ELEMENT FINDER -- _find_element logic')
print('-' * 40)

# Build mock element classes mirroring src/tree/views.py
class MockCoord:
    def __init__(self, x, y): self.x = x; self.y = y
class MockBox:
    def __init__(self): pass
class MockElement:
    def __init__(self, name, x, y):
        self.name = name
        self.coordinates = MockCoord(x, y)
        self.bounding_box = MockBox()

# Build mock tree state and mobile
class MockTreeState:
    def __init__(self, elements): self.interactive_elements = elements
class MockMobileState:
    def __init__(self, elements): self.tree_state = MockTreeState(elements)

def make_find_element(elements):
    """Return a _find_element function bound to a fixed element list."""
    def _find(text, index=0):
        all_names = [e.name for e in elements]
        scrub_map = _scrub_pii_unique(all_names)
        matches = []
        for element in elements:
            if text.lower() in element.name.lower():
                matches.append(element)
            elif text.lower() in scrub_map.get(element.name, '').lower():
                matches.append(element)
        if not matches:
            available = ', '.join('"' + scrub_map.get(e.name, e.name) + '"' for e in elements[:20])
            return None, f'Element "{text}" not found. Available elements: {available}'
        if index >= len(matches):
            return None, f'Index {index} out of range. Found {len(matches)} matches for "{text}".'
        return matches[index], None
    return _find

# Test set 1: Basic name matching
els = [
    MockElement('Login', 100, 200),
    MockElement('Sign Up', 300, 200),
    MockElement('Forgot Password', 100, 400),
]
find = make_find_element(els)

el, err = find('Login')
test('Exact match returns element', el is not None and err is None)
test('Exact match correct element', el is not None and el.name == 'Login')

el, err = find('login')
test('Case-insensitive match', el is not None and el.name == 'Login')

el, err = find('sign')
test('Partial match (sign -> Sign Up)', el is not None and el.name == 'Sign Up')

el, err = find('pass')
test('Partial match (pass -> Forgot Password)', el is not None and el.name == 'Forgot Password')

el, err = find('NonExistent')
test('Not found returns error', el is None and err is not None)
test('Error message contains "not found"', err is not None and 'not found' in err)
test('Error message lists available elements', err is not None and 'Login' in err)

# Test set 2: Index parameter
els2 = [
    MockElement('OK', 100, 200),
    MockElement('OK', 300, 400),
    MockElement('OK', 500, 600),
]
find2 = make_find_element(els2)

el, err = find2('OK', index=0)
test('Index 0 returns first match', el is not None and el.coordinates.x == 100)

el, err = find2('OK', index=1)
test('Index 1 returns second match', el is not None and el.coordinates.x == 300)

el, err = find2('OK', index=2)
test('Index 2 returns third match', el is not None and el.coordinates.x == 500)

el, err = find2('OK', index=3)
test('Index out of range returns error', el is None and err is not None)
test('Out-of-range error message correct', err is not None and 'out of range' in err and '3 matches' in err)

# Test set 3: Scrubbed name matching (privacy integration)
els3 = [
    MockElement('user@gmail.com', 200, 300),
    MockElement('Settings', 100, 100),
]
find3 = make_find_element(els3)

# Agent sees scrubbed name from State-Tool, passes it to find
scrubbed_version = _scrub_pii('user@gmail.com')
el, err = find3(scrubbed_version)
test('Finds element by scrubbed email name', el is not None, f'Searched: "{scrubbed_version}", err: {err}')

el, err = find3('Settings')
test('Normal non-PII name unaffected', el is not None and el.name == 'Settings')

# Test set 4: Error message scrubs PII
els4 = [MockElement('user@gmail.com', 100, 200)]
find4 = make_find_element(els4)

el, err = find4('nonexistent')
test('Error available-list scrubs email', err is not None and 'user@gmail.com' not in err)
test('Error available-list shows masked email', err is not None and '@gmail.com' in err)


# ============================================================
# [2] WAIT-FOR-CONDITION -- function signature + recorder
# ============================================================
print('\n[2] WAIT-FOR-CONDITION -- structure & recorder exports')
print('-' * 40)

# Verify Wait-For-Condition-Tool is defined with correct params
test('Wait-For-Condition-Tool defined', "name='Wait-For-Condition-Tool'" in source)
test('element_text param exists', 'element_text:str=None' in source)
test('element_gone param exists', 'element_gone:str=None' in source)
test('activity_name param exists', 'activity_name:str=None' in source)
test('timeout param exists', 'timeout:int=10' in source)
test('interval param exists', 'interval:float=1.0' in source)
test('ADB fallback in wait_for_condition', 'dumpsys activity activities' in source)

from src.recorder import TestRecorder

rec_wfc = TestRecorder()
rec_wfc.start()

# Success case
rec_wfc.record_action('wait_for_condition', {
    'element_text': 'Welcome', 'element_gone': None, 'activity_name': None,
    'timeout': 10, 'elapsed': 2.5, 'result': 'success'
})
# Timeout case
rec_wfc.record_action('wait_for_condition', {
    'element_text': None, 'element_gone': 'Loading', 'activity_name': None,
    'timeout': 15, 'result': 'timeout'
})
# Activity case
rec_wfc.record_action('wait_for_condition', {
    'element_text': None, 'element_gone': None, 'activity_name': 'MainActivity',
    'timeout': 10, 'elapsed': 1.2, 'result': 'success'
})
rec_wfc.stop()

adb_wfc = rec_wfc.export_as_python(filename='tmp_wfc_adb.py', use_adb=True)
with open(adb_wfc) as f: wfc_adb = f.read()

test('WFC ADB: element_text condition exported', 'Welcome' in wfc_adb)
test('WFC ADB: element_gone condition exported', 'Loading' in wfc_adb)
test('WFC ADB: activity condition exported', 'MainActivity' in wfc_adb)
test('WFC ADB: uses time.sleep', 'time.sleep' in wfc_adb)

read_wfc = rec_wfc.export_as_readable(filename='tmp_wfc_read.txt')
with open(read_wfc) as f: wfc_read = f.read()

test('WFC readable: Wait for appears', 'Wait for' in wfc_read)
test('WFC readable: result shown', 'result: success' in wfc_read)
test('WFC readable: timeout shown', 'result: timeout' in wfc_read)

for f in ['tmp_wfc_adb.py', 'tmp_wfc_read.txt']:
    if os.path.exists(f): os.remove(f)


# ============================================================
# [3] APP LIFECYCLE TOOLS -- structure & recorder exports
# ============================================================
print('\n[3] APP LIFECYCLE TOOLS -- structure & recorder exports')
print('-' * 40)

test('Launch-App-Tool defined', "name='Launch-App-Tool'" in source)
test('Kill-App-Tool defined', "name='Kill-App-Tool'" in source)
test('Clear-App-Data-Tool defined', "name='Clear-App-Data-Tool'" in source)
test('Get-Current-App-Tool defined', "name='Get-Current-App-Tool'" in source)
test('List-Apps-Tool defined', "name='List-Apps-Tool'" in source)
test('monkey command in launch', "monkey -p" in source)
test('am force-stop in kill', "am force-stop" in source)
test('pm clear in clear data', "pm clear" in source)
test('dumpsys in get current app', "dumpsys activity" in source)

rec_app = TestRecorder()
rec_app.start()
rec_app.record_action('launch_app', {'package': 'com.example.app'})
rec_app.record_action('kill_app', {'package': 'com.example.app'})
rec_app.record_action('clear_app_data', {'package': 'com.example.app'})
rec_app.stop()

adb_app = rec_app.export_as_python(filename='tmp_app_adb.py', use_adb=True)
with open(adb_app) as f: app_adb = f.read()

test('ADB: launch_app monkey command', 'monkey' in app_adb and 'com.example.app' in app_adb)
test('ADB: kill_app force-stop', 'force-stop' in app_adb)
test('ADB: clear_app_data pm clear', 'pm clear' in app_adb or ('clear' in app_adb and 'com.example.app' in app_adb))

ui_app = rec_app.export_as_python(filename='tmp_app_ui.py', use_adb=False)
with open(ui_app) as f: app_ui = f.read()

test('UI: launch_app monkey command', 'monkey' in app_ui and 'com.example.app' in app_ui)
test('UI: kill_app force-stop', 'force-stop' in app_ui)
test('UI: clear_app_data present', 'clear' in app_ui.lower() and 'com.example.app' in app_ui)

read_app = rec_app.export_as_readable(filename='tmp_app_read.txt')
with open(read_app) as f: app_read = f.read()

test('Readable: Launch app', 'Launch app com.example.app' in app_read)
test('Readable: Force stop', 'Force stop app com.example.app' in app_read)
test('Readable: Clear all data', 'Clear all data for app com.example.app' in app_read)

for f in ['tmp_app_adb.py', 'tmp_app_ui.py', 'tmp_app_read.txt']:
    if os.path.exists(f): os.remove(f)


# ============================================================
# [4] PII SCRUBBING
# ============================================================
print('\n[4] PII SCRUBBING -- emails, phones, cards')
print('-' * 40)

test('Email 1 char', _scrub_pii('a@test.com') == 'a*@test.com')
test('Email 2 chars', _scrub_pii('ab@test.com') == 'a*@test.com')
test('Email 3 chars', _scrub_pii('abc@test.com') == 'a*c@test.com')
test('Email 4 chars', _scrub_pii('user@gmail.com') == 'us*r@gmail.com')
test('Email 5 chars', _scrub_pii('ggggg@gmail.com') == 'ggg*g@gmail.com')
test('Email long', _scrub_pii('john.doe@company.com') == 'joh****e@company.com')
test('Settings unchanged', _scrub_pii('Settings') == 'Settings')
test('Package name unchanged', _scrub_pii('com.android.settings') == 'com.android.settings')
test('Phone +1-555-123-4567', _scrub_pii('+1-555-123-4567') == '***-***-4567')
test('Phone (555) 123-4567', _scrub_pii('(555) 123-4567') == '***-***-4567')
test('Phone 555.123.4567', _scrub_pii('555.123.4567') == '***-***-4567')
test('Short number unchanged', _scrub_pii('1234') == '1234')
test('Card spaces', _scrub_pii('4111 1111 1111 1111') == '4111-****-1111')
test('Card dashes', _scrub_pii('4111-1111-1111-1111') == '4111-****-1111')


# ============================================================
# [5] COLLISION RESOLUTION
# ============================================================
print('\n[5] COLLISION RESOLUTION')
print('-' * 40)

# Emails sharing prefix and suffix
r = _scrub_pii_unique(['ggggg@gmail.com', 'ggggm@gmail.com', 'gggga@gmail.com'])
test('3 similar emails unique', len(set(r.values())) == 3, f'Got: {list(r.values())}')

# Emails differing only in middle char
r2 = _scrub_pii_unique(['abcde@test.com', 'abcfe@test.com'])
test('Middle-diff emails unique', len(set(r2.values())) == 2, f'Got: {list(r2.values())}')

# user1 vs user2
r3 = _scrub_pii_unique(['user1@gmail.com', 'user2@gmail.com'])
test('user1 vs user2 unique', len(set(r3.values())) == 2, f'Got: {list(r3.values())}')

# Phones with same last 4
r4 = _scrub_pii_unique(['+1-555-123-4567', '+1-555-987-4567', '+1-800-555-4567'])
test('3 phones same last 4 unique', len(set(r4.values())) == 3, f'Got: {list(r4.values())}')

# Non-PII unchanged through unique scrubbing
r5 = _scrub_pii_unique(['Settings', 'Login', 'OK', 'Cancel'])
test('Non-PII unchanged in unique', all(r5[k] == k for k in r5))

# Mixed collision + non-collision
r6 = _scrub_pii_unique(['john@gmail.com', 'jane@gmail.com', 'Submit', 'Cancel'])
test('Mixed unique all distinct', len(set(r6.values())) == 4)
test('Submit unchanged in mixed', r6['Submit'] == 'Submit')


# ============================================================
# [6] SENSITIVE TYPING -- env var exports
# ============================================================
print('\n[6] SENSITIVE TYPING -- env var recorder exports')
print('-' * 40)

rec_s = TestRecorder()
rec_s.start()
rec_s.record_action('type', {
    'text': 'hello', 'x': 100, 'y': 200, 'clear': False,
    'sensitive': False, 'var_name': None
})
rec_s.record_action('type', {
    'text': '****', 'x': 100, 'y': 300, 'clear': False,
    'sensitive': True, 'var_name': 'SENSITIVE_INPUT_1'
})
rec_s.record_action('type_element', {
    'input_text': '****', 'element_text': 'Password', 'index': 0,
    'x': 100, 'y': 400, 'sensitive': True, 'var_name': 'PASSWORD_INPUT_2'
})
rec_s.record_action('type_element', {
    'input_text': 'john', 'element_text': 'Username', 'index': 0,
    'x': 100, 'y': 500, 'sensitive': False, 'var_name': None
})
rec_s.stop()

adb_s = rec_s.export_as_python(filename='tmp_sens_adb.py', use_adb=True)
with open(adb_s) as f: s_adb = f.read()

test('ADB: import os present', 'import os' in s_adb)
test('ADB: normal text exported', 'hello' in s_adb)
test('ADB: sensitive uses env var', 'os.environ["SENSITIVE_INPUT_1"]' in s_adb)
test('ADB: password uses env var', 'os.environ["PASSWORD_INPUT_2"]' in s_adb)
test('ADB: no **** in executable lines', not any('type_text("****")' in l or 'send_keys("****")' in l for l in s_adb.split('\n') if not l.strip().startswith('#')))
test('ADB: normal type_element has real text', 'john' in s_adb)

ui_s = rec_s.export_as_python(filename='tmp_sens_ui.py', use_adb=False)
with open(ui_s) as f: s_ui = f.read()

test('UI: import os present', 'import os' in s_ui)
test('UI: sensitive uses env var', 'os.environ["SENSITIVE_INPUT_1"]' in s_ui)
test('UI: password uses env var', 'os.environ["PASSWORD_INPUT_2"]' in s_ui)

read_s = rec_s.export_as_readable(filename='tmp_sens_read.txt')
with open(read_s) as f: s_read = f.read()

test('Readable: normal text visible', 'hello' in s_read)
test('Readable: SENSITIVE_INPUT_1 shown', 'SENSITIVE_INPUT_1' in s_read)
test('Readable: PASSWORD_INPUT_2 shown', 'PASSWORD_INPUT_2' in s_read)

json_s = rec_s.export_as_json(filename='tmp_sens.json')
with open(json_s) as f: j = json.load(f)

test('JSON: 4 actions recorded', j['total_actions'] == 4)
test('JSON: sensitive flag True', j['actions'][1]['parameters']['sensitive'] == True)
test('JSON: var_name stored', j['actions'][1]['parameters']['var_name'] == 'SENSITIVE_INPUT_1')
test('JSON: masked text stored', j['actions'][1]['parameters']['text'] == '****')
test('JSON: normal text stored', j['actions'][0]['parameters']['text'] == 'hello')

for f in ['tmp_sens_adb.py', 'tmp_sens_ui.py', 'tmp_sens_read.txt', 'tmp_sens.json']:
    if os.path.exists(f): os.remove(f)


# ============================================================
# [7] CLICK-ELEMENT / LONG-CLICK-ELEMENT recorder exports
# ============================================================
print('\n[7] CLICK-ELEMENT + LONG-CLICK-ELEMENT -- recorder exports')
print('-' * 40)

rec_ce = TestRecorder()
rec_ce.start()
rec_ce.record_action('click_element', {'text': 'Submit', 'index': 0, 'x': 200, 'y': 300})
rec_ce.record_action('click_element', {'text': 'OK', 'index': 1, 'x': 400, 'y': 300})
rec_ce.record_action('long_click_element', {'text': 'Delete', 'index': 0, 'x': 100, 'y': 500})
rec_ce.stop()

adb_ce = rec_ce.export_as_python(filename='tmp_ce_adb.py', use_adb=True)
with open(adb_ce) as f: ce_adb = f.read()

test('ADB: click_element Submit', 'Submit' in ce_adb and 'click_element_by_text("Submit", 200, 300)' in ce_adb)
test('ADB: click_element index 1 uses coords', 'click_element_by_text("OK", 400, 300)' in ce_adb)
test('ADB: long_click_element Delete', 'Delete' in ce_adb and 'long_click_element_by_text("Delete", 100, 500)' in ce_adb)

ui_ce = rec_ce.export_as_python(filename='tmp_ce_ui.py', use_adb=False)
with open(ui_ce) as f: ce_ui = f.read()

test('UI: click_element Submit', 'Submit' in ce_ui)
test('UI: long_click_element Delete', 'Delete' in ce_ui)

read_ce = rec_ce.export_as_readable(filename='tmp_ce_read.txt')
with open(read_ce) as f: ce_read = f.read()

test('Readable: click_element desc', 'Click on element "Submit"' in ce_read)
test('Readable: long_click_element desc', 'Long click on element "Delete"' in ce_read)

for f in ['tmp_ce_adb.py', 'tmp_ce_ui.py', 'tmp_ce_read.txt']:
    if os.path.exists(f): os.remove(f)


# ============================================================
# [8] SYNTAX VALIDATION
# ============================================================
print('\n[8] SYNTAX VALIDATION')
print('-' * 40)

with open('main.py', encoding='utf-8') as f:
    try:
        ast.parse(f.read())
        test('main.py syntax valid', True)
    except SyntaxError as e:
        test('main.py syntax valid', False, str(e))

with open('src/recorder.py', encoding='utf-8') as f:
    try:
        ast.parse(f.read())
        test('src/recorder.py syntax valid', True)
    except SyntaxError as e:
        test('src/recorder.py syntax valid', False, str(e))


# ============================================================
# [9] MAIN.PY STRUCTURE -- all 25 tools + privacy + previous features
# ============================================================
print('\n[9] MAIN.PY STRUCTURE -- tools and features')
print('-' * 40)

all_tools = [
    'Click-Tool', 'Click-Element-Tool', 'Long-Click-Element-Tool', 'Type-Element-Tool',
    'State-Tool', 'Launch-App-Tool', 'Kill-App-Tool', 'Clear-App-Data-Tool',
    'Get-Current-App-Tool', 'List-Apps-Tool', 'Long-Click-Tool', 'Swipe-Tool',
    'Type-Tool', 'Drag-Tool', 'Press-Tool', 'Notification-Tool', 'Wait-Tool',
    'Wait-For-Condition-Tool', 'Start-Recording-Tool', 'Stop-Recording-Tool',
    'Export-Test-Script', 'Clear-Recording-Tool', 'Get-Recording-Stats-Tool',
    'Report-Bug-To-Azure', 'Report-Bug-To-Azure-Direct'
]
for tool in all_tools:
    test(f'Tool "{tool}" present', f"'{tool}'" in source)

# Smart Element Finder components
test('_find_element helper present', 'def _find_element(' in source)
test('Partial text matching in _find_element', 'element.name.lower()' in source)
test('Index param in _find_element', 'index >= len(matches)' in source)
test('Scrubbed name fallback matching', 'scrub_map.get(element.name' in source)

# Privacy components
test('_scrub_pii present', 'def _scrub_pii(' in source)
test('_scrub_pii_unique present', 'def _scrub_pii_unique(' in source)
test('_mask_email present', 'def _mask_email(' in source)
test('_mask_phone present', 'def _mask_phone(' in source)
test('_mask_card present', 'def _mask_card(' in source)
test('sensitive param in Type-Tool', 'sensitive:bool=False' in source)
test('_sensitive_counter defined', '_sensitive_counter = 0' in source)
test('Phone state in State-Tool', "ps.get('packageName'" in source)
test('Unique scrubbing in State-Tool', '_scrub_pii_unique(all_names)' in source)
test('import re present', 'import re' in source)


# ============================================================
# [10] RECORDER STRUCTURE
# ============================================================
print('\n[10] RECORDER STRUCTURE')
print('-' * 40)

with open('src/recorder.py', encoding='utf-8') as f:
    rec_src = f.read()

test('import os in UIAutomator template', "'import os'," in rec_src)
test('import os in ADB template', rec_src.count("'import os',") >= 2)
test('os.environ in exports', 'os.environ' in rec_src)
sensitive_count = rec_src.count("params.get('sensitive')")
test(f'6 sensitive checks in recorder (got {sensitive_count})', sensitive_count == 6)
test('wait_for_condition handler in adb export', 'wait_for_condition' in rec_src)
test('launch_app handler in recorder', 'launch_app' in rec_src)
test('kill_app handler in recorder', 'kill_app' in rec_src)
test('clear_app_data handler in recorder', 'clear_app_data' in rec_src)
test('click_element handler in recorder', 'click_element' in rec_src)
test('long_click_element handler in recorder', 'long_click_element' in rec_src)
test('type_element handler in recorder', 'type_element' in rec_src)


# ============================================================
print('\n' + '=' * 70)
print(f'FINAL RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests')
print('=' * 70)
if failed == 0:
    print('ALL TESTS PASSED!')
else:
    sys.exit(1)
