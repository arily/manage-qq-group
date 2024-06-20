import mistune
from playwright.async_api import async_playwright


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
        if "class_name" in attrs.keys():
            attrs["class"] = attrs["class_name"]
        return " ".join([f'{k}="{HTML.escape(v)}"' for k, v in attrs.items() if attrs.keys()])

    @staticmethod
    def escape(s: str):
        return s.replace('"', '"').replace('"', '"')


def trans_md_to_html(md: str, custom_head: str = ""):
    return HTML.html(
        HTML.head(HTML.style(open("resources/css/github-markdown.css").read())),
        custom_head,
        HTML.body(
            HTML.tag(
                "article",
                mistune.html(md),
                class_name="markdown-body",
            ),
            style="padding: 30px",
        ),
    )


async def screenshot_local_html(html: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("about:blank")
        await page.set_content(html)
        return await page.screenshot(full_page=True)
