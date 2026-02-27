package repository

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/entity"
)

// ReadServiceList reads a service-list CSV file and returns a slice of ServiceEntry.
//
// Supported CSV formats (header row is optional, '#' lines are comments):
//
//	正式名称,略語,サービス概要,用途,備考          (id なし / 後方互換)
//	id,正式名称,略語,サービス概要,用途,備考       (id あり / 新形式)
//
// When the first column of a data row contains a valid integer it is parsed as
// CatalogID and the remaining columns are shifted right by one.
// Blank lines and rows with an empty 正式名称 column are skipped.
func ReadServiceList(path string) ([]entity.ServiceEntry, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open service list %s: %w", path, err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.Comment = '#'
	r.FieldsPerRecord = -1 // allow variable number of columns
	r.TrimLeadingSpace = true
	r.LazyQuotes = true

	rows, err := r.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("parse CSV %s: %w", path, err)
	}

	var entries []entity.ServiceEntry
	for _, row := range rows {
		if len(row) == 0 {
			continue
		}
		first := strings.TrimSpace(row[0])
		// skip header row ("id", "正式名称" など)
		if strings.EqualFold(first, "id") || strings.EqualFold(first, "正式名称") {
			continue
		}

		e := entity.ServiceEntry{}
		offset := 0
		// if the first column is an integer, treat it as CatalogID
		if id, err := strconv.Atoi(first); err == nil {
			e.CatalogID = id
			offset = 1
		}
		if len(row) > offset {
			e.OfficialName = strings.TrimSpace(row[offset])
		}
		if len(row) > offset+1 {
			e.Abbreviation = strings.TrimSpace(row[offset+1])
		}
		if len(row) > offset+2 {
			e.Summary = strings.TrimSpace(row[offset+2])
		}
		if len(row) > offset+3 {
			e.Usage = strings.TrimSpace(row[offset+3])
		}
		if len(row) > offset+4 {
			e.Note = strings.TrimSpace(row[offset+4])
		}
		if e.OfficialName == "" {
			continue
		}
		entries = append(entries, e)
	}
	return entries, nil
}
