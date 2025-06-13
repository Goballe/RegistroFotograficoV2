with open('views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the incorrect URL pattern with the correct one
fixed_content = content.replace(
    "reverse('obervaciones:detalle_observacion'",
    "reverse('obervaciones:ver_observacion'"
)

# Write the fixed content back to the file
with open('views.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("URL pattern has been fixed.")
