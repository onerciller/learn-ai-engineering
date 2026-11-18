package main

import (
	"testing"
	"unicode/utf8"
)

func TestPrepareDropsWholeTurns(t *testing.T) {
	h := []message{{Role: "user", Content: "old question"}, {Role: "assistant", Content: "old answer"}}
	budget := utf8.RuneCountInString(rules + "Note:\n" + note + "Friday?")
	input, dropped, err := prepare(h, "Friday?", budget)
	if err != nil {
		t.Fatal(err)
	}
	if dropped != 1 || len(input) != 2 || input[0].Content != "Note:\n"+note || input[1].Content != "Friday?" {
		t.Fatalf("bad history: %+v, %d", input, dropped)
	}
	if h[0].Content != "old question" {
		t.Fatal("caller history changed")
	}
}
func TestPrepareRejectsOversizedCurrentInput(t *testing.T) {
	if _, _, err := prepare([]message{}, "When?", 1); err == nil {
		t.Fatal("expected an error")
	}
}
func TestPrepareKeepsUnicodeAndRecentTurns(t *testing.T) {
	h := []message{{Role: "user", Content: "Ne?"}, {Role: "assistant", Content: "Cuma"}}
	input, dropped, err := prepare(h, "Gün?", 1000)
	if err != nil || dropped != 0 || len(input) != 4 {
		t.Fatalf("input=%v dropped=%d error=%v", input, dropped, err)
	}
}
