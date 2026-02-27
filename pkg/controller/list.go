package controller

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/config"
	"github.com/spf13/cobra"
)

// InitListCmd returns the 'list' parent command.
func InitListCmd() *cobra.Command {
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List available resources",
	}
	listCmd.AddCommand(initListServicesCmd())
	return listCmd
}

func initListServicesCmd() *cobra.Command {
	var (
		category string
		query    string
	)

	cmd := &cobra.Command{
		Use:   "services",
		Short: "List available AWS service icons",
		Long: `Reads service-catalog.csv and prints service names with categories.

Examples:
  aet list services
  aet list services --category Analytics
  aet list services --query lambda`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg := config.New()
			csvPath := cfg.ServiceCatalogCSVPath()

			f, err := os.Open(csvPath)
			if err != nil {
				return fmt.Errorf("open service catalog CSV: %w", err)
			}
			defer f.Close()

			r := csv.NewReader(f)
			// Read and discard header
			if _, err := r.Read(); err != nil {
				return fmt.Errorf("read CSV header: %w", err)
			}

			lowerQuery := strings.ToLower(query)
			lowerCategory := strings.ToLower(category)

			type entry struct {
				cat  string
				name string
			}
			var results []entry

			for {
				rec, err := r.Read()
				if err == io.EOF {
					break
				}
				if err != nil {
					return fmt.Errorf("read CSV: %w", err)
				}
				if len(rec) < 2 {
					continue
				}
				cat, svc := rec[0], rec[1]

				// --category filter
				if lowerCategory != "" && !strings.EqualFold(cat, lowerCategory) {
					continue
				}
				// --query filter
				if lowerQuery != "" && !strings.Contains(strings.ToLower(svc), lowerQuery) {
					continue
				}

				results = append(results, entry{cat: cat, name: svc})
			}

			// Sort by category then service name
			sort.Slice(results, func(i, j int) bool {
				if results[i].cat != results[j].cat {
					return results[i].cat < results[j].cat
				}
				return results[i].name < results[j].name
			})

			for _, e := range results {
				fmt.Printf("%-40s %s\n", e.cat, e.name)
			}
			fmt.Printf("\ntotal: %d\n", len(results))
			return nil
		},
	}

	cmd.Flags().StringVar(&category, "category", "", "filter by category (e.g. Analytics, Compute)")
	cmd.Flags().StringVarP(&query, "query", "q", "", "filter by service name substring (case-insensitive)")
	return cmd
}
