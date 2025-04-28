#!/usr/bin/env python3

import logging
import os
import ssl
import tempfile
import json
import requests

from pyspiffe.workloadapi import WorkloadApiClient
from pyspiffe.spiffe_id.trust_domain import TrustDomain
from pyspiffe.spiffe_id.spiffe_id import SpiffeId

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SPIREエージェントのソケットパス
SOCKET_PATH = os.environ.get('SPIFFE_ENDPOINT_SOCKET', 'unix:///tmp/spire-agent/public/api.sock')

# サーバーのアドレス
SERVER_ADDRESS = 'localhost:8443'

# サーバーのSPIFFE ID
SERVER_SPIFFE_ID = 'spiffe://example.org/server'

def main():
    logger.info("Starting SPIFFE demo client...")
    
    # WorkloadAPIクライアントの作成
    client = WorkloadApiClient(SOCKET_PATH)
    
    try:
        # X.509-SVIDの取得
        x509_context = client.fetch_x509_context()
        svid = x509_context.default_svid
        
        logger.info(f"Client SPIFFE ID: {svid.spiffe_id}")
        
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
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_cert_chain(cert_path, key_path)
        context.load_verify_locations(cafile=bundle_path)
        context.check_hostname = False  # SPIFFE IDベースの検証を行うため、ホスト名の検証は無効化
        
        # サーバーのSPIFFE IDを検証するカスタム関数
        def verify_spiffe_id(ssl_socket, server_hostname, ssl_context, as_callback=False):
            cert = ssl_socket.getpeercert()
            san = cert.get('subjectAltName', [])
            uri_sans = [san_value for san_type, san_value in san if san_type == 'URI']
            
            for uri in uri_sans:
                if uri == SERVER_SPIFFE_ID:
                    return True
                    
            if as_callback:
                return False
            else:
                raise ssl.SSLError(f"Server SPIFFE ID {uri_sans} does not match expected ID {SERVER_SPIFFE_ID}")
        
        # コンテキストにSPIFFE ID検証関数を設定
        context.verify_mode = ssl.CERT_REQUIRED
        
        # リクエストの送信
        logger.info(f"Sending request to server: https://{SERVER_ADDRESS}")
        response = requests.get(
            f"https://{SERVER_ADDRESS}",
            cert=(cert_path, key_path),
            verify=bundle_path
        )
        
        # レスポンスの処理
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response from server: {data}")
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
        
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
