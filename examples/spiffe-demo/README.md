# SPIFFE認証サンプルアプリケーション

このサンプルアプリケーションは、SPIFFEを使用したサービス間認証の基本的な実装を示しています。サーバーとクライアントの両方のコンポーネントが含まれており、SPIREを使用してX.509-SVIDベースの相互TLS（mTLS）認証を実装しています。

## 前提条件

- Go 1.20以上
- 実行中のSPIREサーバーとエージェント
- SPIREエージェントのUNIXソケット（デフォルトでは`/tmp/agent.sock`）

## セットアップ

### 1. SPIREのインストールと設定

SPIREをインストールして設定する方法については、[SPIREのドキュメント](https://spiffe.io/docs/latest/try/getting-started-linux-macos-x/)を参照してください。

以下は、基本的なSPIREのセットアップ手順です：

```bash
# SPIREサーバーを起動
spire-server run -config /path/to/server/config.conf &

# SPIREエージェントを起動
spire-agent run -config /path/to/agent/config.conf &

# エントリを登録
spire-server entry create \
    -parentID spiffe://example.org/spire/agent/join_token/abcdef \
    -spiffeID spiffe://example.org/server \
    -selector unix:user:server

spire-server entry create \
    -parentID spiffe://example.org/spire/agent/join_token/abcdef \
    -spiffeID spiffe://example.org/client \
    -selector unix:user:client
```

### 2. サンプルアプリケーションのビルド

```bash
go build -o spiffe-demo
```

## 使用方法

### サーバーの実行

```bash
# サーバーユーザーとして実行
sudo -u server ./spiffe-demo server
```

サーバーは、SPIREエージェントからX.509-SVIDを取得し、ポート8443でHTTPSサーバーを起動します。

### クライアントの実行

```bash
# クライアントユーザーとして実行
sudo -u client ./spiffe-demo client
```

クライアントは、SPIREエージェントからX.509-SVIDを取得し、サーバーに接続してリクエストを送信します。

## コードの説明

### メイン関数

`main.go`のメイン関数は、コマンドライン引数に基づいてサーバーまたはクライアントモードで実行します。

```go
func main() {
    if len(os.Args) != 2 {
        log.Fatalf("Usage: %s [server|client]", os.Args[0])
    }

    switch os.Args[1] {
    case "server":
        runServer()
    case "client":
        runClient()
    default:
        log.Fatalf("Unknown mode: %s", os.Args[1])
    }
}
```

### サーバー実装

サーバーは以下の手順で実装されています：

1. SPIREワークロードAPIに接続してX.509-SVIDを取得
2. mTLS用のTLS設定を作成
3. HTTPSサーバーを起動
4. クライアントからのリクエストを処理

### クライアント実装

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

## 参考リソース

- [SPIFFE公式ドキュメント](https://spiffe.io/docs/)
- [go-spiffe ライブラリ](https://github.com/spiffe/go-spiffe)
- [SPIRE ドキュメント](https://spiffe.io/docs/latest/spire-about/)
