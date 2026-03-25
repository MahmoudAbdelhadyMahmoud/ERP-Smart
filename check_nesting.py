import sys

with open(r'c:\Users\LENOVO\Desktop\Neferdidi\backend\static\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    opens = line.count('<div')
    closes = line.count('</div>')
    old_count = count
    count += (opens - closes)
    if opens > 0 or closes > 0:
        # Avoid printing non-ASCII content
        tag_info = f"<{opens} open, {closes} close>"
        sys.stdout.buffer.write(f"{i+1:4}: {'  ' * old_count}{tag_info} (Depth: {count})\n".encode('utf-8'))
