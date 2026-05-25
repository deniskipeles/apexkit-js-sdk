package apexkit

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"strings"
)

type ApexKit struct {
	BaseURL     string
	Token       string
	CurrentUser *User
	ScopeType   string
	ScopeID     string
	httpClient  *http.Client
}

func NewApexKit(baseURL string) *ApexKit {
	return &ApexKit{
		BaseURL:    strings.TrimSuffix(baseURL, "/"),
		ScopeType:  "root",
		httpClient: &http.Client{},
	}
}

func (a *ApexKit) Sandbox(uuid string) *ApexKit {
	instance := NewApexKit(fmt.Sprintf("%s/sandbox/%s", a.BaseURL, uuid))
	instance.ScopeType = "sandbox"
	instance.ScopeID = uuid
	instance.Token = a.Token
	instance.CurrentUser = a.CurrentUser
	return instance
}

func (a *ApexKit) Tenant(tenantID string) *ApexKit {
	instance := NewApexKit(fmt.Sprintf("%s/tenant/%s", a.BaseURL, tenantID))
	instance.ScopeType = "tenant"
	instance.ScopeID = tenantID
	instance.Token = a.Token
	instance.CurrentUser = a.CurrentUser
	return instance
}

func (a *ApexKit) SetToken(token string, user *User) {
	a.Token = token
	if user != nil {
		a.CurrentUser = user
		if user.Scope != "" {
			a.setScopeFromTag(user.Scope)
		}
	}
}

func (a *ApexKit) setScopeFromTag(tag string) {
	if tag == "root" {
		a.ScopeType = "root"
		a.ScopeID = ""
	} else if strings.HasPrefix(tag, "tenant:") {
		a.ScopeType = "tenant"
		a.ScopeID = strings.TrimPrefix(tag, "tenant:")
	} else if strings.HasPrefix(tag, "sandbox:") {
		a.ScopeType = "sandbox"
		a.ScopeID = strings.TrimPrefix(tag, "sandbox:")
	}
}

func (a *ApexKit) request(method, endpoint string, body interface{}, params url.Values, isRoot bool) ([]byte, error) {
	path := endpoint
	if !isRoot && !strings.HasPrefix(endpoint, "/api/v1") {
		path = "/api/v1/" + strings.TrimPrefix(endpoint, "/")
	}

	fullURL := a.BaseURL + path
	if len(params) > 0 {
		fullURL += "?" + params.Encode()
	}

	var bodyReader io.Reader
	if body != nil {
		if reader, ok := body.(io.Reader); ok {
			bodyReader = reader
		} else {
			jsonBody, err := json.Marshal(body)
			if err != nil {
				return nil, err
			}
			bodyReader = bytes.NewBuffer(jsonBody)
		}
	}

	req, err := http.NewRequest(method, fullURL, bodyReader)
	if err != nil {
		return nil, err
	}

	if a.Token != "" {
		req.Header.Set("Authorization", "Bearer "+a.Token)
	}
	if body != nil && bodyReader != nil {
		if _, ok := body.(io.Reader); !ok {
			req.Header.Set("Content-Type", "application/json")
		}
	}

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode == http.StatusNoContent {
		return nil, nil
	}

	if resp.StatusCode >= 400 {
		var apexErr ApexError
		if err := json.Unmarshal(respBody, &apexErr); err != nil {
			return nil, &ApexError{Message: string(respBody), Status: resp.StatusCode}
		}
		apexErr.Status = resp.StatusCode
		return nil, &apexErr
	}

	return respBody, nil
}

// Namespaces

type AuthNamespace struct{ client *ApexKit }
func (a *ApexKit) Auth() *AuthNamespace { return &AuthNamespace{client: a} }

func (n *AuthNamespace) ListRoles() (map[string][]string, error) {
	resp, err := n.client.request("GET", "/auth/roles", nil, nil, false)
	if err != nil { return nil, err }
	var res map[string][]string
	err = json.Unmarshal(resp, &res)
	return res, err
}

