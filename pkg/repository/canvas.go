package repository

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/entity"
)

// CanvasClient is an HTTP client for the mcp-excalidraw-canvas REST API.
// Canvas REST API reference (http://localhost:3000):
//
//	GET  /api/elements          – list all elements
//	POST /api/elements/batch    – create many elements
//	POST /api/elements/sync     – overwrite canvas (clear + write)
//	DELETE /api/elements/clear  – clear canvas
//	GET  /health                – health check
type CanvasClient struct {
	BaseURL    string
	httpClient *http.Client
}

// NewCanvasClient creates a CanvasClient targeting baseURL (default: http://localhost:3000).
func NewCanvasClient(baseURL string) *CanvasClient {
	if baseURL == "" {
		baseURL = "http://localhost:3000"
	}
	return &CanvasClient{
		BaseURL:    baseURL,
		httpClient: &http.Client{},
	}
}

// Health checks whether the canvas server is reachable.
func (c *CanvasClient) Health() error {
	resp, err := c.httpClient.Get(c.BaseURL + "/health")
	if err != nil {
		return fmt.Errorf("canvas health check: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("canvas health: status %d: %s", resp.StatusCode, body)
	}
	return nil
}

// elementsResponse wraps the canvas API response for GET /api/elements.
// The server returns {"success": bool, "elements": [...], "count": int}.
type elementsResponse struct {
	Success  bool                     `json:"success"`
	Elements []map[string]interface{} `json:"elements"`
	Count    int                      `json:"count"`
}

// GetElements fetches all elements currently on the canvas.
func (c *CanvasClient) GetElements() ([]map[string]interface{}, error) {
	resp, err := c.httpClient.Get(c.BaseURL + "/api/elements")
	if err != nil {
		return nil, fmt.Errorf("get elements: %w", err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read elements body: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get elements: status %d: %s", resp.StatusCode, body)
	}
	var wrapper elementsResponse
	if err := json.Unmarshal(body, &wrapper); err != nil {
		return nil, fmt.Errorf("parse elements: %w", err)
	}
	return wrapper.Elements, nil
}

// BatchCreate appends new elements to the canvas without clearing existing ones.
func (c *CanvasClient) BatchCreate(elements []map[string]interface{}) error {
	return c.postJSON(c.BaseURL+"/api/elements/batch", elements)
}

// SyncScene replaces the entire canvas with the provided scene (clear + write).
// files may be nil/empty if no images are involved.
func (c *CanvasClient) SyncScene(scene *entity.Scene) error {
	payload := map[string]interface{}{
		"elements": scene.Elements,
		"files":    scene.Files,
	}
	return c.postJSON(c.BaseURL+"/api/elements/sync", payload)
}

// MergeScene gets the current canvas content, merges new elements and files,
// then syncs the combined result back. This preserves existing canvas content.
func (c *CanvasClient) MergeScene(newScene *entity.Scene) error {
	existing, err := c.GetElements()
	if err != nil {
		return fmt.Errorf("merge: get existing: %w", err)
	}

	merged := make([]map[string]interface{}, 0, len(existing)+len(newScene.Elements))
	merged = append(merged, existing...)
	merged = append(merged, newScene.Elements...)

	combined := &entity.Scene{
		Type:     "excalidraw",
		Version:  2,
		Source:   "https://excalidraw.com",
		Elements: merged,
		AppState: newScene.AppState,
		Files:    newScene.Files,
	}
	return c.SyncScene(combined)
}

// ClearCanvas removes all elements from the canvas.
func (c *CanvasClient) ClearCanvas() error {
	req, err := http.NewRequest(http.MethodDelete, c.BaseURL+"/api/elements/clear", nil)
	if err != nil {
		return fmt.Errorf("build clear request: %w", err)
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("clear canvas: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("clear canvas: status %d: %s", resp.StatusCode, body)
	}
	return nil
}

// postJSON marshals v as JSON and POSTs it to url.
func (c *CanvasClient) postJSON(url string, v interface{}) error {
	data, err := json.Marshal(v)
	if err != nil {
		return fmt.Errorf("marshal payload: %w", err)
	}
	resp, err := c.httpClient.Post(url, "application/json", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("POST %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("POST %s: status %d: %s", url, resp.StatusCode, body)
	}
	return nil
}
