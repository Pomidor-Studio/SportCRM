from django.template import Engine, Template, TemplateSyntaxError
from django.template.base import Lexer, Parser, TokenType


class EasyEngine(Engine):
    default_builtins = [
        'django.template.defaultfilters'
    ]


class EasyLexer(Lexer):
    def create_token(self, token_string, position, lineno, in_tag):
        token = super().create_token(token_string, position, lineno, in_tag)
        if token.token_type == TokenType.BLOCK:
            token.token_type = TokenType.TEXT
        return token


class EasyTemplate(Template):
    def compile_nodelist(self):
        """
        Parse and compile the template source into a nodelist. If debug
        is True and an exception occurs during parsing, the exception is
        is annotated with contextual line information where it occurred in the
        template source.
        """
        lexer = EasyLexer(self.source)

        tokens = lexer.tokenize()
        parser = EasyParser(
            tokens, self.engine.template_libraries,
            self.engine.template_builtins,
            self.origin,
        )

        try:
            return parser.parse()
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)
            raise


def empty_filter(data):
    return data


class EasyParser(Parser):
    def find_filter(self, filter_name):
        try:
            return super().find_filter(filter_name)
        except TemplateSyntaxError:
            return empty_filter
