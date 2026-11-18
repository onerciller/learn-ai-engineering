package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/rand/v2"
	"net/http"
	"sync"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Step 1: Input, output, and the record kept for each key.
type SendEmailInput struct {
	IdempotencyKey string `json:"idempotency_key" jsonschema:"unique key for this email"`
	To             string `json:"to"`
	Subject        string `json:"subject"`
	Body           string `json:"body"`
}

type SendEmailOutput struct {
	MessageID string `json:"message_id"`
}

type record struct {
	state string // "sending", "sent", or "unknown"
	out   SendEmailOutput
}

// Step 2: The tool: check the key, send, record the result.
type Emailer struct {
	mu   sync.Mutex
	seen map[string]*record // in a real project: a database table
}

func (e *Emailer) Send(
	ctx context.Context, req *mcp.CallToolRequest, in SendEmailInput,
) (*mcp.CallToolResult, SendEmailOutput, error) {
	if out, done, err := e.checkKey(in.IdempotencyKey); done {
		return nil, out, err
	}
	id, err := mailer.Send(ctx, in.To, in.Subject, in.Body)
	return e.finish(in.IdempotencyKey, id, err)
}

// Step 3: Have we seen this key before?
var errUnknown = errors.New("previous attempt is unknown; check the sent folder first")

func (e *Emailer) checkKey(key string) (SendEmailOutput, bool, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	r, ok := e.seen[key]
	if !ok {
		e.seen[key] = &record{state: "sending"}
		return SendEmailOutput{}, false, nil
	}
	switch r.state {
	case "sent":
		return r.out, true, nil // already sent: return the first result, don't send again
	case "unknown":
		return SendEmailOutput{}, true, errUnknown
	default:
		return SendEmailOutput{}, true, errors.New("this email is still being sent")
	}
}

// Step 4: Record what we know.
func (e *Emailer) finish(
	key, id string, err error,
) (*mcp.CallToolResult, SendEmailOutput, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	switch {
	case err == nil:
		e.seen[key].state, e.seen[key].out = "sent", SendEmailOutput{MessageID: id}
		return nil, e.seen[key].out, nil
	case isDefinitelyNotSent(err): // rejected before sending: safe to retry
		delete(e.seen, key)
		return nil, SendEmailOutput{}, err
	default: // timeout or lost connection: the email may have gone out
		e.seen[key].state = "unknown"
		return nil, SendEmailOutput{}, fmt.Errorf("result unknown, not retrying: %w", err)
	}
}

// Step 5: For reads: wait a little longer, at random, each time.
func retry[T any](
	ctx context.Context, attempts int, f func(context.Context) (T, error),
) (T, error) {
	var zero T
	base := 200 * time.Millisecond
	for i := 0; i < attempts; i++ {
		v, err := f(ctx)
		if err == nil || i == attempts-1 {
			return v, err
		}
		// Wait a random time up to 200ms, 400ms, 800ms...
		wait := time.Duration(rand.Int64N(int64(base << i)))
		select {
		case <-time.After(wait):
		case <-ctx.Done():
			return zero, ctx.Err()
		}
	}
	return zero, errors.New("attempts must be at least 1")
}

// Step 6: A label is only a claim.
func registerSetStatus(server *mcp.Server) {
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_status",
		Description: "Sets the status of a record.",
		Annotations: &mcp.ToolAnnotations{IdempotentHint: true}, // a claim, not proof
	}, setStatus)
}

// Step 7: Read at most 4 MB of the body and put it back for the next layer.
func readLimited(w http.ResponseWriter, r *http.Request) ([]byte, bool) {
	body, err := io.ReadAll(io.LimitReader(r.Body, (4<<20)+1))
	if err != nil {
		http.Error(w, "could not read body", http.StatusBadRequest)
		return nil, false
	}
	if len(body) > 4<<20 {
		http.Error(w, "request too large", http.StatusRequestEntityTooLarge)
		return nil, false
	}
	r.Body = io.NopCloser(bytes.NewReader(body))
	return body, true
}

// Step 8: Does the label on the envelope match the letter inside?
type rpcMessage struct {
	Method string `json:"method"`
	Params struct {
		Name string `json:"name"`
	} `json:"params"`
}

func checkHeaders(r *http.Request, msg rpcMessage) error {
	if h := r.Header.Get("Mcp-Method"); h != "" && h != msg.Method {
		return errors.New("Mcp-Method header does not match the body")
	}
	name := r.Header.Get("Mcp-Name")
	if name != "" && msg.Method == "tools/call" && name != msg.Params.Name {
		return errors.New("Mcp-Name header does not match the body")
	}
	return nil
}

// Step 9: Combine everything in one middleware.
func headersMatchBody(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, ok := readLimited(w, r)
		if !ok {
			return
		}
		var msg rpcMessage
		if err := json.Unmarshal(body, &msg); err != nil {
			http.Error(w, "invalid JSON-RPC message", http.StatusBadRequest)
			return
		}
		if err := checkHeaders(r, msg); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		next.ServeHTTP(w, r)
	})
}
