# SPIFFEトラブルシューティングガイド

このガイドでは、SPIFFE/SPIREを使用する際に発生する可能性のある一般的な問題とその解決方法について説明します。

## 目次

- [SPIFFEトラブルシューティングガイド](#spiffeトラブルシューティングガイド)
  - [目次](#目次)
  - [1. 一般的な問題](#1-一般的な問題)
    - [1.1 SPIREサーバーが起動しない](#11-spireサーバーが起動しない)
    - [1.2 SPIREエージェントがサーバーに接続できない](#12-spireエージェントがサーバーに接続できない)
    - [1.3 ワークロードがSVIDを取得できない](#13-ワークロードがsvidを取得できない)
    - [1.4 SVIDの検証に失敗する](#14-svidの検証に失敗する)
    - [1.5 パフォーマンスの問題](#15-パフォーマンスの問題)
  - [2. 環境別のトラブルシューティング](#2-環境別のトラブルシューティング)
    - [2.1 Kubernetes環境](#21-kubernetes環境)

## 1. 一般的な問題

### 1.1 SPIREサーバーが起動しない

**症状**:
- SPIREサーバーが起動せず、エラーメッセージが表示される
- プロセスがすぐに終了する

**考えられる原因と解決策**:

1. **設定ファイルの問題**
   - 設定ファイルの構文が正しいことを確認してください
   - 必要なセクションとプラグインがすべて設定されていることを確認してください
   ```bash
   spire-server validate -config /path/to/server.conf
   ```

2. **ポートの競合**
   - 指定したポートが既に使用されていないか確認してください
   ```bash
   netstat -tuln | grep 8081
   ```

3. **データディレクトリのアクセス権限**
   - データディレクトリが存在し、適切なアクセス権限があることを確認してください
   ```bash
   ls -la /path/to/data/dir
   sudo chown -R spire:spire /path/to/data/dir
   ```

4. **データベース接続の問題**
   - データベースが実行中で、接続文字列が正しいことを確認してください
   - データベースユーザーに適切な権限があることを確認してください
   ```bash
   mysql -u username -p -h database.example.org spire
   ```

### 1.2 SPIREエージェントがサーバーに接続できない

**症状**:
- エージェントがサーバーに接続できず、タイムアウトエラーが発生する
- エージェントが認証エラーを報告する

**考えられる原因と解決策**:

1. **ネットワーク接続の問題**
   - サーバーのアドレスとポートが正しいことを確認してください
   - ファイアウォールがSPIREサーバーのポートへのアクセスを許可していることを確認してください
   ```bash
   telnet spire-server.example.org 8081
   ```

2. **トラストバンドルの問題**
   - エージェントのトラストバンドルが正しく設定されていることを確認してください
   - トラストバンドルが最新であることを確認してください
   ```bash
   spire-server bundle show > /path/to/bundle.crt
   ```

3. **ノード認証の問題**
   - エージェントとサーバーのNodeAttestorプラグインが一致していることを確認してください
   - 必要な認証情報（トークン、証明書など）が正しく設定されていることを確認してください
   ```bash
   # Join Tokenの場合
   spire-server token generate -spiffeID spiffe://example.org/agent
   ```

4. **サーバーの可用性**
   - SPIREサーバーが実行中であることを確認してください
   ```bash
   curl -k https://spire-server.example.org:8081/api/health
   ```

### 1.3 ワークロードがSVIDを取得できない

**症状**:
- ワークロードがSVIDを取得できず、エラーメッセージが表示される
- `spire-agent api fetch` コマンドがSVIDを返さない

**考えられる原因と解決策**:

1. **ワークロードエントリの不足**
   - ワークロードのSPIFFE IDが登録されていることを確認してください
   ```bash
   spire-server entry show
   ```

2. **セレクタの不一致**
   - ワークロードエントリのセレクタが、実際のワークロードの属性と一致していることを確認してください
   ```bash
   # UNIXセレクタの場合
   id -u
   id -g
   ```

3. **ソケットのアクセス権限**
   - ワークロードAPIソケットが存在し、適切なアクセス権限があることを確認してください
   ```bash
   ls -la /tmp/spire-agent/public/api.sock
   ```

4. **エージェントの状態**
   - SPIREエージェントが実行中で、サーバーと正常に通信できることを確認してください
   ```bash
   spire-agent healthcheck
   ```

### 1.4 SVIDの検証に失敗する

**症状**:
- サービス間の通信が失敗し、証明書の検証エラーが発生する
- クライアントがサーバーのSVIDを信頼できない

**考えられる原因と解決策**:

1. **トラストバンドルの不一致**
   - クライアントが正しいトラストバンドルを使用していることを確認してください
   ```bash
   spire-agent api fetch -socketPath /tmp/spire-agent/public/api.sock bundle
   ```

2. **SVID有効期限切れ**
   - SVIDが有効期限内であることを確認してください
   ```bash
   spire-agent api fetch -socketPath /tmp/spire-agent/public/api.sock x509
   ```

3. **SPIFFE IDの不一致**
   - クライアントが期待するSPIFFE IDとサーバーのSPIFFE IDが一致していることを確認してください
   ```bash
   openssl x509 -in cert.pem -text -noout | grep URI
   ```

4. **トラストドメインの不一致**
   - クライアントとサーバーが同じトラストドメインを使用しているか、適切にフェデレーションされていることを確認してください
   ```bash
   spire-server bundle show
   ```

### 1.5 パフォーマンスの問題

**症状**:
- SVIDの取得に時間がかかる
- サーバーやエージェントのCPU/メモリ使用率が高い

**考えられる原因と解決策**:

1. **リソース不足**
   - サーバーとエージェントに十分なCPUとメモリリソースが割り当てられていることを確認してください
   ```bash
   top
   free -m
   ```

2. **データベースのパフォーマンス**
   - データベースのパフォーマンスを最適化してください（インデックスの追加、接続プールの調整など）
   ```bash
   mysqltuner
   ```

3. **キャッシュの設定**
   - エージェントのキャッシュ設定を調整してください
   ```hcl
   agent {
       cache_refresh_interval = "1h"
   }
   ```

4. **ログレベル**
   - 本番環境では、ログレベルを`INFO`または`WARN`に設定してください
   ```hcl
   server {
       log_level = "INFO"
   }
   ```

## 2. 環境別のトラブルシューティング

### 2.1 Kubernetes環境

**一般的な問題**:

1. **サービスアカウントトークンの問題**
   - サービスアカウントが存在し、適切な権限があることを確認してください
   ```bash
   kubectl get serviceaccount -n spire spire-agent
   kubectl describe serviceaccount -n spire spire-agent
   ```

2. **RBAC権限の問題**
   - 必要なRBAC権限が設定されていることを確認してください
   ```bash
   kubectl get clusterrole spire-agent-cluster-role
   kubectl get clusterrolebinding
