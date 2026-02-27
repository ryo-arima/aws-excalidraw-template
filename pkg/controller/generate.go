package controller

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/config"
	"github.com/spf13/cobra"
)

// InitGenerateCmd returns the 'generate' parent command.
func InitGenerateCmd() *cobra.Command {
	genCmd := &cobra.Command{
		Use:   "generate",
		Short: "Copy .excalidraw templates to the output directory",
		Long:  "Copies .excalidraw template files from the source templates directory to the output directory.",
	}
	genCmd.AddCommand(initGenerateFramesCmd())
	genCmd.AddCommand(initGenerateCatalogCmd())
	return genCmd
}

// initGenerateFramesCmd creates 'generate frames'.
//
//	aet generate frames [--variant <name>] [--size A4] [--output dir] [--list-variants]
func initGenerateFramesCmd() *cobra.Command {
	var (
		outputDir    string
		sizeFlag     string
		variantFlag  string
		listVariants bool
	)

	const defaultVariant = "1cloud-1account-1region-2az-3subnet"

	cmd := &cobra.Command{
		Use:   "frames",
		Short: "Copy AWS frame templates to the output directory",
		Long: `Copies .excalidraw files from templates/aws-frames/<variant>/ to the output directory.

Available variants are named as:
  <N>cloud-<N>account-<N>region-<N>az-<N>subnet[-staggered]
  e.g. 1cloud-1account-1region-2az-3subnet  (default)
       1cloud-1account-1region-2az-3subnet-staggered  (staggered AZ layout)
       2cloud-3account-2region-3az-4subnet  (most complex)
  "base" copies the original pre-generated templates.

  Subnet counts: 2 (Public + Private), 3 (Public + Private 1/2), 4 (Public + Private 1/2/3)
  AZ layout:     grid (default), staggered (overlapping AZs with depth shading, requires N>=2)

Use --list-variants to see all variants available in the template directory.

Examples:
  aet generate frames
  aet generate frames --variant 1cloud-1account-1region-2az-2subnet
  aet generate frames --variant 1cloud-1account-1region-2az-3subnet-staggered
  aet generate frames --variant 2cloud-3account-2region-3az-4subnet
  aet generate frames --variant base
  aet generate frames --size A4
  aet generate frames --list-variants
  aet generate frames --output /tmp/my-frames`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg := config.New()
			awsFramesDir := filepath.Join(cfg.TemplatesSourceDir(), "aws-frames")

			// ── --list-variants ───────────────────────────────────────────
			if listVariants {
				entries, err := os.ReadDir(awsFramesDir)
				if err != nil {
					return fmt.Errorf("read aws-frames dir %s: %w", awsFramesDir, err)
				}
				fmt.Printf("Available variants in %s:\n", awsFramesDir)
				for _, e := range entries {
					if !e.IsDir() {
						continue
					}
					marker := ""
					if e.Name() == defaultVariant {
						marker = "  ← default"
					}
					fmt.Printf("  %s%s\n", e.Name(), marker)
				}
				return nil
			}

			// ── resolve variant subdirectory ──────────────────────────────
			if variantFlag == "" {
				variantFlag = defaultVariant
			}
			srcDir := filepath.Join(awsFramesDir, variantFlag)
			if _, err := os.Stat(srcDir); os.IsNotExist(err) {
				return fmt.Errorf("variant %q not found in %s (use --list-variants to see available variants)",
					variantFlag, awsFramesDir)
			}

			if outputDir == "" {
				outputDir = cfg.OutputFramesDir()
			}
			if err := os.MkdirAll(outputDir, 0755); err != nil {
				return fmt.Errorf("create output dir: %w", err)
			}

			entries, err := os.ReadDir(srcDir)
			if err != nil {
				return fmt.Errorf("read variant dir %s: %w", srcDir, err)
			}

			count := 0
			for _, e := range entries {
				if e.IsDir() || !strings.HasSuffix(e.Name(), ".excalidraw") {
					continue
				}
				// filter by size if specified
				if sizeFlag != "" && !strings.HasPrefix(strings.ToLower(e.Name()), strings.ToLower(sizeFlag)) {
					continue
				}
				src := filepath.Join(srcDir, e.Name())
				dst := filepath.Join(outputDir, e.Name())
				if err := copyFile(src, dst); err != nil {
					return fmt.Errorf("copy %s: %w", e.Name(), err)
				}
				fmt.Printf("  %s\n", e.Name())
				count++
			}
			fmt.Printf("\nDone: %d files → %s\n", count, outputDir)
			return nil
		},
	}

	cmd.Flags().StringVarP(&outputDir, "output", "o", "", "output directory (default: output/aws-frames/)")
	cmd.Flags().StringVar(&sizeFlag, "size", "", "filter by paper size prefix, e.g. A4")
	cmd.Flags().StringVar(&variantFlag, "variant", "", fmt.Sprintf("layout variant (default: %s)", defaultVariant))
	cmd.Flags().BoolVar(&listVariants, "list-variants", false, "list available variants and exit")
	return cmd
}

// initGenerateCatalogCmd creates 'generate catalog'.
//
//	aet generate catalog [--output file]
func initGenerateCatalogCmd() *cobra.Command {
	var outputFile string

	cmd := &cobra.Command{
		Use:   "catalog",
		Short: "Copy the service-catalog template to the output path",
		Long: `Copies service-catalog.excalidraw from etc/resources/templates/ to the output path.

Examples:
  aet generate catalog
  aet generate catalog --output /tmp/my-catalog.excalidraw`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg := config.New()
			if outputFile == "" {
				outputFile = cfg.OutputCatalogFile()
			}

			src := filepath.Join(cfg.TemplatesSourceDir(), "service-catalog.excalidraw")
			if err := os.MkdirAll(filepath.Dir(outputFile), 0755); err != nil {
				return fmt.Errorf("create output dir: %w", err)
			}
			if err := copyFile(src, outputFile); err != nil {
				return fmt.Errorf("copy catalog: %w", err)
			}
			fmt.Printf("Done: %s\n", outputFile)
			return nil
		},
	}

	cmd.Flags().StringVarP(&outputFile, "output", "o", "", "output file path (default: output/service-catalog.excalidraw)")
	return cmd
}

// copyFile copies src to dst, creating dst's parent directories as needed.
func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, in)
	return err
}

