def slugify(string):
    new_string = ""
    no_nos = [
        "\\",
        "/",
        "\'",
        "\"",
        "|",
        ":",
        "*",
        ",",
    ]
    for letter in string:
        if letter not in no_nos:
            new_string += letter
    return new_string