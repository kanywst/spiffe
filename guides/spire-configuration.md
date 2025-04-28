# SPIREの詳細設定ガイド

このガイドでは、SPIREサーバーとエージェントの詳細な設定方法について説明します。本番環境でSPIREを使用する際の推奨設定やベストプラクティスも紹介します。

## 目次

- [SPIREの詳細設定ガイド](#spireの詳細設定ガイド)
  - [目次](#目次)
  - [1. SPIREサーバーの設定](#1-spireサーバーの設定)
    - [1.1 基本設定](#11-基本設定)
    - [1.2 データストアの設定](#12-データストアの設定)
    - [1.3 鍵管理の設定](#13-鍵管理の設定)
    - [1.4 ノード認証の設定](#14-ノード認証の設定)
    - [1.5 アップストリーム認証局の設定](#15-アップストリーム認証局の設定)
    - [1.6 ヘルスチェックの設定](#16-ヘルスチェックの設定)
    - [1.7 高可用性の設定](#17-高可用性の設定)
  - [2. SPIREエージェントの設定](#2-spireエージェントの設定)
    - [2.1 基本設定](#21-基本設定)
    - [2.2 ノード認証の設定](#22-ノード認証の設定)

## 1. SPIREサーバーの設定

### 1.1 基本設定

SPIREサーバーの基本設定は、`server`セクションで行います。

```hcl
server {
    # サーバーがバインドするアドレス
    bind_address = "0.0.0.0"
    
    # サーバーがリッスンするポート
    bind_port = "8081"
    
    # UNIXソケットのパス
    socket_path = "/tmp/spire-server/private/api.sock"
    
    # トラストドメイン名
    trust_domain = "example.org"
    
    # データディレクトリ
    data_dir = "/var/lib/spire/server"
    
    # ログレベル（DEBUG, INFO, WARN, ERROR）
    log_level = "INFO"
    
    # デフォルトのSVID有効期限（例：1時間）
    default_svid_ttl = "1h"
    
    # CA証明書のサブジェクト
    ca_subject = {
        country = ["JP"],
        organization = ["SPIFFE"],
        common_name = "",
    }
    
    # CA証明書の有効期限（例：24時間）
    ca_ttl = "24h"
}
```

### 1.2 データストアの設定

SPIREサーバーは、登録エントリやノード情報を保存するためのデータストアを必要とします。本番環境では、SQLiteではなくMySQLやPostgreSQLなどの堅牢なデータベースを使用することをお勧めします。

```hcl
plugins {
    DataStore "sql" {
        plugin_data {
            # データベースタイプ（sqlite3, mysql, postgres）
            database_type = "mysql"
            
            # 接続文字列
            connection_string = "username:password@tcp(database.example.org:3306)/spire"
            
            # 最大オープン接続数
            max_open_conns = 10
            
            # 最大アイドル接続数
            max_idle_conns = 5
            
            # 接続の最大ライフタイム
            conn_max_lifetime = "5m"
        }
    }
}
```

### 1.3 鍵管理の設定

SPIREサーバーは、CA鍵を管理するためのKeyManagerプラグインを使用します。本番環境では、ディスク上に鍵を保存するのではなく、HSM（Hardware Security Module）やAWS KMS、HashiCorp Vaultなどの安全な鍵管理サービスを使用することをお勧めします。

```hcl
plugins {
    KeyManager "disk" {
        plugin_data {
            # 鍵を保存するパス
            keys_path = "/var/lib/spire/server/keys.json"
        }
    }
    
    # または、HSMを使用する場合
    KeyManager "pkcs11" {
        plugin_data {
            # HSMのライブラリパス
            library_path = "/usr/lib/softhsm/libsofthsm2.so"
            
            # スロットID
            slot_id = 1
            
            # トークンラベル
            token_label = "SPIRE"
            
            # PINコード
            pin = "1234"
        }
    }
}
```

### 1.4 ノード認証の設定

SPIREサーバーは、ノード（エージェント）を認証するためのNodeAttestorプラグインを使用します。環境に応じて、適切なNodeAttestorを選択してください。

```hcl
plugins {
    # Kubernetesの場合
    NodeAttestor "k8s_sat" {
        plugin_data {
            clusters = {
                "cluster-name" = {
                    service_account_allow_list = ["spire:spire-agent"]
                    audience = ["spire-server"]
                    kube_config_file = "/path/to/kubeconfig"
                }
            }
        }
    }
    
    # AWSの場合
    NodeAttestor "aws_iid" {
        plugin_data {
            access_key_id = "ACCESS_KEY_ID"
            secret_access_key = "SECRET_ACCESS_KEY"
            skip_block_device = false
        }
    }
    
    # GCPの場合
    NodeAttestor "gcp_iit" {
        plugin_data {
            project_id = "PROJECT_ID"
            use_instance_metadata = true
            service_account_file = "/path/to/service-account.json"
        }
    }
    
    # Azure VMの場合
    NodeAttestor "azure_msi" {
        plugin_data {
            tenants = {
                "TENANT_ID" = {
                    resource_id = "https://management.azure.com/"
                }
            }
        }
    }
}
```

### 1.5 アップストリーム認証局の設定

SPIREサーバーは、オプションでアップストリーム認証局（CA）を使用して、SVIDの署名に使用する中間CA証明書を発行できます。これにより、既存のPKIインフラストラクチャとの統合が容易になります。

```hcl
plugins {
    UpstreamAuthority "disk" {
        plugin_data {
            key_file_path = "/path/to/upstream-key.pem"
            cert_file_path = "/path/to/upstream-cert.pem"
        }
    }
    
    # または、Vaultを使用する場合
    UpstreamAuthority "vault" {
        plugin_data {
            vault_addr = "https://vault.example.org:8200"
            vault_token = "VAULT_TOKEN"
            pki_mount_point = "pki"
            ca_cert_path = "/path/to/vault-ca-cert.pem"
        }
    }
    
    # または、AWS Certificate Managerを使用する場合
    UpstreamAuthority "aws_pca" {
        plugin_data {
            region = "us-west-2"
            certificate_authority_arn = "arn:aws:acm-pca:us-west-2:ACCOUNT_ID:certificate-authority/CA_ID"
            signing_algorithm = "SHA256WITHRSA"
        }
    }
}
```

### 1.6 ヘルスチェックの設定

SPIREサーバーは、ヘルスチェックエンドポイントを提供できます。これは、Kubernetes環境でのLivenessProbeやReadinessProbeに役立ちます。

```hcl
health_checks {
    listener_enabled = true
    bind_address = "0.0.0.0"
    bind_port = "8080"
    live_path = "/live"
    ready_path = "/ready"
}
```

### 1.7 高可用性の設定

本番環境では、SPIREサーバーを高可用性（HA）モードで実行することをお勧めします。これには、複数のSPIREサーバーインスタンスと共有データストアが必要です。

```hcl
server {
    # 他の設定...
    
    # CAの署名に使用する鍵のタイプ
    ca_key_type = "rsa-2048"
    
    # CAの署名に使用するアルゴリズム
    ca_signing_algorithm = "RSAPKCS1SHA256"
    
    # ジャーナルの設定
    journal_path = "/var/lib/spire/server/journal.pem"
}

plugins {
    DataStore "sql" {
        plugin_data {
            # 共有データベースの接続文字列
            connection_string = "username:password@tcp(database.example.org:3306)/spire"
        }
    }
}
```

## 2. SPIREエージェントの設定

### 2.1 基本設定

SPIREエージェントの基本設定は、`agent`セクションで行います。

```hcl
agent {
    # データディレクトリ
    data_dir = "/var/lib/spire/agent"
    
    # ログレベル（DEBUG, INFO, WARN, ERROR）
    log_level = "INFO"
    
    # SPIREサーバーのアドレス
    server_address = "spire-server.example.org"
    
    # SPIREサーバーのポート
    server_port = "8081"
    
    # ワークロードAPIのUNIXソケットパス
    socket_path = "/tmp/spire-agent/public/api.sock"
    
    # トラストバンドルのパス
    trust_bundle_path = "/var/lib/spire/agent/bootstrap.crt"
    
    # トラストドメイン名（サーバーと同じ）
    trust_domain = "example.org"
    
    # SVIDの更新頻度
    svid_ttl = "1h"
}
```

### 2.2 ノード認証の設定

SPIREエージェントは、SPIREサーバーに対して自身を認証するためのNodeAttestorプラグインを使用します。サーバー側で設定したNodeAttestorと一致するプラグインを選択する必要があります。

```hcl
plugins {
    # Kubernetesの場合
    NodeAttestor "k8s_sat" {
        plugin_data {
            # Kubernetes Service Account Tokenのパス
            token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        }
    }
    
    # AWSの場合
    NodeAttestor "aws_iid" {
        plugin_data {
            # IMDSv2を使用するかどうか
            use_imdsv2 = true
        }
    }
    
    # GCPの場合
    NodeAttestor "gcp_iit" {
        plugin_data {
