package main

import (
	"context"
	"errors"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// The types and functions in this file are placeholders for the example.
// In a real project you write token checks and permission storage yourself.

type AddInput struct {
	A    int    `json:"a"`
	B    int    `json:"b"`
	Note string `json:"note"`
}

func add(ctx context.Context, req *mcp.CallToolRequest, in AddInput) (*mcp.CallToolResult, any, error) {
	return nil, nil, nil
}

type jwtClaims struct {
	Subject  string
	Audience []string
	Scopes   []string
	Expiry   time.Time
}

func parseAndCheckJWT(ctx context.Context, raw string) (*jwtClaims, error) {
	return nil, errors.New("example: verify the JWT here")
}

type permStore struct{}

func (permStore) Allowed(ctx context.Context, user, action, id string) bool { return false }

var perms permStore

type noteStore struct{}

func (noteStore) Delete(ctx context.Context, id string) error { return nil }

var notes noteStore

var _ = poisonedTool
