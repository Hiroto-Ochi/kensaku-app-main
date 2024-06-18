import requests
from bs4 import BeautifulSoup, Comment


class HtmlTool:

    @staticmethod
    def get_html(url: str) -> str:
        """
        指定されたURLからコンテンツを取得

        Parameters:
        url (str): 取得するコンテンツのURL

        Returns:
        str: 取得したコンテンツの文字列形式
        """
        resp = requests.get(url)
        try:
            return resp.content.decode("utf-8")
        except:
            try:
                return resp.content.decode("shift_jis")
            except:
                return resp.text

    @staticmethod
    def remove_unnecessary_html_tags(html: str, required_attrs: list[str] = ["href", "src", "alt", "title"]) -> str:
        """
        不要なHTMLタグを削除する

        Parameters:
        html (str): HTML文字列

        Returns:
        str: 不要なHTMLタグを削除したHTML文字列
        """

        # BeautifulSoup を使ってHTMLを解析する
        soup = BeautifulSoup(html, "html.parser")

        # 不要なタグ要素を定義する
        unnecessary_tags = [
            "head",
            "meta",
            "style",
            "link",
            "script",
            "noscript",
            "header",
            "footer",
            "nav",
            "img",
            "svg",
            "form",
            "select",
            "input",
            "textarea",
            "button",
            "i",
            "iframe",
            "figure",
            "object",
            "audio",
            "video",
            "progress",
            "canvas",
            "picture",
        ]

        # 不要なタグ要素を削除する
        for tag in unnecessary_tags:
            for tag_elm in soup.find_all(tag):
                tag_elm.extract()

        # 不要なタグ要素を抽出するクエリセレクタを定義
        unnecessary_tag_selecters = [
            "div.header",
            "div.footer",
            "div.page-header",
            "div.page-footer",
            "div.nav",
        ]

        # 不要なタグ要素をクエリセレクタで削除する
        for selector in unnecessary_tag_selecters:
            for tag_elm in soup.select(selector):
                tag_elm.extract()

        # メインコンテンツのある部分のみに限定する
        find_methods = [
            lambda elm: elm.find("main"),
            lambda elm: elm.find("section#main"),
            lambda elm: elm.find("section#main-content"),
            lambda elm: elm.find("section.main"),
            lambda elm: elm.find("section.main-content"),
            lambda elm: elm.find("div#main"),
            lambda elm: elm.find("div#main-content"),
            lambda elm: elm.find("div.main"),
            lambda elm: elm.find("div.main-content"),
            lambda elm: elm.find("body"),
        ]
        for find_method in find_methods:
            elm = find_method(soup)
            if elm is not None:
                break
        if elm is not None:
            soup = elm

        # 中身のない要素を削除する
        for tag in soup.find_all():
            if tag.text.strip() == "":
                tag.extract()

        # タグの必要な属性以外の属性を全て削除する
        for tag in soup.find_all():
            tag.attrs = {key: tag.attrs[key] for key in tag.attrs.keys() if key in required_attrs}

        # コメントを削除する
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

        # 余分なdivを排除する
        for div in soup.find_all("div"):
            div.unwrap()

        # HTMLを文字列に変換する
        processed_html = str(soup)

        # 連続する改行を削除する
        processed_html = processed_html.replace("\n", "")

        # 連続する空白を削除する
        processed_html = processed_html.strip()

        return processed_html
