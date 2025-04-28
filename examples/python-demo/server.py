#!/usr/bin/env python3

import logging
import os
import ssl
import tempfile
from datetime import datetime
from flask import Flask, jsonify, request

from pyspiffe.workloadapi import WorkloadApiClient
from pyspiffe.spiffe_id.trust_domain import TrustDomain
from pyspiffe.spiffe_id.spiffe_id import SpiffeId

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SPIREエージェントのソケットパス
SOCKET_PATH = os.environ.get('SPIFFE_ENDPOINT_SOCKET', 'unix:///tmp/spire-agent/public/api.sock')

# サーバーのポート
PORT = 8443

# Flaskアプリケーションの作成
app = Flask(__name__)

# クライアントのSPIFFE IDを取得する関数
def get_client_spiffe_id(environ):
    if 'SSL_CLIENT_CERT' in environ:
        # クライアント証明書からSPIFFE IDを抽出する処理
        # 実際の実装では、X.509証明書からURI SANを抽出する必要があります
        return environ.get('SSL_CLIENT_SPIFFE_ID', 'Unknown')
    return 'No client certificate'

# ルートエンドポイント
@app.route('/')
def hello():
    client_id = get_client_spiffe_id(request.environ)
    logger.info(f"Received request from client: {client_id}")
    
    return jsonify({
        'message': f'Hello, {client_id}!',
        'time': datetime.now().isoformat()
    })

def main():
    logger.info("Starting SPIFFE demo server...")
    
    # WorkloadAPIクライアントの作成
    client = WorkloadApiClient(SOCKET_PATH)
    
    try:
        # X.509-SVIDの取得
        x509_context = client.fetch_x509_context()
        svid = x509_context.default_svid
        
        logger.info(f"Server SPIFFE ID: {svid.spiffe_id}")
        
        # 一時ファイルに証明書と秘密鍵を書き込む
        with tempfile.NamedTemporaryFile(delete=False) as cert_file:
            cert_file.write(svid.cert.encode())
            cert_path = cert_file.name
            
        with tempfile.NamedTemporaryFile(delete=False) as key_file:
            key_file.write(svid.private_key.encode())
            key_path = key_file.name
            
        with tempfile.NamedTemporaryFile(delete=False) as bundle_file:
            bundle_file.write(x509_context.trust_bundles[0].trust_bundle.encode())
            bundle_path = bundle_file.name
        
        # SSLコンテキストの設定
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_path, key_path)
        context.load_verify_locations(cafile=bundle_path)
        context.verify_mode = ssl.CERT_REQUIRED
        
        # サーバーの起動
        logger.info(f"Server started: https://localhost:{PORT}")
        app.run(host='0.0.0.0', port=PORT, ssl_context=context)
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # 一時ファイルの削除
        for path in [cert_path, key_path, bundle_path]:
            if os.path.exists(path):
                os.unlink(path)
        
        # WorkloadAPIクライアントのクローズ
        client.close()

if __name__ == '__main__':
    main()
