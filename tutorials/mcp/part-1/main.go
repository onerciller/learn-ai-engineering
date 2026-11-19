// Step 1: The top of the file.
package main

import (
	"context"
	"log"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Step 2: Input and output.
// The SDK builds the JSON Schema from SearchInput.
type SearchInput struct {
	Query string `json:"query" jsonschema:"words to search for in the notes"`
}

type SearchOutput struct {
	Matches []string `json:"matches"`
}

// Step 3: What the tool does.
func searchNotes(
	ctx context.Context,
	req *mcp.CallToolRequest,
	in SearchInput,
) (*mcp.CallToolResult, SearchOutput, error) {
	return nil, SearchOutput{Matches: findNotes(in.Query)}, nil
}

// Step 4: The notes and the search.
func findNotes(query string) []string {
	notes := []string{
		"MCP tools offer actions with clearly defined input.",
		"Resources give the assistant context.",
		"Every tool call needs a permission check.",
	}
	q := strings.ToLower(query)
	matches := make([]string, 0)
	for _, note := range notes {
		if strings.Contains(strings.ToLower(note), q) {
			matches = append(matches, note)
		}
	}
	return matches
}

// Step 5: Register the tool and start the server.
func main() {
	server := mcp.NewServer(
		&mcp.Implementation{Name: "my-notes", Version: "v0.1.0"},
		nil,
	)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "search_notes",
		Description: "Finds notes that contain the query.",
	}, searchNotes)

	// Talk over stdin/stdout until the connection closes.
	err := server.Run(context.Background(), &mcp.StdioTransport{})
	if err != nil {
		log.Fatal(err)
	}
}
