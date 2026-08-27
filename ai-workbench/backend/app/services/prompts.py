import re

# template_string = "Hello {{ user.name }}, your balance is {{ currency }}{{ user.balance }}."

# data_context = {
#     "currency": "$",
#     "user": {
#         "name": "Alice",
#         "balance": 150
#     }
# }

# # Running the function
# output = render_prompt(template_string, data_context)

def render_prompt(
    template: str,
    context: dict,
) -> str:

    result = template

    pattern = r"\{\{([^}]+)\}\}" # search text wrap inside {{}}

    matches = re.findall(
        pattern,
        template,
    )

    for expression in matches:

        expression = expression.strip()

        value = resolve_expression(
            expression,
            context,
        )

        result = result.replace(
            "{{" + expression + "}}",
            str(value),
        )

    return result


def resolve_expression(
    expression: str,
    context: dict,
):

    if expression in context:
        return context[expression]

    parts = expression.split(".")

    current = context

    for part in parts:

        if isinstance(current, dict):
            current = current.get(part)

        else:
            return ""

        if current is None:
            return ""

    return current