package main

import (
	"encoding/json"
	"testing"
)

func TestReadCall(t *testing.T) {
	cases := []struct {
		name, body string
		bad        bool
	}{
		{name: "allowed", body: `{"type":"function_call","name":"search_notes","call_id":"call-1","arguments":"{\"query\":\"tools\"}"}`},
		{name: "wrong tool", body: `{"type":"function_call","name":"delete_notes","call_id":"call-1","arguments":"{\"query\":\"tools\"}"}`, bad: true},
		{name: "empty query", body: `{"type":"function_call","name":"search_notes","call_id":"call-1","arguments":"{\"query\":\"\"}"}`, bad: true},
		{name: "extra argument", body: `{"type":"function_call","name":"search_notes","call_id":"call-1","arguments":"{\"query\":\"tools\",\"delete\":true}"}`, bad: true},
		{name: "missing id", body: `{"type":"function_call","name":"search_notes","arguments":"{\"query\":\"tools\"}"}`, bad: true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, _, err := readCall(modelResponse{Output: []json.RawMessage{json.RawMessage(tc.body)}})
			if (err != nil) != tc.bad {
				t.Fatalf("error=%v", err)
			}
		})
	}
}
func TestReadCallRejectsMultipleCalls(t *testing.T) {
	item := json.RawMessage(`{"type":"function_call","name":"search_notes","call_id":"x","arguments":"{\"query\":\"tools\"}"}`)
	if _, _, err := readCall(modelResponse{Output: []json.RawMessage{item, item}}); err == nil {
		t.Fatal("expected multiple-call rejection")
	}
}
