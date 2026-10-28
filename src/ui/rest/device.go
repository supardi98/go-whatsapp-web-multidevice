package rest

import (
	"fmt"
	"strings"

	"github.com/aldinokemal/go-whatsapp-web-multidevice/config"
	"github.com/aldinokemal/go-whatsapp-web-multidevice/domains/chatstorage"
	"github.com/aldinokemal/go-whatsapp-web-multidevice/domains/device"
	"github.com/aldinokemal/go-whatsapp-web-multidevice/pkg/utils"
	"github.com/gofiber/fiber/v3"
)

type Device struct {
	Service device.IDeviceUsecase
}

func InitRestDevice(app fiber.Router, service device.IDeviceUsecase) Device {
	rest := Device{Service: service}

	app.Get("/devices", rest.ListDevices)
	app.Post("/devices", rest.AddDevice)

	app.Get("/devices/:device_id", rest.GetDevice)
	app.Delete("/devices/:device_id", rest.RemoveDevice)

	app.Get("/devices/:device_id/login", rest.LoginDevice)
	app.Post("/devices/:device_id/login/code", rest.LoginDeviceWithCode)
	app.Post("/devices/:device_id/logout", rest.LogoutDevice)
	app.Post("/devices/:device_id/reconnect", rest.ReconnectDevice)
	app.Get("/devices/:device_id/status", rest.Status)
	app.Patch("/devices/:device_id/webhook", rest.UpdateDeviceWebhook)
	app.Get("/devices/:device_id/webhook", rest.GetDeviceWebhook)
	app.Get("/devices/:device_id/webhook/routes", rest.ListDeviceWebhookRoutes)
	app.Post("/devices/:device_id/webhook/routes", rest.AddDeviceWebhookRoute)
	app.Put("/devices/:device_id/webhook/routes/:route_id", rest.UpdateDeviceWebhookRoute)
	app.Delete("/devices/:device_id/webhook/routes/:route_id", rest.DeleteDeviceWebhookRoute)

	return rest
}

func (handler *Device) ListDevices(c fiber.Ctx) error {
	devices, err := handler.Service.ListDevices(c.Context())
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "List devices",
		Results: devices,
	})
}

func (handler *Device) GetDevice(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	device, err := handler.Service.GetDevice(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device info",
		Results: device,
	})
}

func (handler *Device) AddDevice(c fiber.Ctx) error {
	var req struct {
		DeviceID                  string `json:"device_id"`
		WebhookURL                string `json:"webhook_url"`
		WebhookSecret             string `json:"webhook_secret"`
		WebhookEvents             string `json:"webhook_events"`
		WebhookInsecureSkipVerify bool   `json:"webhook_insecure_skip_verify"`
	}

	if err := c.Bind().Body(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "Invalid request body",
			Results: nil,
		})
	}

	var webhook *chatstorage.DeviceWebhookConfig
	if req.WebhookURL != "" || req.WebhookSecret != "" || req.WebhookEvents != "" || req.WebhookInsecureSkipVerify {
		webhook = &chatstorage.DeviceWebhookConfig{
			WebhookURL:                &req.WebhookURL,
			WebhookSecret:             req.WebhookSecret,
			WebhookEvents:             req.WebhookEvents,
			WebhookInsecureSkipVerify: req.WebhookInsecureSkipVerify,
		}
	}

	device, err := handler.Service.AddDevice(c.Context(), req.DeviceID, webhook)
	utils.PanicIfNeeded(err)

	result := map[string]any{
		"id":           device.ID,
		"display_name": device.DisplayName,
		"jid":          device.JID,
		"state":        device.State,
		"created_at":   device.CreatedAt,
	}
	if webhook != nil {
		result["webhook_url"] = req.WebhookURL
		result["webhook_secret"] = req.WebhookSecret
		result["webhook_events"] = req.WebhookEvents
		result["webhook_insecure_skip_verify"] = req.WebhookInsecureSkipVerify
	}

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device added",
		Results: result,
	})
}

func (handler *Device) RemoveDevice(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	err := handler.Service.RemoveDevice(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device removed",
		Results: nil,
	})
}

func (handler *Device) LoginDevice(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	response, err := handler.Service.LoginDevice(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Login success",
		Results: map[string]any{
			"device_id":   deviceID,
			"qr_link":     fmt.Sprintf("%s://%s%s/%s", c.Scheme(), c.Host(), config.AppBasePath, response.ImagePath),
			"qr_duration": response.Duration,
		},
	})
}

func (handler *Device) LoginDeviceWithCode(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	code, err := handler.Service.LoginDeviceWithCode(c.Context(), deviceID, c.Query("phone"))
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Login with code started",
		Results: map[string]any{
			"device_id": deviceID,
			"pair_code": code,
		},
	})
}

func (handler *Device) LogoutDevice(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	err := handler.Service.LogoutDevice(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Logout requested",
		Results: nil,
	})
}

func (handler *Device) ReconnectDevice(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	err := handler.Service.ReconnectDevice(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Reconnect requested",
		Results: nil,
	})
}

func (handler *Device) Status(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	isConnected, isLoggedIn, err := handler.Service.GetStatus(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device status",
		Results: map[string]any{
			"device_id":    deviceID,
			"is_connected": isConnected,
			"is_logged_in": isLoggedIn,
		},
	})
}

