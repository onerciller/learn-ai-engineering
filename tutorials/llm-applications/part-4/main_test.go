package main

import (
	"context"
	"strings"
	"testing"
)

func TestReadStream(t *testing.T) {
	cases := []struct {
		name, events, want, state string
		bad                       bool
	}{
		{name: "canonical deltas", events: "data: {\"type\":\"response.output_text.delta\",\"delta\":\"Hello\"}\n\ndata: {\"type\":\"response.completed\",\"response\":{\"status\":\"completed\"}}\n\n", want: "Hello", state: "complete"},
		{name: "documented alternate events", events: ":keepalive\n\ndata: {\"type\":\"response.content_part.delta\",\"delta\":\"Hi\"}\n\ndata: {\"type\":\"response.done\",\"response\":{\"status\":\"completed\"}}\n\n", want: "Hi", state: "complete"},
		{name: "multiline event", events: "data: {\"type\":\"response.output_text.delta\",\ndata: \"delta\":\"Hi\"}\n\ndata: {\"type\":\"response.completed\",\"response\":{\"status\":\"completed\"}}\n\n", want: "Hi", state: "complete"},
		{name: "done marker alone", events: "data: [DONE]\n\n", state: "interrupted", bad: true},
		{name: "cut off after partial text", events: "data: {\"type\":\"response.output_text.delta\",\"delta\":\"Half\"}\n\n", want: "Half", state: "interrupted", bad: true},
		{name: "failed response", events: "data: {\"type\":\"response.failed\"}\n\n", state: "interrupted", bad: true},
		{name: "no text", events: "data: {\"type\":\"response.completed\",\"response\":{\"status\":\"completed\"}}\n\n", state: "interrupted", bad: true},
		{name: "malformed event", events: "data: broken\n\n", state: "interrupted", bad: true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var out strings.Builder
			state, err := readStream(context.Background(), strings.NewReader(tc.events), &out)
			if state != tc.state || (err != nil) != tc.bad || out.String() != tc.want {
				t.Fatalf("state=%s error=%v output=%q", state, err, out.String())
			}
		})
	}
}
func TestReadStreamCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	var out strings.Builder
	state, err := readStream(ctx, strings.NewReader("data: {}\n\n"), &out)
	if state != "cancelled" || err == nil || out.Len() != 0 {
		t.Fatalf("state=%s error=%v", state, err)
	}
}
