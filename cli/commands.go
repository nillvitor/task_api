package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "syscall"

    "github.com/urfave/cli/v2"
    "golang.org/x/term"
    "task-cli/config"
    "task-cli/types"
)

func loginCommand() *cli.Command {
    return &cli.Command{
        Name:  "login",
        Usage: "Login to the Task Management API",
        Flags: []cli.Flag{
            &cli.StringFlag{
                Name:     "username",
                Aliases:  []string{"u"},
                Usage:    "Username for authentication",
                Required: true,
            },
            &cli.StringFlag{
                Name:    "password",
                Aliases: []string{"p"},
                Usage:   "Password for authentication (if not provided, will prompt for password)",
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            var password string
            if c.String("password") != "" {
                password = c.String("password")
            } else {
                fmt.Print("Password: ")
                passwordBytes, err := term.ReadPassword(int(syscall.Stdin))
                if err != nil {
                    return fmt.Errorf("error reading password: %v", err)
                }
                fmt.Println() // Adiciona uma nova linha após a senha
                password = string(passwordBytes)
            }

            loginReq := types.LoginRequest{
                Username: c.String("username"),
                Password: password,
            }

            resp, err := http.Post(
                fmt.Sprintf("%s/token", cfg.APIBaseURL),
                "application/x-www-form-urlencoded",
                bytes.NewBuffer([]byte(fmt.Sprintf("username=%s&password=%s", 
                    loginReq.Username, loginReq.Password))),
            )
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("login failed: %s", resp.Status)
            }

            var loginResp types.LoginResponse
            if err := json.NewDecoder(resp.Body).Decode(&loginResp); err != nil {
                return err
            }

            cfg.AccessToken = loginResp.AccessToken
            if err := config.SaveConfig(cfg); err != nil {
                return err
            }

            fmt.Println("Login successful!")
            return nil
        },
    }
}

func createTaskCommand() *cli.Command {
    return &cli.Command{
        Name:  "create",
        Usage: "Create a new task",
        Flags: []cli.Flag{
            &cli.StringFlag{
                Name:     "title",
                Aliases:  []string{"t"},
                Usage:    "Task title",
                Required: true,
            },
            &cli.StringFlag{
                Name:     "description",
                Aliases:  []string{"d"},
                Usage:    "Task description",
                Required: true,
            },
            &cli.StringFlag{
                Name:    "status",
                Aliases: []string{"s"},
                Usage:   "Task status (pending, in_progress, done)",
                Value:   "pending",
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in. Please run 'task-cli login' first")
            }

            task := types.CreateTaskRequest{
                Title:       c.String("title"),
                Description: c.String("description"),
                Status:      c.String("status"),
            }

            data, err := json.Marshal(task)
            if err != nil {
                return err
            }

            req, err := http.NewRequest(
                "POST",
                fmt.Sprintf("%s/tasks", cfg.APIBaseURL),
                bytes.NewBuffer(data),
            )
            if err != nil {
                return err
            }

            req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.AccessToken))
            req.Header.Set("Content-Type", "application/json")

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("failed to create task: %s", resp.Status)
            }

            var createdTask types.Task
            if err := json.NewDecoder(resp.Body).Decode(&createdTask); err != nil {
                return err
            }

            fmt.Printf("Task created successfully! ID: %d\n", createdTask.ID)
            return nil
        },
    }
}

func listTasksCommand() *cli.Command {
    return &cli.Command{
        Name:  "list",
        Usage: "List all tasks",
        Flags: []cli.Flag{
            &cli.IntFlag{
                Name:    "page",
                Aliases: []string{"p"},
                Usage:   "Page number",
                Value:   1,
            },
            &cli.IntFlag{
                Name:    "limit",
                Aliases: []string{"l"},
                Usage:   "Number of tasks per page",
                Value:   10,
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in. Please run 'task-cli login' first")
            }

            skip := (c.Int("page") - 1) * c.Int("limit")
            url := fmt.Sprintf("%s/tasks?skip=%d&limit=%d", cfg.APIBaseURL, skip, c.Int("limit"))

            req, err := http.NewRequest("GET", url, nil)
            if err != nil {
                return err
            }

            req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.AccessToken))

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("failed to list tasks: %s", resp.Status)
            }

            var tasks []types.Task
            if err := json.NewDecoder(resp.Body).Decode(&tasks); err != nil {
                return err
            }

            for _, task := range tasks {
                fmt.Printf("ID: %d\nTitle: %s\nDescription: %s\nStatus: %s\nCreated: %s\nUpdated: %s\n\n",
                    task.ID, task.Title, task.Description, task.Status, task.CreatedAt, task.UpdatedAt)
            }

            return nil
        },
    }
}

