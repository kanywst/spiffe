#!/bin/bash

# エラー時に停止するように設定
set -e

echo "=== SPIFFEサンプルアプリケーション用のkindクラスターをセットアップします ==="

# kindがインストールされているか確認
if ! command -v kind &> /dev/null; then
    echo "kindがインストールされていません。kindをインストールしてください。"
    echo "インストール方法: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# kubectlがインストールされているか確認
if ! command -v kubectl &> /dev/null; then
    echo "kubectlがインストールされていません。kubectlをインストールしてください。"
    echo "インストール方法: https://kubernetes.io/docs/tasks/tools/install-kubectl/"
    exit 1
fi

# kindクラスターの設定ファイルを作成
cat > kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

echo "=== kindクラスターを作成しています ==="
kind create cluster --name spiffe-demo --config kind-config.yaml

echo "=== クラスターの状態を確認しています ==="
kubectl get nodes
kubectl cluster-info

echo "=== SPIREサーバーをデプロイしています ==="
kubectl apply -f spire-server.yaml

echo "=== SPIREサーバーが起動するのを待っています ==="
kubectl -n spire wait --for=condition=Ready pod -l app=spire-server --timeout=120s

echo "=== SPIREエージェントをデプロイしています ==="
kubectl apply -f spire-agent.yaml

echo "=== SPIREエージェントが起動するのを待っています ==="
kubectl -n spire wait --for=condition=Ready pod -l app=spire-agent --timeout=120s

echo "=== サンプルアプリケーションをデプロイしています ==="
kubectl apply -f spiffe-demo.yaml

echo "=== サンプルアプリケーションが起動するのを待っています ==="
kubectl -n spiffe-demo wait --for=condition=Ready pod -l app=spiffe-demo-server --timeout=120s
kubectl -n spiffe-demo wait --for=condition=Ready pod -l app=spiffe-demo-client --timeout=120s

echo "=== サーバーのログを確認しています ==="
kubectl -n spiffe-demo logs -l app=spiffe-demo-server

echo "=== クライアントのログを確認しています ==="
kubectl -n spiffe-demo logs -l app=spiffe-demo-client

echo "=== セットアップが完了しました ==="
echo "以下のコマンドでログを確認できます："
echo "  サーバーログ: kubectl -n spiffe-demo logs -l app=spiffe-demo-server"
echo "  クライアントログ: kubectl -n spiffe-demo logs -l app=spiffe-demo-client"
echo ""
echo "クラスターを削除するには以下のコマンドを実行してください："
echo "  kind delete cluster --name spiffe-demo"
