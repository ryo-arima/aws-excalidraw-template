// Package entity defines the data structures for Excalidraw JSON documents.
package entity

// Scene is the root Excalidraw document (version 2).
type Scene struct {
	Type     string                            `json:"type"`
	Version  int                               `json:"version"`
	Source   string                            `json:"source"`
	Elements []map[string]interface{}          `json:"elements"`
	AppState map[string]interface{}            `json:"appState"`
	Files    map[string]map[string]interface{} `json:"files"`
}

// NewScene creates an empty Scene with default fields.
func NewScene() *Scene {
	return &Scene{
		Type:     "excalidraw",
		Version:  2,
		Source:   "https://excalidraw.com",
		Elements: []map[string]interface{}{},
		AppState: map[string]interface{}{
			"gridSize":              nil,
			"viewBackgroundColor":   "#ffffff",
		},
		Files: map[string]map[string]interface{}{},
	}
}
