package repository

import (
	"crypto/md5"
	"encoding/base64"
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"regexp"
	"strconv"
	"strings"
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

// LoadFromCSV looks up svgFilename in the catalog CSV and returns the base64 data URL.
// Supported formats:
//   - 6-column (new): id, category, service, svg_file, rel_path, base64
//   - 5-column (old): category, service, svg_file, rel_path, base64
func LoadFromCSV(csvPath, svgFilename string) (string, error) {
	f, err := os.Open(csvPath)
	if err != nil {
		return "", fmt.Errorf("open catalog csv: %w", err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	// read header to detect column layout
	header, err := r.Read()
	if err != nil {
		return "", fmt.Errorf("read csv header: %w", err)
	}
	// determine indices by header name (case-insensitive)
	svgCol, b64Col := 2, 4 // legacy defaults
	for i, h := range header {
		switch strings.ToLower(h) {
		case "svg_file":
			svgCol = i
		case "base64":
			b64Col = i
		}
	}
	minCols := b64Col + 1
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", fmt.Errorf("read csv: %w", err)
		}
		if len(rec) >= minCols && strings.EqualFold(rec[svgCol], svgFilename) {
			return rec[b64Col], nil
		}
	}
	return "", fmt.Errorf("svg %q not found in catalog csv", svgFilename)
}

// LoadFromCSVByID looks up an entry in the catalog CSV by numeric id.
// When officialName is non-empty, the service name column must also match
// (case-insensitive AND match).
// Returns (svgFile, dataURL, error); svgFile is the value of the svg_file column
// (e.g. "Arch_Amazon-EC2_64.svg").
func LoadFromCSVByID(csvPath string, id int, officialName string) (string, string, error) {
	f, err := os.Open(csvPath)
	if err != nil {
		return "", "", fmt.Errorf("open catalog csv: %w", err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.LazyQuotes = true
	header, err := r.Read()
	if err != nil {
		return "", "", fmt.Errorf("read csv header: %w", err)
	}
	// detect column positions from header names
	idCol, svcCol, svgCol, b64Col := 0, 2, 3, 5
	for i, h := range header {
		switch strings.ToLower(strings.TrimSpace(h)) {
		case "id":
			idCol = i
		case "service":
			svcCol = i
		case "svg_file":
			svgCol = i
		case "base64":
			b64Col = i
		}
	}
	idStr := strconv.Itoa(id)
	minCols := b64Col + 1
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", "", fmt.Errorf("read csv: %w", err)
		}
		if len(rec) < minCols {
			continue
		}
		if strings.TrimSpace(rec[idCol]) != idStr {
			continue
		}
		if officialName != "" && !strings.EqualFold(strings.TrimSpace(rec[svcCol]), strings.TrimSpace(officialName)) {
			continue
		}
		return strings.TrimSpace(rec[svgCol]), rec[b64Col], nil
	}
	if officialName != "" {
		return "", "", fmt.Errorf("catalog: id=%d name=%q not found (AND match failed)", id, officialName)
	}
	return "", "", fmt.Errorf("catalog: id=%d not found", id)
}

// svgBGColorRe matches the first non-white hex fill color in an SVG.
var svgBGColorRe = regexp.MustCompile(`fill="(#[0-9a-fA-F]{3,6})"`)

// SVGBGColor decodes a base64 data URL and returns the icon background color.
// Falls back to "#232F3E" (AWS dark) if no suitable color is found.
func SVGBGColor(dataURL string) string {
	const prefix = "data:image/svg+xml;base64,"
	if !strings.HasPrefix(dataURL, prefix) {
		return "#232F3E"
	}
	decoded, err := base64.StdEncoding.DecodeString(dataURL[len(prefix):])
	if err != nil {
		return "#232F3E"
	}
	svg := string(decoded)
	for _, m := range svgBGColorRe.FindAllStringSubmatch(svg, -1) {
		c := strings.ToUpper(m[1])
		// skip white and near-white
		if c == "#FFFFFF" || c == "#FFF" || c == "#FEFEFE" {
			continue
		}
		return m[1]
	}
	return "#232F3E"
}