func (n *AuthNamespace) Login(email, password string) (*AuthResponse, error) {
	body := map[string]string{"email": email, "password": password}
	resp, err := n.client.request("POST", "/auth/login", body, nil, false)
	if err != nil { return nil, err }
	var res AuthResponse
	if err := json.Unmarshal(resp, &res); err != nil { return nil, err }
	n.client.SetToken(res.Token, &res.User)
	return &res, nil
}

func (n *AuthNamespace) Register(email, password string) (*AuthResponse, error) {
	body := map[string]string{"email": email, "password": password}
	resp, err := n.client.request("POST", "/auth/register", body, nil, false)
	if err != nil { return nil, err }
	var res AuthResponse
	if err := json.Unmarshal(resp, &res); err != nil { return nil, err }
	n.client.SetToken(res.Token, &res.User)
	return &res, nil
}

func (n *AuthNamespace) GetMe() (*User, error) {
	resp, err := n.client.request("GET", "/auth/me", nil, nil, false)
	if err != nil { return nil, err }
	var res User
	if err := json.Unmarshal(resp, &res); err != nil { return nil, err }
	if res.Scope != "" { n.client.setScopeFromTag(res.Scope) }
	return &res, nil
}

func (n *AuthNamespace) Logout() {
	n.client.Token = ""
	n.client.CurrentUser = nil
}

func (n *AuthNamespace) LoginWithGithub(redirectTo string) string {
	u, _ := url.Parse(n.client.BaseURL + "/api/v1/auth/github")
	if redirectTo != "" {
		q := u.Query()
		q.Set("redirect_to", redirectTo)
		u.RawQuery = q.Encode()
	}
	return u.String()
}

func (n *AuthNamespace) LoginWithGoogle(redirectTo string) string {
	u, _ := url.Parse(n.client.BaseURL + "/api/v1/auth/google")
	if redirectTo != "" {
		q := u.Query()
		q.Set("redirect_to", redirectTo)
		u.RawQuery = q.Encode()
	}
	return u.String()
}

type CollectionNamespace struct {
	client *ApexKit
	id     string
}
func (a *ApexKit) Collection(id string) *CollectionNamespace { return &CollectionNamespace{client: a, id: id} }

func (n *CollectionNamespace) List(options url.Values) (*ListResult, error) {
	resp, err := n.client.request("GET", fmt.Sprintf("/collections/%s/records", n.id), nil, options, false)
	if err != nil { return nil, err }
	var res ListResult
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *CollectionNamespace) Create(data interface{}) (*BaseRecord, error) {
	body := map[string]interface{}{"data": data}
	resp, err := n.client.request("POST", fmt.Sprintf("/collections/%s/records", n.id), body, nil, false)
	if err != nil { return nil, err }
	var res BaseRecord
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *CollectionNamespace) Get(recordID string, options url.Values) (*BaseRecord, error) {
	resp, err := n.client.request("GET", fmt.Sprintf("/collections/%s/records/%s", n.id, recordID), nil, options, false)
	if err != nil { return nil, err }
	var res BaseRecord
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *CollectionNamespace) Update(recordID string, data interface{}) (*BaseRecord, error) {
	body := map[string]interface{}{"data": data}
	resp, err := n.client.request("PUT", fmt.Sprintf("/collections/%s/records/%s", n.id, recordID), body, nil, false)
	if err != nil { return nil, err }
	var res BaseRecord
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *CollectionNamespace) Patch(recordID string, data interface{}) (*BaseRecord, error) {
	body := map[string]interface{}{"data": data}
	resp, err := n.client.request("PATCH", fmt.Sprintf("/collections/%s/records/%s", n.id, recordID), body, nil, false)
	if err != nil { return nil, err }
	var res BaseRecord
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *CollectionNamespace) Delete(recordID string) error {
	_, err := n.client.request("DELETE", fmt.Sprintf("/collections/%s/records/%s", n.id, recordID), nil, nil, false)
	return err
}

