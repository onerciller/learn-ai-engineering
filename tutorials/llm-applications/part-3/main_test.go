package main

import "testing"

func TestParseSummary(t *testing.T) {
	cases := []struct {
		name, input string
		bad         bool
	}{
		{name: "valid", input: `{"title":"Launch","summary":"Finish onboarding before Friday."}`},
		{name: "missing field", input: `{"title":"Launch"}`, bad: true},
		{name: "empty field", input: `{"title":" ","summary":"text"}`, bad: true},
		{name: "extra field", input: `{"title":"Launch","summary":"text","owner":"invented"}`, bad: true},
		{name: "wrong type", input: `{"title":4,"summary":"text"}`, bad: true},
		{name: "two objects", input: `{"title":"a","summary":"b"} {}`, bad: true},
		{name: "invalid json", input: `not json`, bad: true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := parseSummary(tc.input)
			if (err != nil) != tc.bad {
				t.Fatalf("error=%v", err)
			}
		})
	}
}
func TestShapeDoesNotProveFacts(t *testing.T) {
	if _, err := parseSummary(`{"title":"Launch","summary":"The owner is Alice."}`); err != nil {
		t.Fatal("shape checker should not pretend to verify facts")
	}
}
