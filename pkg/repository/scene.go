package repository

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/entity"
)

// WriteScene serialises scene to a .excalidraw JSON file.
func WriteScene(scene *entity.Scene, path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", filepath.Dir(path), err)
	}
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create %s: %w", path, err)
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	enc.SetEscapeHTML(false)
	return enc.Encode(scene)
}

// ReadScene reads and parses a .excalidraw JSON file.
func ReadScene(path string) (*entity.Scene, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	var scene entity.Scene
	if err := json.Unmarshal(data, &scene); err != nil {
		return nil, fmt.Errorf("parse %s: %w", path, err)
	}
	return &scene, nil
}
