#The script 
#cache_buster.py
# automates the process of forcing client browsers to download the updated CSS and JS files instead of loading outdated, cached versions.

import os

templates_dir = "/Users/apple/VisualCode/newproject/frontend/templates"
files_to_update = [
    "search.html", "groceries.html", "beauty.html", "orders.html",
    "homeappliances.html", "kids.html", "womens.html", "furniture.html",
    "books.html", "pharma.html", "mens-wear.html", "home.html", "cart.html"
]

for filename in files_to_update:
    filepath = os.path.join(templates_dir, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename}: path not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated = content
    for v in ["1.0.0", "1.0.1", "1.0.2", "1.0.3"]:
        if f"cart.css?v={v}" in updated:
            updated = updated.replace(f"cart.css?v={v}", "cart.css?v=1.0.4")
            print(f"Updated cart.css version in {filename}")
        if f"cart.js?v={v}" in updated:
            updated = updated.replace(f"cart.js?v={v}", "cart.js?v=1.0.4")
            print(f"Updated cart.js version in {filename}")
        
    if updated != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
            
print("Done!")
