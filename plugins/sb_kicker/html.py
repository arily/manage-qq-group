class HTML:
    @staticmethod
    def html(*content: str):
        return f"""
        <!DOCTYPE html>
        <html>
        {"".join(content)}
        </html>
    """

    @staticmethod
    def head(*content: str):
        return f"""
        <head>
            <meta charset="UTF-8">
            {"".join(content)}
        </head>
    """

    @staticmethod
    def style(content: str):
        return HTML.tag("style", content)

    @staticmethod
    def body(*content: str, **attrs: str):
        return HTML.tag("body", "".join(content), **attrs)

    @staticmethod
    def tag(tag: str, *content: str, **attrs: str):
        if " " in tag:
            raise Exception("invalid tag")

        return f"""<{tag} {HTML.unpack_attrs(attrs)}>{"".join(content)}</{tag}>"""

    @staticmethod
    def unpack_attrs(attrs: dict[str, str]):
        attrs["class"] = attrs["class_name"]
        return " ".join([f'{k}="{HTML.escape(v)}"' for k, v in attrs if k is not None])

    @staticmethod
    def escape(str: str):
        return str.replace('"', '"').replace('"', '"')