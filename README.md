# RAG での質問回答を試すためのサンプル Web アプリ
ユーザからの質問に対して Azure AI Search や Bing Search API の情報を基に Azure OpenAI Service で回答させる、いわゆる RAG に動作を行う Web アプリケーションをデプロイするためのコードです。  
Azure OpenAI Service を活用した RAG の動作をクイックに試してみたい時に活用できます。

![動作の例](.images/how-it-work.gif)

## 使い方

### Azure へのデプロイ
以下のボタンをクリックすることで、Web アプリケーション動作に必要な Azure リソースをデプロイすることができます。  
  
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmahiya%2Fsample-rag-chat-app%2Fmain%2Fazuredeploy.json)

[Deploy to Azure] ボタンをクリックすると、Azure Portal のカスタムデプロイのページが表示されます。
![Azure Portal でデプロイを開始する](.images/deploy-1.jpg)

以下を情報を指定します。
- Azure リソースをデプロイする先の [Azure サブスクリプション]
- Azure リソースをデプロイする先の [リソースグループ]
- 回答生成に使用する Azure OpenAI Service アカウントのエンドポイント
- 回答生成に使用する Azure OpenAI Service アカウントのキー
- 回答生成に使用する Azure OpenAI Service アカウントにおけるデプロイの名前 (モデル名ではなくデプロイ名)

> 参考: [操作方法: Azure OpenAI Service リソースを作成してデプロイする - Azure OpenAI | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/ai-services/openai/how-to/create-resource?pivots=webportal)  

もし回答生成の情報源として Azure AI Search を使用する場合は以下を指定します (任意)
- Azure AI Search アカウントのエンドポイント
- Azure AI Search アカウントのクエリキー
- Azure AI Search アカウントでのインデックスの名前
- Azure AI Search にてセマンティック検索を使用するかどうか(trueの場合は使用する)
- Azure AI Search にてベクトル検索を使用する場合、ベクトルフィールドの名前(空白の場合はベクトル検索を行わない)

> 参考: [ポータルで Search サービスを作成する - Azure AI Search | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/search/search-create-service-portal)  

もし回答生成の情報源として Bing Search API ([Bing Web Search API](https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview), [Bing News Search API](https://learn.microsoft.com/en-us/bing/search-apis/bing-news-search/overview)) を使用する場合は以下を指定します (任意)
- Bing Search リソースの API キー

> 参考: [Create Bing Search Services Resource - Bing Search Services | Microsoft Learn](https://learn.microsoft.com/ja-jp/bing/search-apis/bing-web-search/create-bing-search-service-resource)

必要な情報を入力したら、[確認と作成]ボタンをクリックします。

![デプロイの確認をする](.images/deploy-2.jpg)
[作成]ボタンをクリックして、デプロイを開始します。デプロイを開始すると、以下の Azure サービスのリソースのデプロイが行われます。
- Azure Web Apps (Web アプリケーションの稼働)
- Azure App Service Plan (上記　Azure Web Apps アプリのホスト)
- Azure Application Insights (Web アプリケーションの監視とログ管理)
- Azure Cosmos DB (会話履歴の管理)

今回デプロイされる構成図は以下の通りです (Azure AI Search と Bing Search API は既存のリソースを使用)
![構成図](.images/architecture.jpg)

### デプロイした Web アプリケーションの利用
Azure Web Apps へデプロイした Web アプリケーションへアクセスするために、デプロイ先の Azure リソースグループのページを表示し、デプロイした Azure Web Apps アプリの名前をクリックします。
![Webアプリへアクセス](.images/use-web-app-1.jpg)

Azure Web Apps アプリのページが表示されたら、画面上部の[参照]をクリックします。
![Webアプリへアクセス](.images/use-web-app-2.jpg)

デプロイしたチャットアプリが表示されます。  
デプロイ完了からアクセスまでが早すぎる場合、アプリケーションのアクティベーションが完了してなく、既定の Azure Web Apps ページが表示される場合があります。その場合はしばらく待ってから Web アプリケーションへアクセスしてください。
![Webアプリへアクセス](.images/use-web-app-3.jpg)

### デプロイした Web アプリケーションを認証で保護する
Azure Web Apps の Easy Auth 機能を使うことで、デプロイした Web アプリケーションに対して、ユーザ認証されたユーザのみがアクセス可能とさせることができます。今回は Microsoft Entra での認証を設定する方法を説明します。デプロイした Azure Web Apps リソースのページを表示して、サイドメニューの[認証]をクリックし、表示されたページの[ID プロバイダーを追加]をクリックします。
![認証設定](.images/set-auth-1.jpg)

[ID プロバイダー]に ```Microsoft``` を選択し、[アプリの登録]にはアプリの新規登録が可能であれば既定で入力されている値を使用、新規登録ができないのであれば、事前に Microsoft Entra でアプリ登録したものを選択してください。そして、[追加]ボタンをクリックします。認証設定の反映には数分かかることがあります。

> 参考: [Microsoft Entra 認証を構成する - Azure App Service | Microsoft Learn](https://learn.microsoft.com/ja-jp/azure/app-service/configure-authentication-provider-aad?tabs=workforce-configuration)

![認証設定](.images/set-auth-2.jpg)

Web アプリケーションへアクセスすると、Web アプリケーションがログインユーザの一部情報を使用することを許諾するページが表示されます。[承諾]をクリックすると、チャットアプリが使えるようになることが分かります。また、シークレットブラウズ等でアクセスすると、認証を求められることが分かります。
![認証設定](.images/set-auth-3.jpg)