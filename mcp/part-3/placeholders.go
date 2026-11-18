package main

import (
	"context"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// The functions in this file are placeholders for the example.
// In a real project you write these for your own data layer and UI.

func deleteProject(ctx context.Context, name string) error { return nil }

func askUser(ctx context.Context, p *mcp.ElicitParams) (*mcp.ElicitResult, error) {
	return &mcp.ElicitResult{Action: "decline"}, nil
}

func listFiles(repo string) []string { return []string{"README.md", "main.go"} }

func scanFile(ctx context.Context, f string) []string { return nil }

var _ = newClient
