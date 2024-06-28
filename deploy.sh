#!/bin/bash -e

# デプロイ設定
RETION='japaneast'       # Azure App Service リソースのリージョン
RESOURCE_GROUP=""        # リソースグループの名前
APP_SERVICE_PLAN_NAME="" # Azure App Service プランの名前
APP_SERVICE_NAME=""      # Azure App Service の名前

# アプリケーションをデプロイする
az webapp up \
    --location $RETION \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN_NAME \
    --name $APP_SERVICE_NAME \
    --runtime 'PYTHON:3.11'