package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"
)

type transportFunc func(*http.Request) (*http.Response, error)

func (f transportFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestAskRejectsEmptyQuestionBeforeNetwork(t *testing.T) {
	client := &http.Client{Transport: transportFunc(func(*http.Request) (*http.Response, error) {
		t.Fatal("empty questions must not reach the network")
		return nil, nil
	})}
	_, err := ask(context.Background(), client, "https://example.invalid/api/v1", "test-key", "test-model", " ")
	if err == nil {
		t.Fatal("expected an error")
	}
}

func TestSendDoesNotExposeErrorBody(t *testing.T) {
	client := &http.Client{Transport: transportFunc(func(*http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 401, Body: io.NopCloser(strings.NewReader("private note and secret"))}, nil
	})}
	_, err := send(context.Background(), client, "https://example.invalid/api/v1", "test-key", []byte("{}"))
	if err == nil || !strings.Contains(err.Error(), "401") || strings.Contains(err.Error(), "private") {
		t.Fatalf("expected status without response body, got %v", err)
	}
}

func TestSendPreservesCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	client := &http.Client{Transport: transportFunc(func(r *http.Request) (*http.Response, error) {
		return nil, r.Context().Err()
	})}
	_, err := send(ctx, client, "https://example.invalid/api/v1", "test-key", []byte("{}"))
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected cancellation, got %v", err)
	}
}

func TestReadResponse(t *testing.T) {
	cases := []struct {
		name, body, want string
		wantError        bool
	}{
		{name: "text after a non-message item", body: `{"status":"completed","output":[{"type":"reasoning"},{"type":"message","content":[{"type":"output_text","text":"Finish onboarding."}]}]}`, want: "Finish onboarding."},
		{name: "incomplete text is not success", body: `{"status":"incomplete","output":[{"type":"message","content":[{"type":"output_text","text":"Finish"}]}]}`, wantError: true},
		{name: "refusal has no answer text", body: `{"status":"completed","output":[{"type":"message","content":[{"type":"refusal","refusal":"No"}]}]}`, wantError: true},
		{name: "malformed body", body: `not json`, wantError: true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			result, err := readResponse(strings.NewReader(tc.body))
			if (err != nil) != tc.wantError {
				t.Fatalf("error = %v", err)
			}
			if err == nil && answerText(result) != tc.want {
				t.Fatalf("answer = %q", answerText(result))
			}
		})
	}
}

func TestAskSendsNoteAndInstructions(t *testing.T) {
	client := &http.Client{Transport: transportFunc(func(r *http.Request) (*http.Response, error) {
		if r.URL.Path != "/api/v1/responses" || r.Method != http.MethodPost {
			t.Fatalf("unexpected request: %s %s", r.Method, r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer test-key" {
			t.Fatal("missing authorization")
		}
		var payload struct {
			Model        string `json:"model"`
			Instructions string `json:"instructions"`
			Input        string `json:"input"`
			Store        bool   `json:"store"`
		}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Fatal(err)
		}
		if payload.Model != "test-model" || payload.Instructions != instructions ||
			!strings.Contains(payload.Input, note) || !strings.Contains(payload.Input, "When is launch?") || payload.Store {
			t.Fatal("request must include model, instructions, note, question, and store=false")
		}
		return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(
			`{"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"Friday."}]}]}`))}, nil
	})}
	result, err := ask(context.Background(), client, "https://example.invalid/api/v1", "test-key", "test-model", "When is launch?")
	if err != nil {
		t.Fatal(err)
	}
	if answerText(result) != "Friday." {
		t.Fatalf("answer = %q", answerText(result))
	}
}
