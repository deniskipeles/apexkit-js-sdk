package apexkit

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type SubscriptionFilter struct {
	CollectionID int                    `json:"collection_id,omitempty"`
	RecordID     int                    `json:"record_id,omitempty"`
	EventType    string                 `json:"event_type,omitempty"`
	DataFilter   map[string]interface{} `json:"filter,omitempty"`
	Channel      string                 `json:"channel,omitempty"`
	CustomEvent  string                 `json:"custom_event,omitempty"`
}

type ApexKitRealtimeWSClient struct {
	URL               string
	Token             string
	Conn              *websocket.Conn
	mu                sync.Mutex
	listeners         []func(msg interface{})
	isConnected       bool
	currentFilter     *SubscriptionFilter
	reconnectInterval time.Duration
}

func NewRealtimeWSClient(baseURL, token string) *ApexKitRealtimeWSClient {
	wsURL := strings.Replace(baseURL, "http", "ws", 1) + "/ws"
	return &ApexKitRealtimeWSClient{
		URL:               wsURL,
		Token:             token,
		reconnectInterval: 3 * time.Second,
	}
}

func (c *ApexKitRealtimeWSClient) Connect() {
	go func() {
		for {
			err := c.connect()
			if err != nil {
				log.Printf("[ApexKit] Connection failed: %v. Retrying in %v...", err, c.reconnectInterval)
				time.Sleep(c.reconnectInterval)
				continue
			}
			break
		}
	}()
}

func (c *ApexKitRealtimeWSClient) connect() error {
	dialer := websocket.DefaultDialer
	conn, _, err := dialer.Dial(c.URL, nil)
	if err != nil {
		return err
	}

	c.mu.Lock()
	c.Conn = conn
	c.isConnected = true
	c.mu.Unlock()

	log.Println("[ApexKit] Realtime Connected")

	if c.currentFilter != nil {
		c.Subscribe(*c.currentFilter)
	}

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			c.mu.Lock()
			c.isConnected = false
			c.mu.Unlock()
			return err
		}

		var msg interface{}
		if err := json.Unmarshal(message, &msg); err != nil {
			if string(message) == "Pong" {
				continue
			}
			log.Printf("WS Parse Error: %v", err)
			continue
		}

		c.notify(msg)
	}
}

func (c *ApexKitRealtimeWSClient) Subscribe(filter SubscriptionFilter) error {
	c.mu.Lock()
	c.currentFilter = &filter
	conn := c.Conn
	connected := c.isConnected
	c.mu.Unlock()

	if !connected || conn == nil {
		return fmt.Errorf("not connected")
	}

	msg := map[string]interface{}{
		"type":    "Subscribe",
		"payload": filter,
	}
	return conn.WriteJSON(msg)
}

func (c *ApexKitRealtimeWSClient) SendSignal(channel, eventName string, data interface{}) error {
	c.mu.Lock()
	conn := c.Conn
	connected := c.isConnected
	c.mu.Unlock()

	if !connected || conn == nil {
		return fmt.Errorf("not connected")
	}

	msg := map[string]interface{}{
		"type": "Signal",
		"payload": map[string]interface{}{
			"channel": channel,
			"event":   eventName,
			"data":    data,
		},
	}
	return conn.WriteJSON(msg)
}

func (c *ApexKitRealtimeWSClient) OnEvent(listener func(msg interface{})) func() {
	c.mu.Lock()
	c.listeners = append(c.listeners, listener)
	c.mu.Unlock()

	return func() {
		c.mu.Lock()
		defer c.mu.Unlock()
		for i, l := range c.listeners {
			if fmt.Sprintf("%p", l) == fmt.Sprintf("%p", listener) {
				c.listeners = append(c.listeners[:i], c.listeners[i+1:]...)
				break
			}
		}
	}
}

func (c *ApexKitRealtimeWSClient) notify(msg interface{}) {
	c.mu.Lock()
	defer c.mu.Unlock()
	for _, l := range c.listeners {
		l(msg)
	}
}