type AdminsNamespace struct{ client *ApexKit }
func (a *ApexKit) Admins() *AdminsNamespace { return &AdminsNamespace{client: a} }

func (n *AdminsNamespace) ListCollections() ([]Collection, error) {
	resp, err := n.client.request("GET", "/collections", nil, nil, false)
	if err != nil { return nil, err }
	var res []Collection
	err = json.Unmarshal(resp, &res)
	return res, err
}

func (n *AdminsNamespace) CreateCollection(name string, schema interface{}) (*Collection, error) {
	body := map[string]interface{}{"name": name, "schema": schema}
	resp, err := n.client.request("POST", "/collections", body, nil, false)
	if err != nil { return nil, err }
	var res Collection
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *AdminsNamespace) GetCollection(id string) (*Collection, error) {
	resp, err := n.client.request("GET", fmt.Sprintf("/collections/%s", id), nil, nil, false)
	if err != nil { return nil, err }
	var res Collection
	err = json.Unmarshal(resp, &res)
	return &res, err
}

func (n *AdminsNamespace) DeleteCollection(id string) error {
	_, err := n.client.request("DELETE", fmt.Sprintf("/collections/%s", id), nil, nil, false)
	return err
}

func (n *AdminsNamespace) ListUsers(options url.Values) (*ListResult, error) {
	resp, err := n.client.request("GET", "/admin/users", nil, options, false)
	if err != nil { return nil, err }
	var res ListResult
	err = json.Unmarshal(resp, &res)
	return &res, err
}

type AiNamespace struct{ client *ApexKit }
func (a *ApexKit) AI() *AiNamespace { return &AiNamespace{client: a} }

func (n *AiNamespace) Run(slug string, variables map[string]interface{}) (map[string]interface{}, error) {
	body := map[string]interface{}{"variables": variables}
	resp, err := n.client.request("POST", fmt.Sprintf("/ai/run/%s", slug), body, nil, false)
	if err != nil { return nil, err }
	var res map[string]interface{}
	err = json.Unmarshal(resp, &res)
	return res, err
}

type ScriptsNamespace struct{ client *ApexKit }
func (a *ApexKit) Scripts() *ScriptsNamespace { return &ScriptsNamespace{client: a} }

func (n *ScriptsNamespace) Run(name string, variables interface{}) (interface{}, error) {
	resp, err := n.client.request("POST", fmt.Sprintf("/run/%s", name), variables, nil, false)
	if err != nil { return nil, err }
	var res interface{}
	err = json.Unmarshal(resp, &res)
	return res, err
}

func (a *ApexKit) GraphQL(query string, variables map[string]interface{}) (map[string]interface{}, error) {
	body := map[string]interface{}{"query": query, "variables": variables}
	resp, err := a.request("POST", "/graphql", body, nil, true)
	if err != nil { return nil, err }
	var res map[string]interface{}
	err = json.Unmarshal(resp, &res)
	return res, err
}

func (a *ApexKit) UploadFile(filename string, content io.Reader) (*StoredFile, error) {
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, err := writer.CreateFormFile("file", filename)
	if err != nil { return nil, err }
	_, err = io.Copy(part, content)
	if err != nil { return nil, err }
	writer.Close()

	path := "/api/v1/storage/upload"
	fullURL := a.BaseURL + path
	req, err := http.NewRequest("POST", fullURL, body)
	if err != nil { return nil, err }
	req.Header.Set("Content-Type", writer.FormDataContentType())
	if a.Token != "" { req.Header.Set("Authorization", "Bearer "+a.Token) }

	resp, err := a.httpClient.Do(req)
	if err != nil { return nil, err }
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)
	var res StoredFile
	err = json.Unmarshal(respBody, &res)
	return &res, err
}
