def complain(exception, message, source, lineno, col_offset):
    message = "Line {0}: {1}".format(lineno, message)
    quoted = source.split("\n")[lineno - 1]
    arrow = "-" * (col_offset + 4) + "^"
    raise exception(message + "\n    " + quoted + "\n" + arrow)
