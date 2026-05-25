package apexkit

import "time"

type Scope struct {
	Type string `json:"type"`
	ID   string `json:"id"`
}

type User struct {
	ID         string                 `json:"id"`
	Email      string                 `json:"email"`
	Role       string                 `json:"role"`
	Scope      string                 `json:"scope"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	LastActive string                 `json:"last_active,omitempty"`
}

type AuthResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

type BaseRecord struct {
	ID      string                 `json:"id"`
	Created string                 `json:"created"`
	Updated string                 `json:"updated"`
	Data    map[string]interface{} `json:"data"`
	Expand  map[string]interface{} `json:"expand"`
}

type ListResult struct {
	Items   []interface{} `json:"items"`
	Total   int           `json:"total"`
	Page    int           `json:"page,omitempty"`
	PerPage int           `json:"per_page,omitempty"`
}

type SchemaField struct {
	Name     string                 `json:"name"`
	Type     string                 `json:"type"`
	Required bool                   `json:"required"`
	Unique   bool                   `json:"unique,omitempty"`
	Options  []string               `json:"options,omitempty"`
	Extra    map[string]interface{} `json:"-"`
}

type Collection struct {
	ID      string                 `json:"id"`
	Name    string                 `json:"name"`
	Type    string                 `json:"type"`
	Schema  map[string]interface{} `json:"schema"`
	Created string                 `json:"created"`
	Updated string                 `json:"updated"`
}

type StoredFile struct {
	ID           string `json:"id"`
	Filename     string `json:"filename"`
	OriginalName string `json:"original_name"`
	MimeType     string `json:"mime_type"`
	Size         int64  `json:"size"`
	URL          string `json:"url"`
	CreatedAt    string `json:"created_at"`
}

type InstantResult struct {
	ID      int                    `json:"id"`
	Score   float64                `json:"score"`
	Snippet map[string]interface{} `json:"snippet"`
}

type Script struct {
	ID               string `json:"id"`
	Name             string `json:"name"`
	TriggerType      string `json:"trigger_type"`
	Code             string `json:"code"`
	Active           bool   `json:"active"`
	TargetCollection string `json:"target_collection,omitempty"`
}

type Template struct {
	ID       string `json:"id"`
	Slug     string `json:"slug"`
	Content  string `json:"content"`
	ScriptID string `json:"script_id,omitempty"`
}

type AiAction struct {
	ID           string      `json:"id"`
	Slug         string      `json:"slug"`
	Name         string      `json:"name"`
	Model        string      `json:"model"`
	SystemPrompt string      `json:"system_prompt,omitempty"`
	Template     string      `json:"template"`
	Config       interface{} `json:"config,omitempty"`
}

type AiSession struct {
	ID              string                   `json:"id"`
	Name            string                   `json:"name"`
	Messages        []map[string]string      `json:"messages"`
	CurrentManifest interface{}              `json:"current_manifest,omitempty"`
	DiffSummary     string                   `json:"diff_summary,omitempty"`
	LastError       string                   `json:"last_error,omitempty"`
	CreatedAt       time.Time                `json:"created_at"`
}

type Plugin struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Version     string      `json:"version"`
	Description string      `json:"description,omitempty"`
	Manifest    interface{} `json:"manifest"`
	CreatedAt   time.Time   `json:"created_at"`
}

type ApiKey struct {
	ID         string    `json:"id"`
	Name       string    `json:"name"`
	Prefix     string    `json:"prefix"`
	Role       string    `json:"role"`
	Scope      string    `json:"scope"`
	BypassCors bool      `json:"bypass_cors"`
	CreatedAt  time.Time `json:"created_at"`
}

type SystemLog struct {
	ID        string      `json:"id"`
	Level     string      `json:"level"` // info, warning, error, success
	Message   string      `json:"message"`
	Source    string      `json:"source"`
	Timestamp string      `json:"timestamp"`
	Meta      interface{} `json:"meta,omitempty"`
}

type SiteFile struct {
	Path string `json:"path"`
	Size int64  `json:"size"`
}

type ApexError struct {
	Message string      `json:"message"`
	Status  int         `json:"status"`
	Code    string      `json:"code,omitempty"`
	Details interface{} `json:"details,omitempty"`
}

func (e *ApexError) Error() string {
	return e.Message
}
