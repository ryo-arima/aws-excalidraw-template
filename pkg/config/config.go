package config

import (
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// appYAML mirrors the structure of etc/app.yaml.
type appYAML struct {
	Canvas struct {
		URL string `yaml:"url"`
	} `yaml:"canvas"`
	Paths struct {
		AssetPackage       string `yaml:"asset_package"`
		Templates          string `yaml:"templates"`
		ServiceCatalogCSV  string `yaml:"service_catalog_csv"`
	} `yaml:"paths"`
	Output struct {
		Frames  string `yaml:"frames"`
		Catalog string `yaml:"catalog"`
	} `yaml:"output"`
	Legend struct {
		OffsetX  float64 `yaml:"offset_x"`
		OffsetY  float64 `yaml:"offset_y"`
		IconSize int     `yaml:"icon_size"`
		FontSize int     `yaml:"font_size"`
	} `yaml:"legend"`
}

// LegendConfig holds resolved legend defaults.
type LegendConfig struct {
	OffsetX  float64
	OffsetY  float64
	IconSize int
	FontSize int
}

// Config holds application-wide configuration resolved from etc/app.yaml and env vars.
type Config struct {
	ProjectRoot       string
	CanvasURL         string
	AssetDir_         string // absolute path to Asset-Package
	TemplSrcDir       string // absolute path to etc/resources/templates (source, read-only)
	OutFramesDir      string // absolute path to generated frames output dir
	OutCatalogFile    string // absolute path to generated catalog output file
	SvcCatalogCSV     string // absolute path to service-catalog.csv
	Legend            LegendConfig
}

// New loads etc/app.yaml from the project root and applies environment overrides.
func New() *Config {
	root := findProjectRoot()

	// defaults
	def := appYAML{}
	def.Canvas.URL = "http://localhost:3000"
	def.Paths.AssetPackage = "etc/resources/Asset-Package"
	def.Paths.Templates = "etc/resources/templates"
	def.Paths.ServiceCatalogCSV = "etc/resources/service-catalog.csv"
	def.Output.Frames = "output/aws-frames"
	def.Output.Catalog = "output/service-catalog.excalidraw"
	def.Legend.OffsetX = 120
	def.Legend.OffsetY = 0
	def.Legend.IconSize = 32
	def.Legend.FontSize = 12

	yamlPath := filepath.Join(root, "etc", "app.yaml")
	if data, err := os.ReadFile(yamlPath); err == nil {
		_ = yaml.Unmarshal(data, &def)
	}

	// ENV override
	if v := os.Getenv("EXPRESS_SERVER_URL"); v != "" {
		def.Canvas.URL = v
	}

	abs := func(rel string) string {
		if filepath.IsAbs(rel) {
			return rel
		}
		return filepath.Join(root, rel)
	}

	return &Config{
		ProjectRoot:    root,
		CanvasURL:      def.Canvas.URL,
		AssetDir_:      abs(def.Paths.AssetPackage),
		TemplSrcDir:    abs(def.Paths.Templates),
		OutFramesDir:   abs(def.Output.Frames),
		OutCatalogFile: abs(def.Output.Catalog),
		SvcCatalogCSV:  abs(def.Paths.ServiceCatalogCSV),
		Legend: LegendConfig{
			OffsetX:  def.Legend.OffsetX,
			OffsetY:  def.Legend.OffsetY,
			IconSize: def.Legend.IconSize,
			FontSize: def.Legend.FontSize,
		},
	}
}

// AssetDir returns the absolute path to the Asset-Package directory.
func (c *Config) AssetDir() string { return c.AssetDir_ }

// TemplatesSourceDir returns the absolute path to etc/resources/templates (source, read-only).
func (c *Config) TemplatesSourceDir() string { return c.TemplSrcDir }

// OutputFramesDir returns the absolute path to the generated frames output directory.
func (c *Config) OutputFramesDir() string { return c.OutFramesDir }

// OutputCatalogFile returns the absolute path to the generated catalog output file.
func (c *Config) OutputCatalogFile() string { return c.OutCatalogFile }

// ServiceCatalogCSVPath returns the absolute path to the service-catalog CSV file.
func (c *Config) ServiceCatalogCSVPath() string { return c.SvcCatalogCSV }

// findProjectRoot walks up from cwd until it finds go.mod, then returns that dir.
func findProjectRoot() string {
	cwd, err := os.Getwd()
	if err != nil {
		return "."
	}
	dir := cwd
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return cwd
}
