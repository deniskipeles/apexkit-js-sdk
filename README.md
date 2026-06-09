# `@apexkit/sdk`

The official JavaScript/TypeScript client SDK for **ApexKit** — the single-node, high-performance Backend-as-a-Service (BaaS) and AI-Architect platform.

This SDK provides a type-safe, lightweight interface to interact with your ApexKit database, authentication, file storage, real-time channels, serverless scripts, and AI vector engines. It automatically manages authentication headers and handles scoping context (Root, Tenant, and Sandbox spaces) behind the scenes.

---

## Installation

Install the package via your preferred package manager:

```bash
npm install @apexkit/sdk
```

---

## Initialization

Initialize the client pointed at your ApexKit server instance.

```typescript
import { ApexKit } from '@apexkit/sdk';

// 1. Root Client (Primary Admin/System Scope)
const client = new ApexKit('https://api.yourdomain.com');

// 2. Tenant Client (Scoped to a specific Multi-Tenant boundary)
const tenantClient = client.tenant('customer-tenant-id');

// 3. Sandbox Client (Scoped to an isolated development Sandbox session)
const sandboxClient = client.sandbox('sandbox-session-id');
```

---

## Authentication

The SDK automatically caches the JWT token in memory upon a successful login and attaches the correct `Authorization: Bearer <token>` headers to all subsequent requests.

### Email and Password

```typescript
// Register a new user
const registration = await client.auth.register('user@example.com', 'password123');

// Login to acquire a JWT
const session = await client.auth.login('user@example.com', 'password123');
console.log('User Profile:', session.user);
console.log('Authentication Scope:', session.user.scope);

// Fetch current logged-in profile
const me = await client.auth.getMe();

// Logout (Clears internal token cache)
client.auth.logout();
```

### Password Recovery & Verification

```typescript
// Request password reset link (Requires SMTP config)
await client.auth.requestPasswordReset('user@example.com');

// Confirm password reset using the token from the email link
await client.auth.confirmPasswordReset('secure-uuid-token', 'new_secure_password');

// Confirm email verification from the link
// (Handled automatically on GET redirect, or manual API call)
await fetch(`${client.baseUrl}/api/v1/auth/verify?token=secure-uuid-token`);
```

### Third-Party OAuth

Redirect your users to social sign-in providers. Once completed, they will be redirected back to your callback URL with the JWT token appended.

```typescript
// Redirect to Google Consent Screen
client.auth.loginWithGoogle('https://myapp.com/auth-callback');

// Redirect to GitHub Consent Screen
client.auth.loginWithGithub('https://myapp.com/auth-callback');
```

---

## Database Operations (CRUD)

All record operations are scoped per collection.

### Fetch & Paginate Records

```typescript
const postsCollection = client.collection('posts');

const result = await postsCollection.list({
  page: 1,
  per_page: 20,
  sort: '-created', // Sort descending by creation timestamp
  filter: {
    status: 'published',
    category: 'engineering'
  },
  expand: 'author_id,category_id' // Auto-fetch and expand foreign keys
});

console.log('Matching Records:', result.items);
console.log('Total Count:', result.total);
```

### Create, Update, Delete

```typescript
// Get a single record
const record = await client.collection('posts').get('record_id_123');

// Create a record
const newRecord = await client.collection('posts').create({
  title: 'My First Post',
  status: 'published',
  views: 0
});

// Update a record (Partial patch or full update)
const updatedRecord = await client.collection('posts').update(newRecord.id, {
  title: 'My Updated First Post'
});

// Delete a record
await client.collection('posts').delete(newRecord.id);
```

### Advanced SQL Query Engine

ApexKit features an advanced, schema-aware SQL Query pipeline. Send complex aggregation queries directly from the SDK.

