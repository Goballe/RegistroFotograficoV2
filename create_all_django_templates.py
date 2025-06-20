import os
import shutil

# Directorios base para las plantillas
template_dirs = [
    "app/templates/django/forms",
    "app/templates/django/forms/widgets",
    "app/templates/django/forms/formsets",
]

# Asegurarse de que los directorios existan
for dir_path in template_dirs:
    os.makedirs(dir_path, exist_ok=True)

# Plantillas de formularios
form_templates = {
    "div.html": """{% if errors %}
    <div class="alert alert-danger">
        {% for error in errors %}
            <div>{{ error }}</div>
        {% endfor %}
    </div>
{% endif %}
{% for field in fields %}
    <div class="form-group mb-3">
        {{ field }}
    </div>
{% endfor %}""",

    "p.html": """{% if errors %}
    <p class="errorlist">
        {% for error in errors %}
            {{ error }}{% if not forloop.last %}<br>{% endif %}
        {% endfor %}
    </p>
{% endif %}
{% for field in fields %}
    <p>
        {{ field.label_tag }}
        {{ field }}
        {% if field.help_text %}
            <span class="helptext">{{ field.help_text }}</span>
        {% endif %}
        {% if field.errors %}
            <span class="errorlist">
                {% for error in field.errors %}
                    {{ error }}{% if not forloop.last %}<br>{% endif %}
                {% endfor %}
            </span>
        {% endif %}
    </p>
{% endfor %}""",

    "table.html": """{% if errors %}
    <tr>
        <td colspan="2">
            <ul class="errorlist">
                {% for error in errors %}
                    <li>{{ error }}</li>
                {% endfor %}
            </ul>
        </td>
    </tr>
{% endif %}
{% for field in fields %}
    <tr>
        <th>{{ field.label_tag }}</th>
        <td>
            {{ field }}
            {% if field.help_text %}
                <br><span class="helptext">{{ field.help_text }}</span>
            {% endif %}
            {% if field.errors %}
                <ul class="errorlist">
                    {% for error in field.errors %}
                        <li>{{ error }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        </td>
    </tr>
{% endfor %}""",

    "ul.html": """{% if errors %}
    <li>
        <ul class="errorlist">
            {% for error in errors %}
                <li>{{ error }}</li>
            {% endfor %}
        </ul>
    </li>
{% endif %}
{% for field in fields %}
    <li>
        {{ field.label_tag }}
        {{ field }}
        {% if field.help_text %}
            <span class="helptext">{{ field.help_text }}</span>
        {% endif %}
        {% if field.errors %}
            <ul class="errorlist">
                {% for error in field.errors %}
                    <li>{{ error }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    </li>
{% endfor %}""",

    "default.html": """{% if form.non_field_errors %}
  <div class="alert alert-danger">
    {% for error in form.non_field_errors %}
      <div>{{ error }}</div>
    {% endfor %}
  </div>
{% endif %}
{% for field in form.hidden_fields %}
  {{ field }}
{% endfor %}
{% for field in form.visible_fields %}
  <div class="form-group mb-3">
    {% if field.label %}
      <label for="{{ field.id_for_label }}">{{ field.label }}{% if field.field.required %}<span class="text-danger">*</span>{% endif %}</label>
    {% endif %}
    {{ field }}
    {% if field.help_text %}
      <small class="form-text text-muted">{{ field.help_text }}</small>
    {% endif %}
    {% if field.errors %}
      <div class="invalid-feedback d-block">
        {% for error in field.errors %}
          <div>{{ error }}</div>
        {% endfor %}
      </div>
    {% endif %}
  </div>
{% endfor %}"""
}

