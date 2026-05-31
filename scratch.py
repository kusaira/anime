import os

with open('handlers/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# I need to revert <code> to backticks maybe? No, let's keep <code> and add parse_mode="HTML".
# But wait, anime titles can contain HTML tags if they have <>. So html.escape is needed.
# Since the user specifically asked for backticks `47194_2`, let's just give them backticks and set parse_mode="Markdown".
# Wait, let's just use `parse_mode="HTML"` and keep <code>, because it's much safer than Markdown (where _ and * crash).
# Let's see how I can use `parse_mode="HTML"`.
pass
