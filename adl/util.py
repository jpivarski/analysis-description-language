def complain(exception, message, lexpos, lexer):
    message = "Line {0}: {1}".format(lexer.lineno, message)
    quoted = lexer.lexdata.split("\n")[lexer.lineno - 1]
    arrow = "-" * (lexpos - lexer.linepos + 4) + "^"
    raise exception(message + "\n    " + quoted + "\n" + arrow)
