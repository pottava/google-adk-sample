# Google ADK サンプル

## Python 仮想環境

```bash
python -m venv .venv
source .venv/bin/activate
```

## ライブラリのインストール

```bash
pip install --upgrade --quiet google-adk google-genai google-cloud-discoveryengine
```

## Google Custom Search API の利用準備

Google Cloud のプロジェクト内に Custom Search のための API キーを作成します。  
https://console.cloud.google.com/apis/credentials

```bash
export datetime=$( date +"%Y%m%d%H%M" )
gcloud services api-keys create --key-id "custom-search-api-${datetime}" --display-name "A key for Google Custom Search JSON API" --api-target "service=customsearch.googleapis.com"
```

応答の中の `keyString` の値を `GOOGLE_API_KEY` の値として設定してください。

```bash
export GOOGLE_API_KEY=
```

Custom Search を行うため、以下の URL から独自の検索エンジンを作成します。  
https://programmablesearchengine.google.com/controlpanel/all

Custom Search Engine ID を `GOOGLE_CSE_ID` の値として設定してください。

```bash
export GOOGLE_CSE_ID=
```

## Vertex AI Search のための環境変数

予め作成している Vertex AI Search のデータストア ID を `VAIS_DATA_STORE_ID` の値として設定してください。

```bash
export VAIS_DATA_STORE_ID=
```

## Google Cloud 認証情報の設定

```bash
mkdir -p $HOME/.config/gcloud/
gcloud auth application-default login --quiet
```

/tmp 以下などに鍵が作成された場合は移動させましょう。

```bash
mv /tmp/*/application_default_credentials.json $HOME/.config/gcloud/ > /dev/null 2>&1
cat ${GOOGLE_APPLICATION_CREDENTIALS} | jq .
```

認証のための環境変数を設定します。

```bash
export GOOGLE_GENAI_USE_VERTEXAI=True
export GOOGLE_CLOUD_PROJECT=$( gcloud config get-value project )
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/application_default_credentials.json
```

## 各 API の挙動確認

```bash
python tools.py "Vertex AI Search 検索ワード" "Google 検索ワード"
```