```typescript
// Aggregate total revenue grouped by month
const report = await client.collection('orders').searchRecordsWithSQLQueryEngine({
  select: [
    { expr: "strftime('%Y-%m', created)", as: "month" },
    { func: "sum", field: "amount", as: "total_revenue" },
    { func: "count", field: "*", as: "order_count" }
  ],
  filter: { status: "completed" },
  group_by: ["month"],
  sort: "month"
});

console.log(report); // [{ month: "2026-06", total_revenue: 14500.50, order_count: 145 }]
```

---

## Realtime Streams

ApexKit supports lightweight, high-performance subscription channels over both **WebSockets** and **Server-Sent Events (SSE)**. Realtime events are automatically authorized against database collection rules.

### WebSocket Client

Supports receiving database changes, sending custom client-to-client signals, and conducting instant OSE searches.

```typescript
import { ApexKitRealtimeWSClient } from '@apexkit/sdk';

// Initialize the WebSocket client with the base URL and active token
const realtime = new ApexKitRealtimeWSClient(client.baseUrl, client.getToken());
realtime.connect();

// 1. Subscribe to Database events on a specific collection
realtime.subscribe({
  collectionId: 5,
  eventType: 'Insert', // Optionals: "Insert", "Update", "Delete"
  dataFilter: { status: 'published' } // Optional: inline logical filtering
});

// 2. Subscribe to Custom Ephemeral Channels (e.g. Chat or Presence)
realtime.subscribe({
  channel: 'lobby_room',
  customEvent: 'UserTyping' // Filter only specific custom event types
});

// 3. Send a Custom Client-to-Client Signal (Bypasses DB writes)
realtime.sendSignal('lobby_room', 'UserTyping', { user: 'Alice' });

// 4. Handle incoming stream events
const unsubscribe = realtime.onEvent((msg) => {
  if (msg.type === 'Insert') {
    console.log('Record inserted:', msg.payload.data);
  }
  if (msg.type === 'Custom') {
    console.log(`[${msg.payload.event}]`, msg.payload.data);
  }
});
```

### SSE (Server-Sent Events) Client

Best for read-only events (like live activity logs or data feeds).

```typescript
import { ApexKitRealtimeSSEClient } from '@apexkit/sdk';

const sse = new ApexKitRealtimeSSEClient(client.baseUrl, client.getToken());

// Establish connection
sse.connect({
  channel: 'dashboard_feed',
  eventName: 'SystemAlert' // Optional filter
});

sse.onEvent((event) => {
  console.log('Alert received:', event.payload.data);
});
```

---

## File Storage

```typescript
const fileInput = document.getElementById('file-upload') as HTMLInputElement;
const file = fileInput.files?.[0];

if (file) {
  // 1. Upload File
  const uploaded = await client.files.upload(file);
  console.log('Filename on server:', uploaded.name);

  // 2. Resolve public URL
  const publicUrl = client.files.getFileUrl(uploaded.name);
  console.log('Public URL:', publicUrl);

  // 3. Generate a secure, pre-signed URL (For private buckets, expires in 1 hour)
  const signedUrl = await client.files.getSignedUrl(uploaded.name, 3600);
}
```

---

## AI Actions

AI Actions allow you to run complex, pre-defined LLM prompt templates (configured in the Admin Dashboard) without exposing sensitive Gemini or OpenAI API keys to your client code.

```typescript
// Trigger a pre-configured AI Action (slug: "translate-text")
const response = await client.ai.run('translate-text', {
  text: "Hello, how are you today?",
  target_language: "French"
});

console.log('AI Output:', response.result);

// Inspect Google Search Grounding Metadata (if enabled in settings)
if (response.metadata) {
  console.log('Sources cited by AI:', response.metadata.groundingChunks);
}
```

---

## Server Scripts

Run custom, server-side JavaScript endpoints securely.

```typescript
// Runs an active manual script (identifier: "calculate-invoice")
const result = await client.scripts.run('calculate-invoice', {
  subtotal: 1500,
  tax_rate: 0.15,
  coupon_code: "SUMMER10"
});

console.log('Calculated Result:', result);
```

---

## License

This SDK is MIT licensed. Feel free to use, modify, and distribute it for open-source and commercial applications.
