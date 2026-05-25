# ApexKit Go SDK

A Go client for the ApexKit API.

## Installation

```bash
go get github.com/apexkit/apexkit-go/apexkit
```

## Usage

```go
package main

import (
	"fmt"
	"log"
	"github.com/apexkit/apexkit-go/apexkit"
)

func main() {
	client := apexkit.NewApexKit("http://localhost:5000")

	// Login
	auth, err := client.Auth().Login("admin@example.com", "password")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Logged in as %s\n", auth.User.Email)

	// List Collections
	collections, err := client.Admins().ListCollections()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Collections: %v\n", collections)
}
```

## Realtime

```go
realtime := apexkit.NewRealtimeWSClient("http://localhost:5000", token)
realtime.OnEvent(func(msg interface{}) {
    fmt.Printf("Event: %v\n", msg)
})
realtime.Connect()
```
