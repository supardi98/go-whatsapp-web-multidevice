package rest

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/aldinokemal/go-whatsapp-web-multidevice/domains/chatstorage"
	domainDevice "github.com/aldinokemal/go-whatsapp-web-multidevice/domains/device"
	"github.com/aldinokemal/go-whatsapp-web-multidevice/pkg/utils"
	"github.com/aldinokemal/go-whatsapp-web-multidevice/ui/rest/middleware"
	"github.com/gofiber/fiber/v3"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type webhookRoutesStubUsecase struct {
	domainDevice.IDeviceUsecase
	routes []chatstorage.WebhookRoute
	config *chatstorage.DeviceWebhookConfig
}

func (s *webhookRoutesStubUsecase) GetDeviceWebhookRoutes(_ context.Context, _ string) ([]chatstorage.WebhookRoute, error) {
	return s.routes, nil
}

func (s *webhookRoutesStubUsecase) AddDeviceWebhookRoute(_ context.Context, _ string, route chatstorage.WebhookRoute) (*chatstorage.WebhookRoute, error) {
	if route.ID == "" {
		route.ID = "generated-route-id"
	}
	s.routes = append(s.routes, route)
	return &route, nil
}

func (s *webhookRoutesStubUsecase) UpdateDeviceWebhookRoute(_ context.Context, _ string, routeID string, route chatstorage.WebhookRoute) (*chatstorage.WebhookRoute, error) {
	route.ID = routeID
	for i, r := range s.routes {
		if r.ID == routeID {
			s.routes[i] = route
			return &route, nil
		}
	}
	s.routes = append(s.routes, route)
	return &route, nil
}

func (s *webhookRoutesStubUsecase) DeleteDeviceWebhookRoute(_ context.Context, _ string, routeID string) error {
	newRoutes := make([]chatstorage.WebhookRoute, 0, len(s.routes))
	for _, r := range s.routes {
		if r.ID != routeID {
			newRoutes = append(newRoutes, r)
		}
	}
	s.routes = newRoutes
	return nil
}

func (s *webhookRoutesStubUsecase) GetDeviceWebhookConfig(_ context.Context, _ string) (*chatstorage.DeviceWebhookConfig, error) {
	return s.config, nil
}

func (s *webhookRoutesStubUsecase) SetDeviceWebhookConfig(_ context.Context, _ string, cfg *chatstorage.DeviceWebhookConfig) error {
	s.config = cfg
	return nil
}

func newWebhookRoutesTestApp(stub *webhookRoutesStubUsecase) *fiber.App {
	app := fiber.New()
	app.Use(middleware.Recovery())
	InitRestDevice(app, stub)
	return app
}

func TestDeviceWebhookRoutesRESTEndpoints(t *testing.T) {
	stub := &webhookRoutesStubUsecase{}
	app := newWebhookRoutesTestApp(stub)

	// 1. GET routes initially empty
	req := httptest.NewRequest(http.MethodGet, "/devices/dev1/webhook/routes", nil)
	resp, err := app.Test(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	// 2. POST route
	newRouteBody := `{
		"name": "Windmill Monitor",
		"match_jid": "120363429795720905@g.us",
		"webhook_url": "https://windmill.example.com/api/run",
		"custom_headers": {"Authorization": "Bearer secret"},
		"custom_params": {"token": "wm123"},
		"exclusive": true,
		"enabled": true
	}`
	req = httptest.NewRequest(http.MethodPost, "/devices/dev1/webhook/routes", strings.NewReader(newRouteBody))
	req.Header.Set("Content-Type", "application/json")
	resp, err = app.Test(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusCreated, resp.StatusCode)

	bodyBytes, _ := io.ReadAll(resp.Body)
	var respData utils.ResponseData
	err = json.Unmarshal(bodyBytes, &respData)
	require.NoError(t, err)
	assert.Equal(t, "SUCCESS", respData.Code)

	// 3. GET routes has 1 route
	req = httptest.NewRequest(http.MethodGet, "/devices/dev1/webhook/routes", nil)
	resp, err = app.Test(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Len(t, stub.routes, 1)

	// 4. PUT route
	updateRouteBody := `{
		"name": "Windmill Monitor Updated",
		"match_jid": "120363429795720905@g.us",
		"webhook_url": "https://windmill.example.com/api/run-updated",
		"enabled": true
	}`
	req = httptest.NewRequest(http.MethodPut, "/devices/dev1/webhook/routes/generated-route-id", strings.NewReader(updateRouteBody))
	req.Header.Set("Content-Type", "application/json")
	resp, err = app.Test(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "Windmill Monitor Updated", stub.routes[0].Name)

	// 5. DELETE route
	req = httptest.NewRequest(http.MethodDelete, "/devices/dev1/webhook/routes/generated-route-id", nil)
	resp, err = app.Test(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Empty(t, stub.routes)
}
