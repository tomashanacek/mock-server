# -*- coding: utf-8 -*-

import markdown2
import re


def create_todos(content, protocol, ref_id):
    content = re.sub(
        r"\[ \](.*)",
        r'<label><input type="checkbox" class="todo-checkbox" '
        r'data-protocol="%s" data-id="%s">\1</label>' %
        (protocol, ref_id),
        content)

    content = re.sub(
        r"\[x\](.*)",
        r'<label><input type="checkbox" class="todo-checkbox" '
        r'data-protocol="%s" data-id="%s" checked>\1</label>' %
        (protocol, ref_id),
        content)

    return content


def markdown(content, protocol="", ref_id=""):

    content = create_todos(content, protocol, ref_id)

    param_text = '<dt>%s</dt><dd><div><strong>%s</strong> '\
                 '(<i>%s</i>)</div>'\
                 '<div><strong>Example</strong>: %s</div>'\
                 '<p class="description">%s</p></dd>'

    new_content = []
    param_data = None
    in_description = False
    description = []

    c = re.compile(r":(.+):(.+):(.+):(.+)")

    for line in content.split("\n"):
        m = c.match(line)
        if m:
            if param_data:
                new_content.append(
                    param_text % (param_data + ("\n".join(description), )))
                param_data = None
                description = []

            param_data = list(m.groups())
            param_data[0] = param_data[0].replace("_", "\_")
            param_data = tuple(param_data)
            in_description = True
        elif in_description:
            description.append(line)
        else:
            new_content.append(line)

    if param_data:
        new_content.append(
            param_text % (param_data + ("\n".join(description), )))

    return markdown2.markdown("\n".join(new_content), extras=["wiki-tables"])
