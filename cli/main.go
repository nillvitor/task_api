package main

import (
    "log"
    "os"

    "github.com/urfave/cli/v2"
)

func main() {
    app := &cli.App{
        Name:  "task-cli",
        Usage: "A CLI tool to manage tasks through the Task Management API",
        Commands: []*cli.Command{
            loginCommand(),
            logoutCommand(),
            createTaskCommand(),
            listTasksCommand(),
            getTaskCommand(),
            updateTaskCommand(),
            deleteTaskCommand(),
        },
    }

    if err := app.Run(os.Args); err != nil {
        log.Fatal(err)
    }
}
