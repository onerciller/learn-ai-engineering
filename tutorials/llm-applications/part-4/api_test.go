package main

import (
	"encoding/json"
	"testing"
)

func TestAnswerTextSkipsNonMessages(t *testing.T) {
	r := modelResponse{Output: []json.RawMessage{json.RawMessage(`{"type":"reasoning"}`), json.RawMessage(`{"type":"message","content":[{"type":"output_text","text":"Answer"}]}`)}}
	text, err := answerText(r)
	if err != nil || text != "Answer" {
		t.Fatalf("text=%q error=%v", text, err)
	}
}
func TestAnswerTextRejectsRefusal(t *testing.T) {
	r := modelResponse{Output: []json.RawMessage{json.RawMessage(`{"type":"message","content":[{"type":"refusal","refusal":"No"}]}`)}}
	if _, err := answerText(r); err == nil {
		t.Fatal("expected missing text error")
	}
}
