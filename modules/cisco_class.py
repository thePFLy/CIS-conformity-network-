from re import findall

def complete_command(template):
    placeholders = findall(r'<(.*?)>|\{(.*?)\}', template)
    values = []

    for placeholder in placeholders:
        if placeholder[0]:
            question = f"Entrez la valeur pour '{placeholder[0].replace('|', 'ou')}': "
        else:
            question = f"Entrez la valeur pour '{placeholder[1].replace('|', 'ou' )}': "
        value = input(question)
        values.append(value)

    completed_string = template
    for placeholder, value in zip(placeholders, values):
        completed_string = completed_string.replace('<' + placeholder[0] + '>', value)
        completed_string = completed_string.replace('{' + placeholder[1] + '}', value)

    return completed_string


def is_expected_output(output, expected_output):
    if expected_output.startswith("*") and expected_output.endswith("*"):
        return expected_output[1:-1] in output
    elif expected_output.startswith("*"):
        return output.endswith(expected_output[1:])
    elif expected_output.endswith("*"):
        return output.startswith(expected_output[:-1])
    else:
        return output == expected_output
