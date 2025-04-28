package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/spiffe/go-spiffe/v2/spiffeid"
	"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
	"github.com/spiffe/go-spiffe/v2/workloadapi"
)

const (
	serverAddress = "localhost:8443"
	socketPath    = "unix:///tmp/agent.sock" // SPIREエージェントのソケットパス
)

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

// サーバーを実行する関数
func runServer() {
	// SPIREワークロードAPIに接続
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	source, err := workloadapi.NewX509Source(ctx, workloadapi.WithClientOptions(workloadapi.WithAddr(socketPath)))
	if err != nil {
		log.Fatalf("Failed to connect to workload API: %v", err)
	}
	defer source.Close()

	// サーバーのSPIFFE IDを取得
	svid, err := source.GetX509SVID()
	if err != nil {
		log.Fatalf("Failed to get X.509-SVID: %v", err)
	}
	log.Printf("Server SPIFFE ID: %s", svid.ID)

	// mTLS用のTLS設定を作成
	tlsConfig := tlsconfig.MTLSServerConfig(source, source, tlsconfig.AuthorizeAny())
	server := &http.Server{
		Addr:      serverAddress,
		TLSConfig: tlsConfig,
		Handler:   http.HandlerFunc(serverHandler),
	}

	// サーバーを起動
	listener, err := net.Listen("tcp", serverAddress)
	if err != nil {
		log.Fatalf("Failed to create listener: %v", err)
	}

	log.Printf("Server started: https://%s", serverAddress)
	err = server.ServeTLS(listener, "", "")
	if err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// HTTPリクエストを処理するハンドラー
func serverHandler(w http.ResponseWriter, r *http.Request) {
	// クライアントのSPIFFE IDを取得
	clientID := ""
	if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
		cert := r.TLS.PeerCertificates[0]
		if len(cert.URIs) > 0 {
			clientID = cert.URIs[0].String()
		}
	}

	log.Printf("Received request from client: %s", clientID)
	fmt.Fprintf(w, "Hello, %s! The current time is %s.", clientID, time.Now().Format(time.RFC3339))
}

// クライアントを実行する関数
func runClient() {
	// SPIREワークロードAPIに接続
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	source, err := workloadapi.NewX509Source(ctx, workloadapi.WithClientOptions(workloadapi.WithAddr(socketPath)))
	if err != nil {
		log.Fatalf("Failed to connect to workload API: %v", err)
	}
	defer source.Close()

	// クライアントのSPIFFE IDを取得
	svid, err := source.GetX509SVID()
	if err != nil {
		log.Fatalf("Failed to get X.509-SVID: %v", err)
	}
	log.Printf("Client SPIFFE ID: %s", svid.ID)

	// サーバーのSPIFFE IDを指定
	serverID, err := spiffeid.FromString("spiffe://example.org/server")
	if err != nil {
		log.Fatalf("Failed to parse server ID: %v", err)
	}

	// mTLS用のTLS設定を作成
	tlsConfig := tlsconfig.MTLSClientConfig(source, source, tlsconfig.AuthorizeID(serverID))
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
		},
	}

	// サーバーにリクエストを送信
	resp, err := client.Get(fmt.Sprintf("https://%s", serverAddress))
	if err != nil {
		log.Fatalf("Request error: %v", err)
	}
	defer resp.Body.Close()

	// レスポンスを読み取り
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Response read error: %v", err)
	}

	log.Printf("Response from server: %s", body)
}

// TLS証明書からSPIFFE IDを抽出する関数
func extractSPIFFEID(cert *x509.Certificate) (string, error) {
	if cert == nil {
		return "", fmt.Errorf("certificate is nil")
	}

	if len(cert.URIs) == 0 {
		return "", fmt.Errorf("certificate has no URIs")
	}

	return cert.URIs[0].String(), nil
}

// TLS接続からピアのSPIFFE IDを抽出する関数
func getPeerSPIFFEID(conn *tls.Conn) (string, error) {
	// TLS状態を確認
	state := conn.ConnectionState()
	if len(state.PeerCertificates) == 0 {
		return "", fmt.Errorf("no peer certificates")
	}

	// 最初の証明書からSPIFFE IDを抽出
	return extractSPIFFEID(state.PeerCertificates[0])
}
