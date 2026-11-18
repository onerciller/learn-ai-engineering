package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"

	"github.com/google/jsonschema-go/jsonschema"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Step 1: The input and the confirmation schema.
type DeleteInput struct {
	Project string `json:"project" jsonschema:"name of the project to delete"`
}

var confirmSchema = &jsonschema.Schema{
	Type: "object",
	Properties: map[string]*jsonschema.Schema{
		"confirm": {Type: "boolean", Description: "Yes, delete it"},
	},
	Required: []string{"confirm"},
}

// Step 2: Round 1: send the question back, delete nothing.
func askToConfirm(project string) *mcp.CallToolResult {
	return &mcp.CallToolResult{
		InputRequests: mcp.InputRequestMap{
			"confirm": &mcp.ElicitParams{
				Message:         fmt.Sprintf("Delete project %q?", project),
				RequestedSchema: confirmSchema,
			},
		},
		RequestState: "step=confirm",
	}
}

// Step 3: The tool: ask if there's no answer, otherwise go to round 2.
func deleteProjectTool(
	ctx context.Context, req *mcp.CallToolRequest, in DeleteInput,
) (*mcp.CallToolResult, any, error) {
	resp, answered := req.Params.InputResponses["confirm"]
	if !answered {
		return askToConfirm(in.Project), nil, nil // round 1
	}
	return applyAnswer(ctx, in.Project, resp) // round 2
}

func text(s string) *mcp.CallToolResult {
	return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: s}}}
}

// Step 4: Round 2: check the answer, delete only if confirmed.
func applyAnswer(
	ctx context.Context, project string, resp any,
) (*mcp.CallToolResult, any, error) {
	answer, ok := resp.(*mcp.ElicitResult)
	if !ok || answer == nil {
		return nil, nil, fmt.Errorf("unexpected confirmation answer")
	}
	if answer.Action != "accept" || answer.Content["confirm"] != true {
		return text("Nothing was deleted."), nil, nil
	}
	// In a real project, check the user's permission again here.
	if err := deleteProject(ctx, project); err != nil {
		return nil, nil, err
	}
	return text(project + " was deleted."), nil, nil
}

// Step 5: The app side: show the question to the user.
func newClient() *mcp.Client {
	return mcp.NewClient(
		&mcp.Implementation{Name: "my-app", Version: "v0.1.0"},
		&mcp.ClientOptions{ElicitationHandler: askUserHandler},
	)
}

func askUserHandler(
	ctx context.Context, req *mcp.ElicitRequest,
) (*mcp.ElicitResult, error) {
	// Your UI returns accept, decline, or cancel.
	return askUser(ctx, req.Params)
}

// Step 6: Input and output for the long job.
type ScanInput struct {
	Repo string `json:"repo" jsonschema:"repository to scan"`
}

type ScanOutput struct {
	Findings []string `json:"findings"`
}

// Step 7: Scan files, report progress, respect cancellation.
func scanRepo(
	ctx context.Context, req *mcp.CallToolRequest, in ScanInput,
) (*mcp.CallToolResult, ScanOutput, error) {
	files := listFiles(in.Repo)
	token := req.Params.GetProgressToken() // nil if the client didn't ask for progress
	out := ScanOutput{Findings: []string{}}
	for i, f := range files {
		if err := ctx.Err(); err != nil { // cancelled or disconnected
			return nil, ScanOutput{}, err
		}
		out.Findings = append(out.Findings, scanFile(ctx, f)...)
		if token != nil {
			reportProgress(ctx, req, token, i+1, len(files), f)
		}
	}
	return nil, out, nil
}

// Step 8: The progress notification.
func reportProgress(
	ctx context.Context, req *mcp.CallToolRequest,
	token any, done, total int, file string,
) {
	req.Session.NotifyProgress(ctx, &mcp.ProgressNotificationParams{
		ProgressToken: token,
		Progress:      float64(done), // must go up every time
		Total:         float64(total),
		Message:       file + " being scanned",
	})
}

// Step 9: Logs go to stderr; stdout belongs to the MCP conversation.
var logger = slog.New(slog.NewJSONHandler(os.Stderr, nil))

func main() {
	server := mcp.NewServer(&mcp.Implementation{Name: "projects", Version: "v0.3.0"}, nil)
	mcp.AddTool(server, &mcp.Tool{Name: "delete_project"}, deleteProjectTool)
	mcp.AddTool(server, &mcp.Tool{Name: "scan_repo"}, scanRepo)
	logger.Info("server started")
	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		logger.Error("server stopped", "err", err)
	}
}
