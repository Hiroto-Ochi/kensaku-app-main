import os
import json
from utils.logger import logger
from utils.bing import BingSearchClient
from utils.html import HtmlTool
from utils.search import AzureSearchClient


class OpenAITools:

    def __init__(self, tools_definition_path: str = "openai_tools.json"):

        # ツールの定義ファイル(JSON)を読み込む
        tools_definition_path = os.path.join(os.path.dirname(__file__), tools_definition_path)
        if not os.path.exists(tools_definition_path):
            raise FileNotFoundError(f"Tools definition file not found: {tools_definition_path}")
        with open(tools_definition_path, "r") as f:
            self.tools_definition = json.load(f)

        # Bing Search API に関する設定がされていない場合は、Web検索とニュース検索の機能を無効化
        if not os.environ.get("BING_SEARCH_API_KEY"):
            self.tools_definition = [t for t in self.tools_definition if t["function"]["name"] != "search_web_pages"]
            self.tools_definition = [t for t in self.tools_definition if t["function"]["name"] != "search_news"]

        # Azure AI Search に関する設定がされていない場合は、ドキュメント検索の機能を無効化
        if not (os.environ.get("AZURE_SEARCH_ENDPOINT") and os.environ.get("AZURE_SEARCH_QUERY_KEY") and os.environ.get("AZURE_SEARCH_INDEX_NAME")):
            self.tools_definition = [t for t in self.tools_definition if t["function"]["name"] != "search_documents"]

    def search_web_pages(self, query: str, count: int = 3, offset: int = 0) -> str:
        """
        Bing Web検索APIを利用して、指定されたクエリに一致するWebページを検索する。

        Args:
            query (str): 検索クエリ
            count (int): 取得する検索結果の最大数
            offset (int): 検索結果のオフセット

        Returns:
            str: 検索結果のJSON文字列
        """
        logger.info(f"search_web_pages: query={query}, count={count}, offset={offset}")
        bing = BingSearchClient()
        pages = bing.search_web_pages(query, count=count, offset=offset)
        return json.dumps(pages, ensure_ascii=False)

    def search_news(self, query: str, count: int = 3, offset: int = 0) -> str:
        """
        Bing News検索APIを利用して、指定されたクエリに一致するニュース記事を検索する。

        Args:
            query (str): 検索クエリ
            count (int): 取得する検索結果の最大数
            offset (int): 検索結果のオフセット

        Returns:
            str: 検索結果のJSON文字列
        """
        logger.info(f"search_news: query={query}, count={count}, offset={offset}")
        bing = BingSearchClient()
        news = bing.search_news(query, count=count, offset=offset)
        return json.dumps(news, ensure_ascii=False)

    def search_documents(self, query: str, count: int = 3, offset: int = 0) -> str:
        logger.info(f"search_documents: query={query}, count={count}, offset={offset}")
        search_client = AzureSearchClient()
        docs = search_client.search(query, top=count, skip=offset)
        return json.dumps(docs, ensure_ascii=False)

    def get_html_by_url(self, url: str) -> str:
        """
        指定されたURLのWebページのHTMLを取得する

        Args:
            url (str): WebページのURL

        Returns:
            str: WebページのHTML
        """
        logger.info(f"get_html_by_url: url={url}")
        html = HtmlTool.get_html(url)
        html = HtmlTool.remove_unnecessary_html_tags(html)
        return html
