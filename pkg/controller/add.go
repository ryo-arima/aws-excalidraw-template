package controller

import (
	"crypto/rand"
	"fmt"
	"math"
	"path/filepath"
	"strings"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/config"
	"github.com/ryo-arima/aws-excalidraw-template/pkg/entity"
	"github.com/ryo-arima/aws-excalidraw-template/pkg/repository"
	"github.com/spf13/cobra"
)

// InitAddCmd returns the 'add' parent command.
func InitAddCmd() *cobra.Command {
	addCmd := &cobra.Command{
		Use:   "add",
		Short: "Add an AWS service icon to the live Excalidraw canvas",
		Long: `Add an AWS service icon, label, and legend entry to the mcp-excalidraw-canvas server.

The canvas server URL is read from EXPRESS_SERVER_URL (default http://localhost:3000)
or can be overridden with --server.`,
	}
	addCmd.AddCommand(initAddServiceCmd())
	return addCmd
}

// ─────────────────────────────────────────────────────────────────────────────
// add service

func initAddServiceCmd() *cobra.Command {
	var (
		serverURL string
		category  string
		name      string
		x, y      float64
		size      int
		legendX   float64
		legendY   float64
		noLegend  bool
		noMerge   bool
	)

	cmd := &cobra.Command{
		Use:   "service",
		Short: "Add an AWS service icon+label and its legend entry to the live canvas",
		Long: `Searches Architecture-Service-Icons for the given service name, places the icon
and a label at (x, y), then adds a legend entry outside the frame.

The legend entry consists of a small icon and the service name, placed at
(legend-x, legend-y). If not specified, the legend is placed at
x + icon-size + legend.offset_x (from app.yaml).

Examples:
  aet add service --name EC2 --x 100 --y 100
  aet add service --name Lambda --x 200 --y 100 --size 64
  aet add service --name RDS --category Arch_Database --x 300 --y 100 --legend-x 800 --legend-y 100`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg := config.New()
			if serverURL == "" {
				serverURL = cfg.CanvasURL
			}

			// ── find service icon ───────────────────────────────────────────
			svgPath, displayName, err := findServiceIcon(cfg.AssetDir(), category, name, size)
			if err != nil {
				return err
			}

			dataURL, err := repository.SvgToDataURL(svgPath)
			if err != nil {
				return fmt.Errorf("load icon %s: %w", svgPath, err)
			}

			fid := repository.FileID(svgPath)
			files := map[string]map[string]interface{}{}
			files[fid] = map[string]interface{}{
				"mimeType":      "image/svg+xml",
				"id":            fid,
				"dataURL":       dataURL,
				"created":       int64(1709000000000),
				"lastRetrieved": int64(1709000000000),
			}

			elements := []map[string]interface{}{}
			eid := "svc-" + randomHex(6)
			sz := float64(size)

			// ── main icon ──────────────────────────────────────────────────
			elements = append(elements,
				repository.MakeImage(eid, x, y, sz, sz, fid, 6001))

			// ── main label (below icon) ────────────────────────────────────
			lblW := math.Max(sz*3, 120)
			lblX := x + sz/2 - lblW/2
			lblY := y + sz + 4
			elements = append(elements,
				repository.MakeText(eid+"-label", lblX, lblY, lblW, 16,
					displayName, 12, "#1e1e1e", 6002))

			// ── legend entry (outside frame) ───────────────────────────────
			if !noLegend {
				lgSz := float64(cfg.Legend.IconSize)
				lgFs := cfg.Legend.FontSize

				// default legend position
				if !cmd.Flags().Changed("legend-x") {
					legendX = x + sz + cfg.Legend.OffsetX
				}
				if !cmd.Flags().Changed("legend-y") {
					legendY = y + cfg.Legend.OffsetY
				}

				// legend icon (same SVG, smaller)
				lgFid := repository.FileID(svgPath + "-legend")
				files[lgFid] = map[string]interface{}{
					"mimeType":      "image/svg+xml",
					"id":            lgFid,
					"dataURL":       dataURL,
					"created":       int64(1709000000000),
					"lastRetrieved": int64(1709000000000),
				}
				elements = append(elements,
					repository.MakeImage(eid+"-lg-icon", legendX, legendY, lgSz, lgSz, lgFid, 6003))

				// legend label (to the right of the small icon)
				lgLblX := legendX + lgSz + 6
				lgLblY := legendY + (lgSz-float64(lgFs))/2
				lgLblW := math.Max(lgSz*5, 160)
				elements = append(elements,
					repository.MakeText(eid+"-lg-label", lgLblX, lgLblY, lgLblW, float64(lgFs+4),
						displayName, lgFs, "#1e1e1e", 6004))
			}

			// ── push to canvas ─────────────────────────────────────────────
			scene := entity.NewScene()
			scene.Elements = elements
			scene.Files = files

			client := repository.NewCanvasClient(serverURL)
			if err := client.Health(); err != nil {
				return fmt.Errorf("canvas server not reachable at %s: %w", serverURL, err)
			}

			if noMerge {
				return client.SyncScene(scene)
			}
			if err := client.MergeScene(scene); err != nil {
				return fmt.Errorf("merge to canvas: %w", err)
			}
			fmt.Printf("Added service %s to canvas at %s\n", displayName, serverURL)
			if !noLegend {
				fmt.Printf("  legend entry at (%.0f, %.0f)\n", legendX, legendY)
			}
			return nil
		},
	}

	cmd.Flags().StringVarP(&serverURL, "server", "s", "", "canvas server URL (default: config canvas.url)")
	cmd.Flags().StringVar(&category, "category", "", "service icon category, e.g. Arch_Compute (optional, speeds up search)")
	cmd.Flags().StringVarP(&name, "name", "n", "", "service name to search for, e.g. EC2 (required)")
	cmd.Flags().Float64Var(&x, "x", 0, "x position of the service icon")
	cmd.Flags().Float64Var(&y, "y", 0, "y position of the service icon")
	cmd.Flags().IntVar(&size, "size", 64, "icon size in pixels (16 | 32 | 48 | 64)")
	cmd.Flags().Float64Var(&legendX, "legend-x", 0, "x position of the legend entry (default: x+size+offset_x)")
	cmd.Flags().Float64Var(&legendY, "legend-y", 0, "y position of the legend entry (default: y+offset_y)")
	cmd.Flags().BoolVar(&noLegend, "no-legend", false, "omit the legend entry")
	cmd.Flags().BoolVar(&noMerge, "replace", false, "replace the entire canvas instead of merging")
	_ = cmd.MarkFlagRequired("name")
	return cmd
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers

