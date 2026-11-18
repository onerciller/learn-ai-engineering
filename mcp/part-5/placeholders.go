package main

import (
	"context"
	"net/http"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// The functions in this file are placeholders for the example.
// In a real project you write email sending and storage yourself.

type mailService struct{}

func (mailService) Send(ctx context.Context, to, subject, body string) (string, error) {
	return "msg-1", nil
}

var mailer mailService

func isDefinitelyNotSent(err error) bool { return false }

type StatusInput struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

func setStatus(ctx context.Context, req *mcp.CallToolRequest, in StatusInput) (*mcp.CallToolResult, any, error) {
	return nil, nil, nil
}

func main() {
	server := mcp.NewServer(&mcp.Implementation{Name: "mail", Version: "v0.5.0"}, nil)
	em := &Emailer{seen: map[string]*record{}}
	mcp.AddTool(server, &mcp.Tool{Name: "send_email", Description: "Sends an email."}, em.Send)
	registerSetStatus(server)
	handler := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server { return server }, nil)
	http.Handle("/mcp", headersMatchBody(handler))
	_ = retry[int]
	_ = http.ListenAndServe(":8080", nil)
}
