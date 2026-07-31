import re
import os

with open('src/App.jsx', 'r') as f:
    content = f.read()

print("File size:", len(content))