func getTaskCommand() *cli.Command {
    return &cli.Command{
        Name:  "get",
        Usage: "Get a specific task by ID",
        Flags: []cli.Flag{
            &cli.IntFlag{
                Name:     "id",
                Aliases:  []string{"i"},
                Usage:    "Task ID",
                Required: true,
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in. Please run 'task-cli login' first")
            }

            req, err := http.NewRequest(
                "GET",
                fmt.Sprintf("%s/tasks/%d", cfg.APIBaseURL, c.Int("id")),
                nil,
            )
            if err != nil {
                return err
            }

            req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.AccessToken))

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("failed to get task: %s", resp.Status)
            }

            var task types.Task
            if err := json.NewDecoder(resp.Body).Decode(&task); err != nil {
                return err
            }

            fmt.Printf("ID: %d\nTitle: %s\nDescription: %s\nStatus: %s\nCreated: %s\nUpdated: %s\n",
                task.ID, task.Title, task.Description, task.Status, task.CreatedAt, task.UpdatedAt)
            return nil
        },
    }
}

func updateTaskCommand() *cli.Command {
    return &cli.Command{
        Name:  "update",
        Usage: "Update an existing task",
        Flags: []cli.Flag{
            &cli.IntFlag{
                Name:     "id",
                Aliases:  []string{"i"},
                Usage:    "Task ID",
                Required: true,
            },
            &cli.StringFlag{
                Name:     "title",
                Aliases:  []string{"t"},
                Usage:    "Task title",
                Required: true,
            },
            &cli.StringFlag{
                Name:     "description",
                Aliases:  []string{"d"},
                Usage:    "Task description",
                Required: true,
            },
            &cli.StringFlag{
                Name:    "status",
                Aliases: []string{"s"},
                Usage:   "Task status (pending, in_progress, done)",
                Value:   "pending",
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in. Please run 'task-cli login' first")
            }

            task := types.UpdateTaskRequest{
                Title:       c.String("title"),
                Description: c.String("description"),
                Status:      c.String("status"),
            }

            data, err := json.Marshal(task)
            if err != nil {
                return err
            }

            req, err := http.NewRequest(
                "PUT",
                fmt.Sprintf("%s/tasks/%d", cfg.APIBaseURL, c.Int("id")),
                bytes.NewBuffer(data),
            )
            if err != nil {
                return err
            }

            req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.AccessToken))
            req.Header.Set("Content-Type", "application/json")

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("failed to update task: %s", resp.Status)
            }

            var updatedTask types.Task
            if err := json.NewDecoder(resp.Body).Decode(&updatedTask); err != nil {
                return err
            }

            fmt.Printf("Task updated successfully! ID: %d\n", updatedTask.ID)
            return nil
        },
    }
}

func deleteTaskCommand() *cli.Command {
    return &cli.Command{
        Name:  "delete",
        Usage: "Delete a task",
        Flags: []cli.Flag{
            &cli.IntFlag{
                Name:     "id",
                Aliases:  []string{"i"},
                Usage:    "Task ID",
                Required: true,
            },
        },
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in. Please run 'task-cli login' first")
            }

            req, err := http.NewRequest(
                "DELETE",
                fmt.Sprintf("%s/tasks/%d", cfg.APIBaseURL, c.Int("id")),
                nil,
            )
            if err != nil {
                return err
            }

            req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.AccessToken))

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                return fmt.Errorf("failed to delete task: %s", resp.Status)
            }

            fmt.Printf("Task deleted successfully!\n")
            return nil
        },
    }
}

func logoutCommand() *cli.Command {
    return &cli.Command{
        Name:  "logout",
        Usage: "Logout from the Task Management API",
        Action: func(c *cli.Context) error {
            cfg, err := config.GetConfig()
            if err != nil {
                return err
            }

            if cfg.AccessToken == "" {
                return fmt.Errorf("not logged in")
            }

            // Limpa o token de acesso
            cfg.AccessToken = ""
            if err := config.SaveConfig(cfg); err != nil {
                return err
            }

            fmt.Println("Logout successful!")
            return nil
        },
    }
}
