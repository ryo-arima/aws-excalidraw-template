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
//	aet generate frames [--size A4] [--output dir]
func initGenerateFramesCmd() *cobra.Command {
	var (
		outputDir string
		sizeFlag  string
	)

	cmd := &cobra.Command{
		Use:   "frames",
		Short: "Copy AWS frame templates to the output directory",
		Long: `Copies .excalidraw files from etc/resources/templates/aws-frames/ to the output directory.

Examples:
  aet generate frames
  aet generate frames --size A4
  aet generate frames --output /tmp/my-frames`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg := config.New()
			if outputDir == "" {
				outputDir = cfg.OutputFramesDir()
			}
			srcDir := filepath.Join(cfg.TemplatesSourceDir(), "aws-frames")

			entries, err := os.ReadDir(srcDir)
			if err != nil {
				return fmt.Errorf("read templates dir %s: %w", srcDir, err)
			}

			if err := os.MkdirAll(outputDir, 0755); err != nil {
				return fmt.Errorf("create output dir: %w", err)
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

