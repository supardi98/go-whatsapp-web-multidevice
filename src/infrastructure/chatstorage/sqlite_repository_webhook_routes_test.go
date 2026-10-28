package chatstorage

import (
	"testing"
	"time"

	domainChatStorage "github.com/aldinokemal/go-whatsapp-web-multidevice/domains/chatstorage"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSQLiteRepositoryWebhookRoutesCRUD(t *testing.T) {
	repo := newTestSQLiteRepository(t)

	// Create a device
	err := repo.SaveDeviceRecord(&domainChatStorage.DeviceRecord{
		DeviceID:    "session-routes",
		DisplayName: "Routes Test Device",
		JID:         "628999999999@s.whatsapp.net",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	})
	require.NoError(t, err)

	// Initially routes should be empty
	routes, err := repo.GetDeviceWebhookRoutes("session-routes")
	require.NoError(t, err)
	assert.Empty(t, routes)

	// Add a route
	route1 := domainChatStorage.WebhookRoute{
		Name:                      "Group Route",
		MatchJID:                  "120363429795720905@g.us",
		WebhookURL:                "https://windmill.example.com/api/w/admins/jobs/run",
		WebhookSecret:             "secret-1",
		WebhookEvents:             "message",
		WebhookInsecureSkipVerify: true,
		CustomHeaders:             map[string]string{"Authorization": "Bearer token123"},
		CustomParams:              map[string]string{"flow": "instagram"},
		Exclusive:                 true,
		Enabled:                   true,
	}

	createdRoute, err := repo.AddDeviceWebhookRoute("session-routes", route1)
	require.NoError(t, err)
	assert.NotEmpty(t, createdRoute.ID)
	assert.Equal(t, "Group Route", createdRoute.Name)
	assert.Equal(t, "120363429795720905@g.us", createdRoute.MatchJID)
	assert.True(t, createdRoute.Exclusive)

	// Retrieve routes
	routes, err = repo.GetDeviceWebhookRoutes("session-routes")
	require.NoError(t, err)
	require.Len(t, routes, 1)
	assert.Equal(t, createdRoute.ID, routes[0].ID)
	assert.Equal(t, "Bearer token123", routes[0].CustomHeaders["Authorization"])
	assert.Equal(t, "instagram", routes[0].CustomParams["flow"])

	// Update the route
	route1Updated := routes[0]
	route1Updated.Name = "Updated Group Route"
	route1Updated.CustomParams["flow"] = "all"

	updated, err := repo.UpdateDeviceWebhookRoute("session-routes", createdRoute.ID, route1Updated)
	require.NoError(t, err)
	assert.Equal(t, "Updated Group Route", updated.Name)
	assert.Equal(t, "all", updated.CustomParams["flow"])

	// Verify persistence in GetDeviceWebhookConfig
	config, err := repo.GetDeviceWebhookConfig("session-routes")
	require.NoError(t, err)
	require.NotNil(t, config)
	require.Len(t, config.WebhookRoutes, 1)
	assert.Equal(t, "Updated Group Route", config.WebhookRoutes[0].Name)

	// Verify persistence in GetDeviceRecordByJID
	record, err := repo.GetDeviceRecordByJID("628999999999@s.whatsapp.net")
	require.NoError(t, err)
	require.NotNil(t, record)
	assert.Contains(t, record.WebhookRoutes, "Updated Group Route")

	// Delete the route
	err = repo.DeleteDeviceWebhookRoute("session-routes", createdRoute.ID)
	require.NoError(t, err)

	routes, err = repo.GetDeviceWebhookRoutes("session-routes")
	require.NoError(t, err)
	assert.Empty(t, routes)
}
