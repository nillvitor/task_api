package config

import (
    "encoding/json"
    "os"
    "path/filepath"
)

type Config struct {
    APIBaseURL  string `json:"api_base_url"`
    AccessToken string `json:"access_token"`
}

const (
    defaultAPIBaseURL = "http://localhost:8000"
    configFileName    = ".task-cli.json"
)

func GetConfig() (*Config, error) {
    homeDir, err := os.UserHomeDir()
    if err != nil {
        return nil, err
    }

    configPath := filepath.Join(homeDir, configFileName)
    config := &Config{
        APIBaseURL: defaultAPIBaseURL,
    }

    if _, err := os.Stat(configPath); os.IsNotExist(err) {
        return config, nil
    }

    data, err := os.ReadFile(configPath)
    if err != nil {
        return nil, err
    }

    if err := json.Unmarshal(data, config); err != nil {
        return nil, err
    }

    return config, nil
}

func SaveConfig(config *Config) error {
    homeDir, err := os.UserHomeDir()
    if err != nil {
        return err
    }

    configPath := filepath.Join(homeDir, configFileName)
    data, err := json.MarshalIndent(config, "", "  ")
    if err != nil {
        return err
    }

    return os.WriteFile(configPath, data, 0600)
}