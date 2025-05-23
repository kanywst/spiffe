# Python SPIFFEサンプルアプリケーション

このディレクトリには、PythonでSPIFFE認証を実装したサンプルアプリケーションが含まれています。このサンプルでは、SPIREを使用してX.509-SVIDベースの相互TLS（mTLS）認証を実装しています。

## 前提条件

- Python 3.8以上
- 実行中のSPIREサーバーとエージェント
- SPIREエージェントのUNIXソケット（デフォルトでは`/tmp/spire-agent/public/api.sock`）

## インストール

必要なパッケージをインストールします：

```bash
pip install -r requirements.txt
```

## 使用方法

### サーバーの実行

```bash
python server.py
```

サーバーは、SPIREエージェントからX.509-SVIDを取得し、ポート8443でHTTPSサーバーを起動します。

### クライアントの実行

```bash
python client.py
```

クライアントは、SPIREエージェントからX.509-SVIDを取得し、サーバーに接続してリクエストを送信します。

## コードの説明

### サーバー実装（server.py）

サーバーは以下の手順で実装されています：

1. SPIREワークロードAPIに接続してX.509-SVIDを取得
2. mTLS用のTLS設定を作成
3. HTTPSサーバーを起動
4. クライアントからのリクエストを処理

### クライアント実装（client.py）

クライアントは以下の手順で実装されています：

1. SPIREワークロードAPIに接続してX.509-SVIDを取得
2. サーバーのSPIFFE IDを指定
3. mTLS用のTLS設定を作成
4. サーバーにHTTPSリクエストを送信
5. レスポンスを処理

## SPIFFE IDの検証

このサンプルでは、クライアントはサーバーのSPIFFE IDを検証し、サーバーはクライアントのSPIFFE IDをログに記録します。これにより、両方のサービスが互いに認証できます。

## 注意事項

- このサンプルは教育目的であり、本番環境での使用は推奨されません。
- 実際のデプロイメントでは、適切なエラー処理とセキュリティ対策を実装する必要があります。
- SPIREエージェントのソケットパスは、環境に合わせて調整する必要があります。
