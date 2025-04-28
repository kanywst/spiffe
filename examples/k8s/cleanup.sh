#!/bin/bash

# エラー時に停止するように設定
set -e

echo "=== SPIFFEサンプルアプリケーションのクリーンアップを行います ==="

# kindがインストールされているか確認
if ! command -v kind &> /dev/null; then
    echo "kindがインストールされていません。"
    exit 1
fi

echo "=== サンプルアプリケーションを削除しています ==="
kubectl delete -f spiffe-demo.yaml || true

echo "=== SPIREエージェントを削除しています ==="
kubectl delete -f spire-agent.yaml || true

echo "=== SPIREサーバーを削除しています ==="
kubectl delete -f spire-server.yaml || true

echo "=== kindクラスターを削除しています ==="
kind delete cluster --name spiffe-demo

echo "=== 一時ファイルを削除しています ==="
rm -f kind-config.yaml || true

echo "=== クリーンアップが完了しました ==="