// randomHex returns n random hex bytes as a string.
func randomHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return fmt.Sprintf("%x", b)
}

// normalizeSvgName derives a display name from an SVG filename.
func normalizeSvgName(filename string) string {
	name := strings.TrimSuffix(filename, ".svg")
	for _, prefix := range []string{"Arch_", "Res_", "Arch-Category_"} {
		if strings.HasPrefix(name, prefix) {
			name = name[len(prefix):]
			break
		}
	}
	for _, suffix := range []string{"_64", "_48", "_32", "_16"} {
		if strings.HasSuffix(name, suffix) {
			name = name[:len(name)-len(suffix)]
			break
		}
	}
	return strings.ReplaceAll(strings.ReplaceAll(name, "-", " "), "_", " ")
}

// findServiceIcon searches Architecture-Service-Icons for an SVG matching name.
// Prefers the directory matching the requested size; falls back to other sizes.
func findServiceIcon(assetDir, category, name string, size int) (string, string, error) {
	archSvc := filepath.Join(assetDir, "Architecture-Service-Icons")
	lower := strings.ToLower(name)

	// size preference order
	szDirs := []string{fmt.Sprintf("%d", size), "64", "48", "32", "16"}
	// deduplicate while preserving order
	seen := map[string]bool{}
	var szOrder []string
	for _, s := range szDirs {
		if !seen[s] {
			szOrder = append(szOrder, s)
			seen[s] = true
		}
	}

	walkCat := func(catDir string) (string, string, bool) {
		for _, szDir := range szOrder {
			entries, err := filepath.Glob(filepath.Join(catDir, szDir, "*.svg"))
			if err != nil || len(entries) == 0 {
				continue
			}
			for _, p := range entries {
				base := filepath.Base(p)
				if strings.Contains(strings.ToLower(base), lower) {
					return p, normalizeSvgName(base), true
				}
			}
		}
		return "", "", false
	}

	if category != "" {
		if p, dn, ok := walkCat(filepath.Join(archSvc, category)); ok {
			return p, dn, nil
		}
		return "", "", fmt.Errorf("service %q not found in category %q", name, category)
	}

	cats, err := filepath.Glob(filepath.Join(archSvc, "Arch_*"))
	if err != nil {
		return "", "", fmt.Errorf("scan service icons: %w", err)
	}
	for _, cat := range cats {
		if p, dn, ok := walkCat(cat); ok {
			return p, dn, nil
		}
	}
	return "", "", fmt.Errorf("service icon for %q not found in %s", name, archSvc)
}
