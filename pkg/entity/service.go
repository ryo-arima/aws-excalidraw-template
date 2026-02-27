package entity

// ServiceEntry represents one row in a service-list CSV file.
//
// CSV column order (header is optional, '#' lines are comments):
//
//	正式名称,略語,サービス概要,用途,備考          (id なし / 後方互換)
//	id,正式名称,略語,サービス概要,用途,備考       (id あり / 新形式)
//
// When CatalogID > 0, icon lookup uses service-catalog.csv directly by id
// (AND match with OfficialName when OfficialName is also specified).
type ServiceEntry struct {
	CatalogID    int    // catalog id  (0 = not specified)
	OfficialName string // 正式名称 (例: "Amazon EC2")
	Abbreviation string // 略語     (例: "EC2")  ─ アイコン下ラベルに使用
	Summary      string // サービス概要
	Usage        string // 用途
	Note         string // 備考
}

// ShortLabel returns the abbreviation when non-empty, otherwise the official name.
// Used for the compact label placed below the icon on the canvas.
func (s ServiceEntry) ShortLabel() string {
	if s.Abbreviation != "" {
		return s.Abbreviation
	}
	return s.OfficialName
}
