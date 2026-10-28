package whatsapp

import (
	"context"
	"encoding/json"
	"testing"

	domainChatStorage "github.com/aldinokemal/go-whatsapp-web-multidevice/domains/chatstorage"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestForwardPayloadToConfiguredWebhooks_RouteMatchingAndExclusive(t *testing.T) {
	ctx := context.Background()
	defaultURL := "https://default-webhook.example.com"
	groupJID := "120363429795720905@g.us"
	deviceJID := "628111111111@s.whatsapp.net"

	route1 := domainChatStorage.WebhookRoute{
		ID:            "route-windmill",
		Name:          "Windmill Agent",
		MatchJID:      groupJID,
		WebhookURL:    "https://windmill.example.com/api/run",
		WebhookSecret: "route-secret-123",
		CustomHeaders: map[string]string{"Authorization": "Bearer secret-token"},
		CustomParams:  map[string]string{"token": "xyz", "type": "wa"},
		Exclusive:     true, // Should suppress default webhook
		Enabled:       true,
	}

	routesJSON, err := json.Marshal([]domainChatStorage.WebhookRoute{route1})
	require.NoError(t, err)

	webhookStorageForTest = func(jid string) (*domainChatStorage.DeviceRecord, error) {
		if jid == deviceJID {
			return &domainChatStorage.DeviceRecord{
				DeviceID:      "device-1",
				JID:           deviceJID,
				WebhookURL:    &defaultURL,
				WebhookSecret: "default-secret",
				WebhookRoutes: string(routesJSON),
			}, nil
		}
		return nil, nil
	}
	defer func() { webhookStorageForTest = nil }()

	originalSubmit := submitWebhookFn
	var submittedURLs []string
	var submittedConfigs []*domainChatStorage.DeviceWebhookConfig
	submitWebhookFn = func(_ context.Context, _ map[string]any, url string, cfg *domainChatStorage.DeviceWebhookConfig) error {
		submittedURLs = append(submittedURLs, url)
		submittedConfigs = append(submittedConfigs, cfg)
		return nil
	}
	defer func() { submitWebhookFn = originalSubmit }()

	// Message from the matching group
	groupPayload := map[string]any{
		"event":     "message",
		"device_id": deviceJID,
		"payload": map[string]any{
			"chat_id": groupJID,
			"from":    "628999999999@s.whatsapp.net",
			"body":    "hello windmill",
		},
	}

	err = forwardPayloadToConfiguredWebhooks(ctx, groupPayload, "message")
	require.NoError(t, err)

	// Since route has Exclusive: true, only the route URL should be called, NOT defaultURL
	require.Len(t, submittedURLs, 1)
	assert.Contains(t, submittedURLs[0], "https://windmill.example.com/api/run?")
	assert.Contains(t, submittedURLs[0], "token=xyz")
	assert.Contains(t, submittedURLs[0], "type=wa")

	// Verify route headers and secret
	require.Len(t, submittedConfigs, 1)
	assert.Equal(t, "Bearer secret-token", submittedConfigs[0].CustomHeaders["Authorization"])
	assert.Equal(t, "route-secret-123", submittedConfigs[0].WebhookSecret)

	// Now send a message from a DIFFERENT chat (private chat)
	submittedURLs = nil
	submittedConfigs = nil
	privatePayload := map[string]any{
		"event":     "message",
		"device_id": deviceJID,
		"payload": map[string]any{
			"chat_id": "628222222222@s.whatsapp.net",
			"from":    "628222222222@s.whatsapp.net",
			"body":    "private msg",
		},
	}

	err = forwardPayloadToConfiguredWebhooks(ctx, privatePayload, "message")
	require.NoError(t, err)

	// Private message does not match group route -> defaultURL must receive it!
	require.Len(t, submittedURLs, 1)
	assert.Equal(t, defaultURL, submittedURLs[0])
	assert.Equal(t, "default-secret", submittedConfigs[0].WebhookSecret)
}

func TestForwardPayloadToConfiguredWebhooks_NonExclusiveRoutes(t *testing.T) {
	ctx := context.Background()
	defaultURL := "https://cryptobit-api.example.com/webhook"
	groupJID := "120363429795720905@g.us"
	deviceJID := "628111111111@s.whatsapp.net"

	route1 := domainChatStorage.WebhookRoute{
		ID:         "route-wm",
		MatchJID:   "@g.us", // Wildcard for all groups
		WebhookURL: "https://windmill.example.com/api/run",
		Exclusive:  false, // Non-exclusive: both default and route receive!
		Enabled:    true,
	}

	routesJSON, err := json.Marshal([]domainChatStorage.WebhookRoute{route1})
	require.NoError(t, err)

	webhookStorageForTest = func(jid string) (*domainChatStorage.DeviceRecord, error) {
		return &domainChatStorage.DeviceRecord{
			DeviceID:      "device-1",
			JID:           deviceJID,
			WebhookURL:    &defaultURL,
			WebhookRoutes: string(routesJSON),
		}, nil
	}
	defer func() { webhookStorageForTest = nil }()

	originalSubmit := submitWebhookFn
	var submittedURLs []string
	submitWebhookFn = func(_ context.Context, _ map[string]any, url string, _ *domainChatStorage.DeviceWebhookConfig) error {
		submittedURLs = append(submittedURLs, url)
		return nil
	}
	defer func() { submitWebhookFn = originalSubmit }()

	groupPayload := map[string]any{
		"event":     "message",
		"device_id": deviceJID,
		"payload": map[string]any{
			"chat_id": groupJID,
			"body":    "test group",
		},
	}

	err = forwardPayloadToConfiguredWebhooks(ctx, groupPayload, "message")
	require.NoError(t, err)

	// Both default webhook and route webhook should have received the payload!
	assert.Len(t, submittedURLs, 2)
	assert.Contains(t, submittedURLs, defaultURL)
	assert.Contains(t, submittedURLs, "https://windmill.example.com/api/run")
}

func TestForwardPayloadToConfiguredWebhooks_RouteEventFiltering(t *testing.T) {
	ctx := context.Background()
	deviceJID := "628111111111@s.whatsapp.net"

	route1 := domainChatStorage.WebhookRoute{
		ID:            "route-msg-only",
		MatchJID:      "*",
		WebhookURL:    "https://events.example.com/messages",
		WebhookEvents: "message", // Only "message", not "message.ack"
		Enabled:       true,
	}

	routesJSON, err := json.Marshal([]domainChatStorage.WebhookRoute{route1})
	require.NoError(t, err)

	webhookStorageForTest = func(jid string) (*domainChatStorage.DeviceRecord, error) {
		return &domainChatStorage.DeviceRecord{
			DeviceID:      "device-1",
			JID:           deviceJID,
			WebhookRoutes: string(routesJSON),
		}, nil
	}
	defer func() { webhookStorageForTest = nil }()

	originalSubmit := submitWebhookFn
	var submittedURLs []string
	submitWebhookFn = func(_ context.Context, _ map[string]any, url string, _ *domainChatStorage.DeviceWebhookConfig) error {
		submittedURLs = append(submittedURLs, url)
		return nil
	}
	defer func() { submitWebhookFn = originalSubmit }()

	// Event "message.ack" should be filtered out by route's event whitelist
	ackPayload := map[string]any{
		"event":     "message.ack",
		"device_id": deviceJID,
		"payload":   map[string]any{"chat_id": "123@s.whatsapp.net"},
	}

	err = forwardPayloadToConfiguredWebhooks(ctx, ackPayload, "message.ack")
	require.NoError(t, err)
	assert.Empty(t, submittedURLs)

	// Event "message" should pass through
	msgPayload := map[string]any{
		"event":     "message",
		"device_id": deviceJID,
		"payload":   map[string]any{"chat_id": "123@s.whatsapp.net"},
	}

	err = forwardPayloadToConfiguredWebhooks(ctx, msgPayload, "message")
	require.NoError(t, err)
	assert.Len(t, submittedURLs, 1)
}

func TestMatchesRouteJID(t *testing.T) {
	tests := []struct {
		name    string
		payload map[string]any
		pattern string
		want    bool
	}{
		{
			name:    "wildcard * matches any",
			payload: map[string]any{"payload": map[string]any{"chat_id": "123@s.whatsapp.net"}},
			pattern: "*",
			want:    true,
		},
		{
			name:    "group wildcard @g.us matches group",
			payload: map[string]any{"payload": map[string]any{"chat_id": "120363429795720905@g.us"}},
			pattern: "@g.us",
			want:    true,
		},
		{
			name:    "group wildcard @g.us does not match private chat",
			payload: map[string]any{"payload": map[string]any{"chat_id": "628123456789@s.whatsapp.net"}},
			pattern: "@g.us",
			want:    false,
		},
		{
			name:    "exact group JID match",
			payload: map[string]any{"payload": map[string]any{"chat_id": "120363429795720905@g.us"}},
			pattern: "120363429795720905@g.us",
			want:    true,
		},
		{
			name:    "exact phone number match",
			payload: map[string]any{"payload": map[string]any{"from": "628123456789@s.whatsapp.net"}},
			pattern: "628123456789",
			want:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.want, matchesRouteJID(tt.payload, tt.pattern))
		})
	}
}
