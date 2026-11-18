//go:build integration

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"io"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestMCPWithSimulatedModel(t *testing.T) {
	binary := os.Getenv("NOTES_SERVER_BIN")
	if binary == "" {
		t.Fatal("set NOTES_SERVER_BIN to the compiled MCP Part 1 server")
	}
	cases := []struct {
		name, query string
		wantCalls   int
	}{
		{name: "matched note", query: "tools", wantCalls: 2},
		{name: "no matches", query: "zz-no-matching-note", wantCalls: 1},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			cmd := exec.Command(binary)
			cmd.Env = []string{}
			client := mcp.NewClient(&mcp.Implementation{Name: "test-notes-app", Version: "1"}, nil)
			session, err := client.Connect(ctx, &mcp.CommandTransport{Command: cmd}, nil)
			if err != nil {
				t.Fatal(err)
			}
			defer func() {
				if err := session.Close(); err != nil {
					t.Error(err)
				}
			}()
			calls := 0
			httpClient := &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
				calls++
				var body map[string]any
				if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
					t.Fatal(err)
				}
				var output string
				if calls == 1 {
					tools := body["tools"].([]any)
					tool := tools[0].(map[string]any)
					if tool["name"] != "search_notes" || tool["parameters"] == nil {
						t.Fatal("missing real MCP schema")
					}
					args, err := json.Marshal(map[string]string{"query": tc.query})
					if err != nil {
						t.Fatal(err)
					}
					item, err := json.Marshal(map[string]any{"type": "function_call", "name": "search_notes", "call_id": "call-1", "arguments": string(args)})
					if err != nil {
						t.Fatal(err)
					}
					output = `{"status":"completed","output":[{"type":"reasoning","id":"r1"},` + string(item) + `]}`
				} else {
					input := body["input"].([]any)
					last := input[len(input)-1].(map[string]any)
					if body["tool_choice"] != "none" || last["call_id"] != "call-1" || !strings.Contains(last["output"].(string), "MCP tools offer actions") {
						t.Fatal("continuation must contain matching call ID, real search output, and disabled tools")
					}
					if input[1].(map[string]any)["type"] != "reasoning" {
						t.Fatal("reasoning item was dropped")
					}
					output = `{"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"MCP tools offer actions with clearly defined input."}]}]}`
				}
				return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(output))}, nil
			})}
			c := apiClient{Key: "fixture-key", Model: "fixture-model", URL: "https://example.invalid/api/v1/responses", HTTP: httpClient}
			answer, err := answerWithSearch(ctx, c, session, "Find the tools note.")
			if err != nil {
				t.Fatal(err)
			}
			if calls != tc.wantCalls {
				t.Fatalf("model calls=%d", calls)
			}
			if tc.wantCalls == 1 && answer != "No matching notes found." {
				t.Fatal(answer)
			}
			fmt.Println("Verified:", tc.name, "with a real MCP server and simulated model responses")
		})
	}
}
