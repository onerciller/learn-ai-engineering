package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// This small HTTP helper is repeated so each part runs on its own.
type apiClient struct {
	Key, Model, URL string
	HTTP            *http.Client
}

type modelResponse struct {
	Status string            `json:"status"`
	Output []json.RawMessage `json:"output"`
	Usage  struct {
		InputTokens  int `json:"input_tokens"`
		OutputTokens int `json:"output_tokens"`
	} `json:"usage"`
}

type message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func configuredClient() (apiClient, error) {
	key := strings.TrimSpace(os.Getenv("OPENROUTER_API_KEY"))
	model := strings.TrimSpace(os.Getenv("OPENROUTER_MODEL"))
	if key == "" || model == "" {
		return apiClient{}, errors.New("set OPENROUTER_API_KEY and OPENROUTER_MODEL")
	}
	return apiClient{Key: key, Model: model, URL: "https://openrouter.ai/api/v1/responses", HTTP: http.DefaultClient}, nil
}

func (c apiClient) post(ctx context.Context, payload map[string]any) (*http.Response, error) {
	payload["model"] = c.Model
	payload["store"] = false
	payload["max_output_tokens"] = 1024
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("encode request: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.URL, bytes.NewReader(body))
	if err != nil {
		return nil, errors.New("invalid api url")
	}
	req.Header.Set("Authorization", "Bearer "+c.Key)
	req.Header.Set("Content-Type", "application/json")
	res, err := c.HTTP.Do(req)
	if err != nil {
		if ctx.Err() != nil {
			return nil, fmt.Errorf("request stopped: %w", ctx.Err())
		}
		return nil, errors.New("could not reach OpenRouter")
	}
	if res.StatusCode != http.StatusOK {
		if err := res.Body.Close(); err != nil {
			return nil, fmt.Errorf("close failed API response: %w", err)
		}
		return nil, fmt.Errorf("OpenRouter returned HTTP %d", res.StatusCode)
	}
	return res, nil
}

func (c apiClient) complete(ctx context.Context, payload map[string]any) (modelResponse, error) {
	res, err := c.post(ctx, payload)
	if err != nil {
		return modelResponse{}, err
	}
	defer res.Body.Close()
	var result modelResponse
	if err := json.NewDecoder(io.LimitReader(res.Body, 1<<20)).Decode(&result); err != nil {
		return modelResponse{}, fmt.Errorf("decode response: %w", err)
	}
	if result.Status != "completed" {
		return modelResponse{}, errors.New("model response did not complete")
	}
	return result, nil
}

func answerText(result modelResponse) (string, error) {
	parts := []string{}
	for _, raw := range result.Output {
		var item struct {
			Type    string `json:"type"`
			Content []struct {
				Type string `json:"type"`
				Text string `json:"text"`
			} `json:"content"`
		}
		if err := json.Unmarshal(raw, &item); err != nil {
			return "", fmt.Errorf("decode output item: %w", err)
		}
		if item.Type != "message" {
			continue
		}
		for _, content := range item.Content {
			if content.Type == "output_text" {
				parts = append(parts, content.Text)
			}
		}
	}
	text := strings.TrimSpace(strings.Join(parts, "\n"))
	if text == "" {
		return "", errors.New("response contains no answer text")
	}
	return text, nil
}
