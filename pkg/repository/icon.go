package repository

import (
	"crypto/md5"
	"encoding/base64"
	"fmt"
	"os"
)

// SvgToDataURL reads a file and returns a base64 data URL.
func SvgToDataURL(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("read svg %s: %w", path, err)
	}
	encoded := base64.StdEncoding.EncodeToString(data)
	return "data:image/svg+xml;base64," + encoded, nil
}

// FileID returns a 16-char MD5 hex string used as the Excalidraw file ID.
func FileID(name string) string {
	h := md5.Sum([]byte(name))
	return fmt.Sprintf("%x", h)[:16]
}

