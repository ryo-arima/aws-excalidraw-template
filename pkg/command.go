package command

import (
	"fmt"
	"os"

	"github.com/ryo-arima/aws-excalidraw-template/pkg/controller"
	"github.com/spf13/cobra"
)

// NewRootCmd builds the root CLI command and wires subcommands.
func NewRootCmd() *cobra.Command {
	root := &cobra.Command{
		Use:   "aet",
		Short: "AWS Excalidraw Template CLI",
		Long:  "Generate and manage AWS architecture diagrams with Excalidraw.",
	}

	root.AddCommand(controller.InitGenerateCmd())
	root.AddCommand(controller.InitAddCmd())
	root.AddCommand(controller.InitListCmd())
	return root
}

// Execute runs the CLI.
func Execute() {
	if err := NewRootCmd().Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
