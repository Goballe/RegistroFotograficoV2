import os
import sys

# Lista de widgets comunes de Django
widgets = [
    'text', 'number', 'email', 'url', 'password', 'hidden', 'date', 'datetime',
    'time', 'textarea', 'checkbox', 'select', 'select_date', 'radio', 'file',
    'clearable_file_input', 'multiple_hidden', 'splitdatetime', 'splithiddendatetime',
    'multiwidget', 'option', 'attrs', 'input'
]

# Contenido base para los widgets que heredan de input.html
input_based = """{% include "django/forms/widgets/input.html" %}"""

# Contenido para attrs.html
attrs_content = """{% for name, value in widget.attrs.items %}{% if value is not False %} {{ name }}{% if value is not True %}="{{ value|stringformat:'s' }}"{% endif %}{% endif %}{% endfor %}"""

# Contenido para input.html
input_content = """<input type="{{ widget.type }}" name="{{ widget.name }}"{% if widget.value != None %} value="{{ widget.value|stringformat:'s' }}"{% endif %}{% include "django/forms/widgets/attrs.html" %}>"""

# Contenido para textarea.html
textarea_content = """<textarea name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>
{% if widget.value %}{{ widget.value }}{% endif %}</textarea>"""

# Contenido para select.html
select_content = """<select name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>{% for group_name, group_choices, group_index in widget.optgroups %}{% if group_name %}
  <optgroup label="{{ group_name }}">{% endif %}{% for option in group_choices %}
  {% include option.template_name with widget=option %}{% endfor %}{% if group_name %}
  </optgroup>{% endif %}{% endfor %}
</select>"""

# Contenido para option.html
option_content = """<option value="{{ widget.value|stringformat:'s' }}"{% include "django/forms/widgets/attrs.html" %}>{{ widget.label }}</option>"""

# Contenido para checkbox.html
checkbox_content = """<input type="checkbox" name="{{ widget.name }}" {% if widget.value != None %}value="{{ widget.value|stringformat:'s' }}"{% endif %}{% include "django/forms/widgets/attrs.html" %}>{% if widget.wrap_label %}<label{% if widget.attrs.id %} for="{{ widget.attrs.id }}"{% endif %}>{{ widget.label }}</label>{% endif %}"""

# Contenido para clearable_file_input.html
clearable_file_input_content = """{% if widget.is_initial %}{{ widget.initial_text }}: <a href="{{ widget.value.url }}">{{ widget.value }}</a>{% if not widget.required %}
<input type="checkbox" name="{{ widget.checkbox_name }}" id="{{ widget.checkbox_id }}"{% if widget.attrs.disabled %} disabled{% endif %}>
<label for="{{ widget.checkbox_id }}">{{ widget.clear_checkbox_label }}</label>{% endif %}<br>
{{ widget.input_text }}:{% endif %}
<input type="{{ widget.type }}" name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>"""

# Contenido para select_date.html
select_date_content = """{% for select in widget.subwidgets %}{% include select.template_name %}{% endfor %}"""

# Contenido para radio.html
radio_content = """{% for group, options, index in widget.optgroups %}{% for option in options %}
<input type="radio" name="{{ widget.name }}" value="{{ option.value|stringformat:'s' }}" {% include "django/forms/widgets/attrs.html" with widget=option %} {% if option.selected %}checked{% endif %}>
<label {% if option.attrs.id %} for="{{ option.attrs.id }}"{% endif %}>{{ option.label }}</label>{% endfor %}{% endfor %}"""

# Directorio base para las plantillas
template_dir = "app/templates/django/forms/widgets"

# Crear el directorio si no existe
os.makedirs(template_dir, exist_ok=True)

# Mapeo de widgets a su contenido
widget_content = {
    'text': input_based,
    'number': input_based,
    'email': input_based,
    'url': input_based,
    'password': input_based,
    'hidden': input_based,
    'date': input_based,
    'datetime': input_based,
    'time': input_based,
    'textarea': textarea_content,
    'checkbox': checkbox_content,
    'select': select_content,
    'select_date': select_date_content,
    'radio': radio_content,
    'file': input_based,
    'clearable_file_input': clearable_file_input_content,
    'multiple_hidden': "{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}",
    'splitdatetime': "{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}",
    'splithiddendatetime': "{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}",
    'multiwidget': "{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}",
    'option': option_content,
    'attrs': attrs_content,
    'input': input_content
}

# Crear las plantillas
for widget in widgets:
    file_path = os.path.join(template_dir, f"{widget}.html")
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(widget_content.get(widget, input_based))
        print(f"Creada plantilla para {widget}")
    else:
        print(f"La plantilla para {widget} ya existe")

print("Todas las plantillas de widgets han sido creadas.")
