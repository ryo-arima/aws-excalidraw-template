// Package repository provides element builder helpers.
package repository

import "math"

const updated int64 = 1709000000000

// base returns the common fields shared by every Excalidraw element.
func base(eid string, x, y, w, h float64, seed int) map[string]interface{} {
	return map[string]interface{}{
		"id":            eid,
		"x":             math.Round(x),
		"y":             math.Round(y),
		"width":         math.Round(w),
		"height":        math.Round(h),
		"angle":         0,
		"opacity":       100,
		"groupIds":      []interface{}{},
		"frameId":       nil,
		"roundness":     nil,
		"seed":          seed,
		"version":       1,
		"versionNonce":  seed,
		"isDeleted":     false,
		"boundElements": []interface{}{},
		"updated":       updated,
		"link":          nil,
		"locked":        false,
	}
}

// MakeText creates a text element.
func MakeText(eid string, x, y, w, h float64,
	text string, fontSize int, color string, seed int) map[string]interface{} {
	el := base(eid, x, y, w, h, seed)
	el["type"] = "text"
	el["strokeColor"] = color
	el["backgroundColor"] = "transparent"
	el["fillStyle"] = "solid"
	el["strokeWidth"] = 1
	el["strokeStyle"] = "solid"
	el["roughness"] = 0
	el["text"] = text
	el["fontSize"] = fontSize
	el["fontFamily"] = 2 // Helvetica
	el["textAlign"] = "left"
	el["verticalAlign"] = "top"
	el["containerId"] = nil
	el["originalText"] = text
	el["autoResize"] = true
	el["lineHeight"] = 1.25
	return el
}

// MakeImage creates an image (SVG icon) element referencing a file by ID.
func MakeImage(eid string, x, y, w, h float64, fileID string, seed int) map[string]interface{} {
	el := base(eid, x, y, w, h, seed)
	el["type"] = "image"
	el["strokeColor"] = "transparent"
	el["backgroundColor"] = "transparent"
	el["fillStyle"] = "solid"
	el["strokeWidth"] = 1
	el["strokeStyle"] = "solid"
	el["roughness"] = 0
	el["status"] = "saved"
	el["fileId"] = fileID
	el["scale"] = [2]float64{1, 1}
	return el
}

