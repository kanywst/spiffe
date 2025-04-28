# SPIFFEスタートガイド

このチュートリアルでは、SPIFFEとSPIREの基本的な使い方を説明します。SPIREをインストールし、基本的な設定を行い、サービス間の認証を実装する方法を学びます。

## 前提条件

- Linux、macOS、またはWSL2（Windows Subsystem for Linux 2）
- 管理者権限（sudoアクセス）
- 基本的なコマンドラインの知識

## 目次

- [SPIFFEスタートガイド](#spiffeスタートガイド)
  - [前提条件](#前提条件)
  - [目次](#目次)
  - [1. SPIREのインストール](#1-spireのインストール)
    - [1.1 バイナリのダウンロード](#11-バイナリのダウンロード)
    - [1.2 インストールの確認](#12-インストールの確認)
  - [2. SPIREサーバーの設定と起動](#2-spireサーバーの設定と起動)
    - [2.1 設定ファイルの作成](#21-設定ファイルの作成)
    - [2.2 データディレクトリの作成](#22-データディレクトリの作成)
    - [2.3 SPIREサーバーの起動](#23-spireサーバーの起動)
  - [3. SPIREエージェントの設定と起動](#3-spireエージェントの設定と起動)
    - [3.1 Join Tokenの生成](#31-join-tokenの生成)
    - [3.2 設定ファイルの作成](#32-設定ファイルの作成)
    - [3.3 SPIREエージェントの起動](#33-spireエージェントの起動)
  - [4. SPIFFE IDの登録](#4-spiffe-idの登録)
    - [4.1 エントリの作成](#41-エントリの作成)
    - [4.2 エントリの確認](#42-エントリの確認)
  - [5. SVIDの取得と検証](#5-svidの取得と検証)
    - [5.1 X.509-SVIDの取得](#51-x509-svidの取得)
    - [5.2 JWT-SVIDの取得](#52-jwt-svidの取得)
  - [6. クリーンアップ](#6-クリーンアップ)
  - [7. 次のステップ](#7-次のステップ)

## 1. SPIREのインストール

### 1.1 バイナリのダウンロード

SPIREの最新バージョンをダウンロードし、インストールします。

```bash
# 最新バージョンを取得
SPIRE_VERSION=$(curl -s https://api.github.com/repos/spiffe/spire/releases/latest | grep "tag_name" | cut -d '"' -f 4)

# OSとアーキテクチャに応じたバイナリをダウンロード
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH="amd64"
elif [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
fi

# ダウンロードとインストール
curl -LO "https://github.com/spiffe/spire/releases/download/${SPIRE_VERSION}/spire-${SPIRE_VERSION}-${OS}-${ARCH}.tar.gz"
tar -xzf "spire-${SPIRE_VERSION}-${OS}-${ARCH}.tar.gz"
cd "spire-${SPIRE_VERSION}"

# バイナリをシステムパスに配置
sudo cp -r bin/* /usr/local/bin/
```

### 1.2 インストールの確認

インストールが成功したことを確認します。

```bash
spire-server version
spire-agent version
```

以下のような出力が表示されれば、インストールは成功です：

```
SPIRE Server v1.6.3
SPIRE Agent v1.6.3
```

## 2. SPIREサーバーの設定と起動

### 2.1 設定ファイルの作成

SPIREサーバーの設定ファイルを作成します。

```bash
mkdir -p ~/spire-tutorial/conf
cat > ~/spire-tutorial/conf/server.conf << EOF
server {
    bind_address = "0.0.0.0"
    bind_port = "8081"
    socket_path = "/tmp/spire-server/private/api.sock"
    trust_domain = "example.org"
    data_dir = "/tmp/spire-server/data"
    log_level = "DEBUG"
    default_svid_ttl = "1h"
    ca_subject = {
        country = ["JP"],
        organization = ["SPIFFE"],
        common_name = "",
    }
}

plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "sqlite3"
            connection_string = "/tmp/spire-server/data/datastore.sqlite3"
        }
    }

    KeyManager "disk" {
        plugin_data {
            keys_path = "/tmp/spire-server/data/keys.json"
        }
    }

    NodeAttestor "join_token" {
        plugin_data {
        }
    }
}
EOF
```

### 2.2 データディレクトリの作成

SPIREサーバーのデータディレクトリを作成します。

```bash
mkdir -p /tmp/spire-server/data
mkdir -p /tmp/spire-server/private
```

### 2.3 SPIREサーバーの起動

SPIREサーバーを起動します。

```bash
spire-server run -config ~/spire-tutorial/conf/server.conf
```

別のターミナルを開いて、次のステップに進みます。

## 3. SPIREエージェントの設定と起動

### 3.1 Join Tokenの生成

SPIREエージェントがSPIREサーバーに接続するためのJoin Tokenを生成します。

```bash
spire-server token generate -spiffeID spiffe://example.org/agent
```

出力されたトークンをメモしておきます。例：

```
Token: 8d87d1f0-d74c-4137-a5b8-7a8e91e39f25
```

### 3.2 設定ファイルの作成

SPIREエージェントの設定ファイルを作成します。

```bash
mkdir -p ~/spire-tutorial/conf
cat > ~/spire-tutorial/conf/agent.conf << EOF
agent {
    data_dir = "/tmp/spire-agent/data"
    log_level = "DEBUG"
    server_address = "127.0.0.1"
    server_port = "8081"
    socket_path = "/tmp/spire-agent/public/api.sock"
    trust_bundle_path = "/tmp/spire-agent/bootstrap/bootstrap.crt"
    trust_domain = "example.org"
}

plugins {
    NodeAttestor "join_token" {
        plugin_data {
        }
    }

    KeyManager "memory" {
        plugin_data {
        }
    }

    WorkloadAttestor "unix" {
        plugin_data {
        }
    }
}
EOF
```

### 3.3 SPIREエージェントの起動

SPIREエージェントのディレクトリを作成し、サーバーの証明書をフェッチしてから、エージェントを起動します。

```bash
# ディレクトリの作成
mkdir -p /tmp/spire-agent/data
mkdir -p /tmp/spire-agent/public
mkdir -p /tmp/spire-agent/bootstrap

# サーバー証明書のフェッチ
spire-server bundle show > /tmp/spire-agent/bootstrap/bootstrap.crt

# エージェントの起動（先ほど生成したトークンを使用）
spire-agent run -config ~/spire-tutorial/conf/agent.conf -joinToken YOUR_TOKEN_HERE
```

`YOUR_TOKEN_HERE`を、先ほど生成したトークンに置き換えてください。

## 4. SPIFFE IDの登録

### 4.1 エントリの作成

ワークロード（サービス）のSPIFFE IDを登録します。

```bash
# 現在のユーザーのUIDを取得
UNIX_USER=$(id -u)

# ワークロードエントリの作成
spire-server entry create \
    -parentID spiffe://example.org/agent \
    -spiffeID spiffe://example.org/myservice \
    -selector unix:uid:${UNIX_USER}
```

### 4.2 エントリの確認

登録したエントリを確認します。

```bash
spire-server entry show
```

以下のような出力が表示されます：

```
Found 1 entry
Entry ID      : 8f2c8293-d6e8-4357-9c83-9a7b3b5e6a87
SPIFFE ID     : spiffe://example.org/myservice
Parent ID     : spiffe://example.org/agent
Revision      : 0
TTL           : default
Selectors     : unix:uid:1000
```

## 5. SVIDの取得と検証

### 5.1 X.509-SVIDの取得

ワークロードAPIを使用して、X.509-SVIDを取得します。

```bash
spire-agent api fetch x509
```

以下のような出力が表示されます：

```
Received 1 svid after 0.01 seconds

SPIFFE ID:		spiffe://example.org/myservice
SVID Valid After:	2023-08-28 12:34:56 +0000 UTC
SVID Valid Until:	2023-08-28 13:34:56 +0000 UTC
CA #1 Valid After:	2023-08-28 12:00:00 +0000 UTC
CA #1 Valid Until:	2023-08-29 12:00:00 +0000 UTC
```

### 5.2 JWT-SVIDの取得

ワークロードAPIを使用して、JWT-SVIDを取得します。

```bash
spire-agent api fetch jwt -audience myaudience
```

以下のような出力が表示されます：

```
Received 1 svid after 0.01 seconds

SPIFFE ID		: spiffe://example.org/myservice
Audience		: myaudience
Expiry			: 2023-08-28 13:34:56 +0000 UTC
JWT Token		: eyJhbGciOiJSUzI1NiIsImtpZCI6IjIzNDU2Nzg5MCIsInR5cCI6IkpXVCJ9...
```

## 6. クリーンアップ

チュートリアルが終了したら、SPIREサーバーとエージェントを停止し、一時ファイルを削除します。

```bash
# SPIREサーバーとエージェントを停止（Ctrl+Cを使用）

# 一時ファイルの削除
rm -rf /tmp/spire-server
rm -rf /tmp/spire-agent
rm -rf ~/spire-tutorial
```

## 7. 次のステップ

このチュートリアルでは、SPIFFEとSPIREの基本的な使い方を学びました。次のステップとして、以下のトピックを探索することをお勧めします：

- [異なるNodeAttestorの使用](node-attestation.md)
- [Kubernetesでのデプロイ](kubernetes-deployment.md)
- [フェデレーションの設定](federation-setup.md)
- [実際のアプリケーションへの統合](application-integration.md)
