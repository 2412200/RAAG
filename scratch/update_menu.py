import os
import re

templates_dir = "/Users/apple/VisualCode/newproject/frontend/templates"
files_to_update = [
    "search.html", "groceries.html", "beauty.html", "orders.html",
    "homeappliances.html", "kids.html", "womens.html", "furniture.html",
    "books.html", "pharma.html", "mens-wear.html", "home.html"
]

# Regex pattern to match the existing sidebar menu block
pattern = re.compile(
    r'(<nav class="sidebar-menu">)\s*'
    r'<a href="/home" id="nav-home" class="menu-item[^"]*">\s*Home\s*</a>\s*'
    r'<a href="/orders" id="nav-orders" class="menu-item[^"]*">\s*My Orders\s*</a>\s*'
    r'(</nav>)',
    re.DOTALL
)

replacement = (
    r'\1\n'
    r'          <a href="/home" id="nav-home" class="menu-item">\n'
    r'            Home\n'
    r'          </a>\n'
    r'          <a href="/cart" id="nav-cart" class="menu-item">\n'
    r'            My Cart\n'
    r'          </a>\n'
    r'          <a href="/orders" id="nav-orders" class="menu-item">\n'
    r'            My Orders\n'
    r'          </a>\n'
    r'        \2'
)

for filename in files_to_update:
    filepath = os.path.join(templates_dir, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename}: path not found")
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content, count = pattern.subn(replacement, content)
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully updated menu in {filename}")
    else:
        print(f"Failed to match menu pattern in {filename}")

print("Done menu updates!")