# Plantillas de widgets
widget_templates = {
    "attrs.html": """{% for name, value in widget.attrs.items %}{% if value is not False %} {{ name }}{% if value is not True %}="{{ value|stringformat:'s' }}"{% endif %}{% endif %}{% endfor %}""",
    
    "checkbox.html": """<input type="checkbox" name="{{ widget.name }}" {% if widget.value != None %}value="{{ widget.value|stringformat:'s' }}"{% endif %}{% include "django/forms/widgets/attrs.html" %}>{% if widget.wrap_label %}<label{% if widget.attrs.id %} for="{{ widget.attrs.id }}"{% endif %}>{{ widget.label }}</label>{% endif %}""",
    
    "checkbox_option.html": """{% if widget.wrap_label %}<label{% if widget.attrs.id %} for="{{ widget.attrs.id }}"{% endif %}>{% endif %}<input type="checkbox" name="{{ widget.name }}" {% if widget.value != None %}value="{{ widget.value|stringformat:'s' }}"{% endif %}{% include "django/forms/widgets/attrs.html" %}>{% if widget.wrap_label %}{{ widget.label }}</label>{% endif %}""",
    
    "checkbox_select.html": """{% for group, options, index in widget.optgroups %}{% if group %}
  <div>{{ group }}</div>{% endif %}
  {% for option in options %}
    <div>{% include option.template_name with widget=option %}</div>
  {% endfor %}{% endfor %}""",
    
    "clearable_file_input.html": """{% if widget.is_initial %}{{ widget.initial_text }}: <a href="{{ widget.value.url }}">{{ widget.value }}</a>{% if not widget.required %}
<input type="checkbox" name="{{ widget.checkbox_name }}" id="{{ widget.checkbox_id }}"{% if widget.attrs.disabled %} disabled{% endif %}>
<label for="{{ widget.checkbox_id }}">{{ widget.clear_checkbox_label }}</label>{% endif %}<br>
{{ widget.input_text }}:{% endif %}
<input type="{{ widget.type }}" name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>""",
    
    "date.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "datetime.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "email.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "file.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "hidden.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "input.html": """<input type="{{ widget.type }}" name="{{ widget.name }}"{% if widget.value != None %} value="{{ widget.value|stringformat:'s' }}"{% endif %}{% include "django/forms/widgets/attrs.html" %}>""",
    
    "multiple_hidden.html": """{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}""",
    
    "multiple_input.html": """{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}""",
    
    "multiwidget.html": """{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}""",
    
    "number.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "option.html": """<option value="{{ widget.value|stringformat:'s' }}"{% include "django/forms/widgets/attrs.html" %}>{{ widget.label }}</option>""",
    
    "password.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "radio.html": """{% for group, options, index in widget.optgroups %}{% for option in options %}
<input type="radio" name="{{ widget.name }}" value="{{ option.value|stringformat:'s' }}" {% include "django/forms/widgets/attrs.html" with widget=option %} {% if option.selected %}checked{% endif %}>
<label {% if option.attrs.id %} for="{{ option.attrs.id }}"{% endif %}>{{ option.label }}</label>{% endfor %}{% endfor %}""",
    
    "radio_option.html": """{% if widget.wrap_label %}<label{% if widget.attrs.id %} for="{{ widget.attrs.id }}"{% endif %}>{% endif %}<input type="radio" name="{{ widget.name }}" value="{{ widget.value|stringformat:'s' }}"{% include "django/forms/widgets/attrs.html" %}>{% if widget.wrap_label %}{{ widget.label }}</label>{% endif %}""",
    
    "select.html": """<select name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>{% for group_name, group_choices, group_index in widget.optgroups %}{% if group_name %}
  <optgroup label="{{ group_name }}">{% endif %}{% for option in group_choices %}
  {% include option.template_name with widget=option %}{% endfor %}{% if group_name %}
  </optgroup>{% endif %}{% endfor %}
</select>""",
    
    "select_date.html": """{% for select in widget.subwidgets %}{% include select.template_name %}{% endfor %}""",
    
    "select_option.html": """{% include "django/forms/widgets/option.html" %}""",
    
    "splitdatetime.html": """{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}""",
    
    "splithiddendatetime.html": """{% for widget in widget.subwidgets %}{% include widget.template_name %}{% endfor %}""",
    
    "text.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "textarea.html": """<textarea name="{{ widget.name }}"{% include "django/forms/widgets/attrs.html" %}>
{% if widget.value %}{{ widget.value }}{% endif %}</textarea>""",
    
    "time.html": """{% include "django/forms/widgets/input.html" %}""",
    
    "url.html": """{% include "django/forms/widgets/input.html" %}"""
}

# Plantillas de formsets
formset_templates = {
    "table.html": """{{ formset.management_form }}
<table>
    {% for form in formset %}
        {% if forloop.first %}
            <thead>
                <tr>
                    {% for field in form.visible_fields %}
                        <th>{{ field.label }}</th>
                    {% endfor %}
                </tr>
            </thead>
        {% endif %}
        <tr>
            {% for field in form.visible_fields %}
                <td>
                    {{ field.errors }}
                    {{ field }}
                </td>
            {% endfor %}
            {% for field in form.hidden_fields %}
                {{ field }}
            {% endfor %}
        </tr>
    {% endfor %}
</table>""",
    
    "p.html": """{{ formset.management_form }}
{% for form in formset %}
    <div class="formset-form">
        {% for field in form.visible_fields %}
            <p>
                {{ field.label_tag }}
                {{ field }}
                {{ field.errors }}
            </p>
        {% endfor %}
        {% for field in form.hidden_fields %}
            {{ field }}
        {% endfor %}
    </div>
{% endfor %}""",
    
    "ul.html": """{{ formset.management_form }}
<ul>
    {% for form in formset %}
        <li>
            <ul>
                {% for field in form.visible_fields %}
                    <li>
                        {{ field.label_tag }}
                        {{ field }}
                        {{ field.errors }}
                    </li>
                {% endfor %}
                {% for field in form.hidden_fields %}
                    {{ field }}
                {% endfor %}
            </ul>
        </li>
    {% endfor %}
</ul>""",
    
    "div.html": """{{ formset.management_form }}
{% for form in formset %}
    <div class="formset-form">
        {% for field in form.visible_fields %}
            <div class="form-group">
                {{ field.label_tag }}
                {{ field }}
                {{ field.errors }}
            </div>
        {% endfor %}
        {% for field in form.hidden_fields %}
            {{ field }}
        {% endfor %}
    </div>
{% endfor %}"""
}

# Crear las plantillas de formularios
for template_name, content in form_templates.items():
    file_path = os.path.join(template_dirs[0], template_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Creada plantilla de formulario: {template_name}")

# Crear las plantillas de widgets
for template_name, content in widget_templates.items():
    file_path = os.path.join(template_dirs[1], template_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Creada plantilla de widget: {template_name}")

# Crear las plantillas de formsets
for template_name, content in formset_templates.items():
    file_path = os.path.join(template_dirs[2], template_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Creada plantilla de formset: {template_name}")

print("\nTodas las plantillas han sido creadas correctamente.")
