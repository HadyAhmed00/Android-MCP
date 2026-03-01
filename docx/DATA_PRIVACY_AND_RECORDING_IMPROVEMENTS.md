# Updates — Data Privacy, Smart Recording, and Test Cleanup

This document covers the changes made in the current development cycle.

---

## 1. PII Scrubbing in State-Tool Output

**Problem:** When an agent calls State-Tool to read the screen, element names containing emails, phone numbers, or credit card numbers were sent in plain text.

**What changed:** State-Tool now masks sensitive patterns before returning them to the agent.

| Pattern | Before | After |
|---------|--------|-------|
| Email | `john.doe@gmail.com` | `joh***e@gmail.com` |
| Phone | `+1 (555) 123-4567` | `***-***-4567` |
| Credit card | `4111 1111 1111 1234` | `4111-****-1234` |

The masking only applies to the text returned by the tool. Internal element data stays unchanged so clicks and interactions still work correctly.

**Collision handling:** If two elements have different emails that mask to the same string (e.g. `john@gmail.com` and `jane@gmail.com` both become `j***@gmail.com`), the scrubber reveals one extra character per round until each masked name is unique. This lets the agent tell them apart without exposing the full address.

---

## 2. Phone Metadata in State-Tool

State-Tool now includes a one-line header at the top of its output:

```
App: com.example.app | Activity: MainActivity | Keyboard: False
```

This tells the agent which app is in the foreground, which screen is active, and whether the soft keyboard is currently open — without needing an extra tool call.

---

## 3. Sensitive Typing — `sensitive` Parameter

**Type-Tool** and **Type-Element-Tool** both accept a new `sensitive` parameter.

When `sensitive=True`:
- The typed text is replaced with `****` in the tool response so it does not appear in the conversation.
- The recorder saves an environment variable placeholder instead of the actual text.

**Example usage:**

```
Type-Tool(text="mypassword123", x=540, y=1180, sensitive=True)
```

Response returned to the agent:

```
Typed "****" on (540, 1180)
```

---

## 4. Sensitive Credentials in Exported Scripts

When a recording contains sensitive input (typed with `sensitive=True`), the exported Python script uses an environment variable instead of hardcoding the value.

**Exported script (ADB format):**

```python
# Action 6: Type sensitive input (from env var)
device.type_text(os.environ["MAKTABY_PASSWORD"])
```

**Running the exported script:**

```bash
MAKTABY_PASSWORD=your_password python recorded_test.py
```

The variable name is generated automatically from the element or context (e.g. typing into a "Password" field produces `PASSWORD_INPUT`).

---

## 5. Smart Element Finding in Exported Scripts

**Problem:** Exported scripts used raw coordinates like `device.click(840, 1972)`. If the screen resolution or layout changes, the click lands in the wrong place.

**What changed:** When an element click is recorded using Click-Element-Tool or Long-Click-Element-Tool, the exported script now tries to find the element by its text label first, and only falls back to the saved coordinates if the text is not found.

**ADB format (exported script):**

```python
# Action 3: Click element "Compose"  [coords: (840, 1972)]
device.click_element_by_text("Compose", 840, 1972)
```

`click_element_by_text` works by:
1. Dumping the current UI hierarchy via UIAutomator
2. Searching for a node whose `text` or `content-desc` contains the target string
3. Clicking the center of the matched element
4. If no match is found, clicking the recorded coordinates as a fallback

**UIAutomator format (exported script):**

```python
# Action 3: Click element "Compose"  [coords: (840, 1972)]
_el = device(text="Compose")
if not _el.exists(timeout=3):
    _el = device(textContains="Compose")
if _el.exists(timeout=2):
    _el.click()
else:
    device.click(840, 1972)  # coords fallback
```

Both fallback strategies are present because:
- Text-first handles screen size/resolution changes (same text, different position)
- Coordinates-fallback handles text changes (same position, different or no text label)

---

## 6. Sleep Time Cap in Exported Scripts

**Problem:** During recording, actions like UIAutomator dumps and waiting for elements added several seconds of overhead between steps. These timestamps were written as `time.sleep(15.0)` in the exported script, making replays unnecessarily slow and sometimes causing timing issues with the soft keyboard.

**Fix:** Sleep times between actions in exported scripts are now capped at **2.0 seconds**.

---

## 7. _find_element Matches Scrubbed Names

Agents read scrubbed element names from State-Tool. When they pass those scrubbed names to Click-Element-Tool, the internal `_find_element` function now checks both the real name and the scrubbed name, so the element is still found correctly.

---

## 8. Test Cleanup

The following test files that required a physical Android device connected via ADB have been removed:

- `test_device.py` — device integration tests
- `test_flows.py` — full scenario recording and replay
- `recorded_maktaby_login.py` — generated replay script
- `docx/test_mcp_helper_integration.py` — MCP Helper connection tests

The remaining test file is `test_unit.py`, which runs entirely on mocks and does not require a device. Run it with:

```bash
python test_unit.py
```
