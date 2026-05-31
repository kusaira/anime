import re

with open('handlers/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace any occurrence of `await message.answer(text...)` that does not have parse_mode="HTML"
lines = c.split('\n')
for i, line in enumerate(lines):
    if 'await message.answer(text' in line and 'parse_mode' not in line:
        # replace the last parenthesis with `, parse_mode="HTML")`
        idx = line.rfind(')')
        if idx != -1:
            lines[i] = line[:idx] + ', parse_mode="HTML"' + line[idx:]

c = '\n'.join(lines)

with open('handlers/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