// UpdateDeviceWebhook handles PATCH /devices/:device_id/webhook.
func (handler *Device) UpdateDeviceWebhook(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	var req struct {
		WebhookURL                *string                    `json:"webhook_url"`
		WebhookSecret             string                     `json:"webhook_secret"`
		WebhookEvents             string                     `json:"webhook_events"`
		WebhookInsecureSkipVerify bool                       `json:"webhook_insecure_skip_verify"`
		WebhookRoutes             []chatstorage.WebhookRoute `json:"webhook_routes"`
	}

	if err := c.Bind().Body(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "Invalid request body",
			Results: nil,
		})
	}

	existingConfig, _ := handler.Service.GetDeviceWebhookConfig(c.Context(), deviceID)
	webhookURL := req.WebhookURL
	if webhookURL == nil && existingConfig != nil {
		webhookURL = existingConfig.WebhookURL
	}

	if webhookURL == nil && len(req.WebhookRoutes) == 0 {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "webhook_url or webhook_routes is required",
			Results: nil,
		})
	}

	routes := req.WebhookRoutes
	if routes == nil && existingConfig != nil {
		routes = existingConfig.WebhookRoutes
	}
	if routes == nil {
		routes = []chatstorage.WebhookRoute{}
	}

	config := &chatstorage.DeviceWebhookConfig{
		WebhookURL:                webhookURL,
		WebhookSecret:             req.WebhookSecret,
		WebhookEvents:             req.WebhookEvents,
		WebhookInsecureSkipVerify: req.WebhookInsecureSkipVerify,
		WebhookRoutes:             routes,
	}

	err := handler.Service.SetDeviceWebhookConfig(c.Context(), deviceID, config)
	utils.PanicIfNeeded(err)

	urlResult := ""
	if webhookURL != nil {
		urlResult = *webhookURL
	}

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device webhook updated",
		Results: map[string]any{
			"device_id":                    deviceID,
			"webhook_url":                  urlResult,
			"webhook_secret":               req.WebhookSecret,
			"webhook_events":               req.WebhookEvents,
			"webhook_insecure_skip_verify": req.WebhookInsecureSkipVerify,
			"webhook_routes":               routes,
		},
	})
}

// GetDeviceWebhook handles GET /devices/:device_id/webhook.
func (handler *Device) GetDeviceWebhook(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	config, err := handler.Service.GetDeviceWebhookConfig(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	webhookURL := ""
	if config != nil && config.WebhookURL != nil {
		webhookURL = *config.WebhookURL
	}

	routes := []chatstorage.WebhookRoute{}
	if config != nil && config.WebhookRoutes != nil {
		routes = config.WebhookRoutes
	}

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device webhook retrieved",
		Results: map[string]any{
			"device_id":   deviceID,
			"webhook_url": webhookURL,
			"webhook_secret": func() string {
				if config != nil {
					return config.WebhookSecret
				}
				return ""
			}(),
			"webhook_events": func() string {
				if config != nil {
					return config.WebhookEvents
				}
				return ""
			}(),
			"webhook_insecure_skip_verify": func() bool {
				if config != nil {
					return config.WebhookInsecureSkipVerify
				}
				return false
			}(),
			"webhook_routes": routes,
		},
	})
}

// ListDeviceWebhookRoutes handles GET /devices/:device_id/webhook/routes.
func (handler *Device) ListDeviceWebhookRoutes(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	routes, err := handler.Service.GetDeviceWebhookRoutes(c.Context(), deviceID)
	utils.PanicIfNeeded(err)

	if routes == nil {
		routes = []chatstorage.WebhookRoute{}
	}

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device webhook routes retrieved",
		Results: routes,
	})
}

// AddDeviceWebhookRoute handles POST /devices/:device_id/webhook/routes.
func (handler *Device) AddDeviceWebhookRoute(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	var route chatstorage.WebhookRoute
	if err := c.Bind().Body(&route); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "Invalid request body",
			Results: nil,
		})
	}

	if strings.TrimSpace(route.WebhookURL) == "" {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "webhook_url is required",
			Results: nil,
		})
	}

	created, err := handler.Service.AddDeviceWebhookRoute(c.Context(), deviceID, route)
	utils.PanicIfNeeded(err)

	return c.Status(fiber.StatusCreated).JSON(utils.ResponseData{
		Status:  201,
		Code:    "SUCCESS",
		Message: "Device webhook route added",
		Results: created,
	})
}

// UpdateDeviceWebhookRoute handles PUT /devices/:device_id/webhook/routes/:route_id.
func (handler *Device) UpdateDeviceWebhookRoute(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	routeID := c.Params("route_id")
	if strings.TrimSpace(routeID) == "" {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "route_id is required",
			Results: nil,
		})
	}

	var route chatstorage.WebhookRoute
	if err := c.Bind().Body(&route); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "Invalid request body",
			Results: nil,
		})
	}

	if strings.TrimSpace(route.WebhookURL) == "" {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "webhook_url is required",
			Results: nil,
		})
	}

	updated, err := handler.Service.UpdateDeviceWebhookRoute(c.Context(), deviceID, routeID, route)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device webhook route updated",
		Results: updated,
	})
}

// DeleteDeviceWebhookRoute handles DELETE /devices/:device_id/webhook/routes/:route_id.
func (handler *Device) DeleteDeviceWebhookRoute(c fiber.Ctx) error {
	deviceID := pathDeviceID(c)
	routeID := c.Params("route_id")
	if strings.TrimSpace(routeID) == "" {
		return c.Status(fiber.StatusBadRequest).JSON(utils.ResponseData{
			Status:  400,
			Code:    "BAD_REQUEST",
			Message: "route_id is required",
			Results: nil,
		})
	}

	err := handler.Service.DeleteDeviceWebhookRoute(c.Context(), deviceID, routeID)
	utils.PanicIfNeeded(err)

	return c.JSON(utils.ResponseData{
		Status:  200,
		Code:    "SUCCESS",
		Message: "Device webhook route deleted",
		Results: map[string]any{
			"device_id": deviceID,
			"route_id":  routeID,
		},
	})
}
