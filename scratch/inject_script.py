import os

templates_dir = "/Users/apple/VisualCode/newproject/frontend/templates"
script_tag = '  <script src="/static/js/theme-toggle.js"></script>\n</head>'

for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if already injected
        if "theme-toggle.js" in content:
            print(f"Skipping {filename} - already injected")
            continue
            
        if "</head>" in content:
            new_content = content.replace("</head>", script_tag, 1)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Successfully injected theme-toggle.js into {filename}")
        else:
            print(f"Warning: Could not find </head> in {filename}")
