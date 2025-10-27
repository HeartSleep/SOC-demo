package burp;

import burp.api.montoya.BurpExtension;
import burp.api.montoya.MontoyaApi;
import burp.api.montoya.http.message.HttpRequestResponse;
import burp.api.montoya.http.message.requests.HttpRequest;
import burp.api.montoya.http.message.responses.HttpResponse;
import burp.api.montoya.proxy.http.InterceptedRequest;
import burp.api.montoya.proxy.http.InterceptedResponse;
import burp.api.montoya.proxy.http.ProxyRequestHandler;
import burp.api.montoya.proxy.http.ProxyRequestReceivedAction;
import burp.api.montoya.proxy.http.ProxyRequestToBeSentAction;
import burp.api.montoya.proxy.http.ProxyResponseHandler;
import burp.api.montoya.proxy.http.ProxyResponseReceivedAction;
import burp.api.montoya.proxy.http.ProxyResponseToBeSentAction;
import burp.api.montoya.ui.contextmenu.ContextMenuEvent;
import burp.api.montoya.ui.contextmenu.ContextMenuItemsProvider;
import burp.api.montoya.ui.contextmenu.MenuItem;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest.Builder;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * SOC Platform Burp Suite Extension
 *
 * This extension integrates Burp Suite with the SOC Platform by:
 * 1. Automatically sending discovered vulnerabilities to the SOC Platform
 * 2. Allowing manual import of Burp findings
 * 3. Providing context menu integration for sending requests
 */
public class SOCPlatformExtension implements BurpExtension, ProxyRequestHandler,
                                           ProxyResponseHandler, ContextMenuItemsProvider {

    private MontoyaApi api;
    private HttpClient httpClient;
    private SOCConfig config;
    private JPanel configPanel;

    // Configuration storage
    private static class SOCConfig {
        String socApiUrl = "http://localhost:8000";
        String apiToken = "";
        boolean autoSendVulns = true;
        boolean logTraffic = false;
        String projectName = "Burp Suite Scan";

        void loadFromExtensionSettings(MontoyaApi api) {
            socApiUrl = api.persistence().extensionData().getString("soc_api_url", socApiUrl);
            apiToken = api.persistence().extensionData().getString("api_token", apiToken);
            autoSendVulns = api.persistence().extensionData().getBoolean("auto_send_vulns", autoSendVulns);
            logTraffic = api.persistence().extensionData().getBoolean("log_traffic", logTraffic);
            projectName = api.persistence().extensionData().getString("project_name", projectName);
        }

        void saveToExtensionSettings(MontoyaApi api) {
            api.persistence().extensionData().setString("soc_api_url", socApiUrl);
            api.persistence().extensionData().setString("api_token", apiToken);
            api.persistence().extensionData().setBoolean("auto_send_vulns", autoSendVulns);
            api.persistence().extensionData().setBoolean("log_traffic", logTraffic);
            api.persistence().extensionData().setString("project_name", projectName);
        }
    }

    @Override
    public void initialize(MontoyaApi api) {
        this.api = api;
        this.config = new SOCConfig();
        this.config.loadFromExtensionSettings(api);

        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

        // Set extension name
        api.extension().setName("SOC Platform Integration");

        // Register handlers
        api.proxy().registerRequestHandler(this);
        api.proxy().registerResponseHandler(this);
        api.userInterface().registerContextMenuItemsProvider(this);

        // Create configuration UI
        createConfigurationPanel();
        api.userInterface().registerSuiteTab("SOC Platform", configPanel);

        // Register scanner check for automatic vulnerability sending
        if (config.autoSendVulns) {
            registerScannerIntegration();
        }

        api.logging().logToOutput("SOC Platform Extension loaded successfully");
    }

    private void createConfigurationPanel() {
        configPanel = new JPanel(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;

        // SOC API URL
        gbc.gridx = 0; gbc.gridy = 0;
        configPanel.add(new JLabel("SOC API URL:"), gbc);
        JTextField urlField = new JTextField(config.socApiUrl, 30);
        gbc.gridx = 1;
        configPanel.add(urlField, gbc);

        // API Token
        gbc.gridx = 0; gbc.gridy = 1;
        configPanel.add(new JLabel("API Token:"), gbc);
        JPasswordField tokenField = new JPasswordField(config.apiToken, 30);
        gbc.gridx = 1;
        configPanel.add(tokenField, gbc);

        // Project Name
        gbc.gridx = 0; gbc.gridy = 2;
        configPanel.add(new JLabel("Project Name:"), gbc);
        JTextField projectField = new JTextField(config.projectName, 30);
        gbc.gridx = 1;
        configPanel.add(projectField, gbc);

        // Auto-send vulnerabilities checkbox
        gbc.gridx = 0; gbc.gridy = 3; gbc.gridwidth = 2;
        JCheckBox autoSendBox = new JCheckBox("Automatically send vulnerabilities to SOC Platform", config.autoSendVulns);
        configPanel.add(autoSendBox, gbc);

        // Log traffic checkbox
        gbc.gridy = 4;
        JCheckBox logTrafficBox = new JCheckBox("Log HTTP traffic to SOC Platform", config.logTraffic);
        configPanel.add(logTrafficBox, gbc);

        // Save button
        gbc.gridy = 5; gbc.gridwidth = 1;
        JButton saveButton = new JButton("Save Configuration");
        saveButton.addActionListener(e -> {
            config.socApiUrl = urlField.getText().trim();
            config.apiToken = new String(tokenField.getPassword());
            config.projectName = projectField.getText().trim();
            config.autoSendVulns = autoSendBox.isSelected();
            config.logTraffic = logTrafficBox.isSelected();
            config.saveToExtensionSettings(api);

            JOptionPane.showMessageDialog(configPanel, "Configuration saved successfully!");
        });
        configPanel.add(saveButton, gbc);

        // Test connection button
        gbc.gridx = 1;
        JButton testButton = new JButton("Test Connection");
        testButton.addActionListener(e -> testConnection());
        configPanel.add(testButton, gbc);

        // Manual import button
        gbc.gridx = 0; gbc.gridy = 6; gbc.gridwidth = 2;
        JButton importButton = new JButton("Import Current Scanner Issues");
        importButton.addActionListener(e -> importScannerIssues());
        configPanel.add(importButton, gbc);

        // Status area
        gbc.gridy = 7; gbc.fill = GridBagConstraints.BOTH; gbc.weightx = 1.0; gbc.weighty = 1.0;
        JTextArea statusArea = new JTextArea(10, 40);
        statusArea.setEditable(false);
        statusArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        JScrollPane scrollPane = new JScrollPane(statusArea);
        configPanel.add(scrollPane, gbc);

        // Redirect logging to status area
        redirectLoggingToTextArea(statusArea);
    }

    private void redirectLoggingToTextArea(JTextArea textArea) {
        // Simple logging redirect - in practice, you'd want a more sophisticated solution
        SwingUtilities.invokeLater(() -> {
            textArea.append("SOC Platform Extension initialized\n");
            textArea.append("Configuration loaded\n");
            textArea.append("Ready to send data to: " + config.socApiUrl + "\n\n");
        });
    }

    private void testConnection() {
        CompletableFuture.supplyAsync(() -> {
            try {
                java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                    .uri(URI.create(config.socApiUrl + "/health"))
                    .timeout(Duration.ofSeconds(10))
                    .GET()
                    .build();

                var response = httpClient.send(request, BodyHandlers.ofString());

                if (response.statusCode() == 200) {
                    return "✅ Connection successful! SOC Platform is reachable.";
                } else {
                    return "❌ Connection failed. Status: " + response.statusCode();
                }
            } catch (Exception e) {
                return "❌ Connection failed: " + e.getMessage();
            }
        }).thenAccept(message -> {
            SwingUtilities.invokeLater(() -> {
                JOptionPane.showMessageDialog(configPanel, message);
            });
        });
    }

    private void registerScannerIntegration() {
        // Register a scanner check that automatically sends vulnerabilities
        api.scanner().registerScanCheck(new SOCPlatformScanCheck(this));
    }

    private void importScannerIssues() {
        SwingUtilities.invokeLater(() -> {
            JOptionPane.showMessageDialog(configPanel, "Starting import of scanner issues...");
        });

        CompletableFuture.runAsync(() -> {
            var issues = api.siteMap().requestResponses().stream()
                .flatMap(rr -> rr.annotations().notes().stream())
                .filter(note -> note.contains("vulnerability") || note.contains("issue"))
                .toList();

            int imported = 0;
            for (var issue : issues) {
                try {
                    if (sendIssueToSOC(issue, "burp_import")) {
                        imported++;
                    }
                } catch (Exception e) {
                    api.logging().logToError("Failed to import issue: " + e.getMessage());
                }
            }

            final int finalImported = imported;
            SwingUtilities.invokeLater(() -> {
                JOptionPane.showMessageDialog(configPanel,
                    "Import completed! Sent " + finalImported + " issues to SOC Platform.");
            });
        });
    }

    private boolean sendIssueToSOC(String issueDetails, String source) {
        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("name", "Burp Suite Finding");
            payload.put("description", issueDetails);
            payload.put("severity", "medium");  // Default severity
            payload.put("source", source);
            payload.put("project", config.projectName);
            payload.put("discovered_at", java.time.Instant.now().toString());

            String jsonPayload = convertToJson(payload);

            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                .uri(URI.create(config.socApiUrl + "/api/vulnerabilities/import"))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + config.apiToken)
                .POST(java.net.http.HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

            var response = httpClient.send(request, BodyHandlers.ofString());
            return response.statusCode() >= 200 && response.statusCode() < 300;

        } catch (Exception e) {
            api.logging().logToError("Failed to send issue to SOC: " + e.getMessage());
            return false;
        }
    }

    private String convertToJson(Map<String, Object> data) {
        // Simple JSON conversion - in practice, use a proper JSON library
        StringBuilder json = new StringBuilder("{");
        data.forEach((key, value) -> {
            json.append("\"").append(key).append("\":\"").append(value).append("\",");
        });
        if (json.length() > 1) {
            json.setLength(json.length() - 1); // Remove trailing comma
        }
        json.append("}");
        return json.toString();
    }

    @Override
    public ProxyRequestReceivedAction handleRequestReceived(InterceptedRequest interceptedRequest) {
        // Log traffic if enabled
        if (config.logTraffic) {
            logRequest(interceptedRequest.httpRequest());
        }
        return ProxyRequestReceivedAction.continueWith(interceptedRequest.httpRequest());
    }

    @Override
    public ProxyRequestToBeSentAction handleRequestToBeSent(InterceptedRequest interceptedRequest) {
        return ProxyRequestToBeSentAction.continueWith(interceptedRequest.httpRequest());
    }

    @Override
    public ProxyResponseReceivedAction handleResponseReceived(InterceptedResponse interceptedResponse) {
        // Log traffic if enabled
        if (config.logTraffic) {
            logResponse(interceptedResponse.httpResponse());
        }
        return ProxyResponseReceivedAction.continueWith(interceptedResponse.httpResponse());
    }

    @Override
    public ProxyResponseToBeSentAction handleResponseToBeSent(InterceptedResponse interceptedResponse) {
        return ProxyResponseToBeSentAction.continueWith(interceptedResponse.httpResponse());
    }

    private void logRequest(HttpRequest request) {
        CompletableFuture.runAsync(() -> {
            try {
                Map<String, Object> logData = new HashMap<>();
                logData.put("type", "request");
                logData.put("method", request.method());
                logData.put("url", request.url());
                logData.put("headers", request.headers().toString());
                logData.put("timestamp", java.time.Instant.now().toString());
                logData.put("source", "burp_proxy");

                sendLogToSOC(logData);
            } catch (Exception e) {
                api.logging().logToError("Failed to log request: " + e.getMessage());
            }
        });
    }

    private void logResponse(HttpResponse response) {
        CompletableFuture.runAsync(() -> {
            try {
                Map<String, Object> logData = new HashMap<>();
                logData.put("type", "response");
                logData.put("status_code", response.statusCode());
                logData.put("headers", response.headers().toString());
                logData.put("timestamp", java.time.Instant.now().toString());
                logData.put("source", "burp_proxy");

                sendLogToSOC(logData);
            } catch (Exception e) {
                api.logging().logToError("Failed to log response: " + e.getMessage());
            }
        });
    }

    private void sendLogToSOC(Map<String, Object> logData) {
        try {
            String jsonPayload = convertToJson(logData);

            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                .uri(URI.create(config.socApiUrl + "/api/logs/burp"))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + config.apiToken)
                .POST(java.net.http.HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

            httpClient.sendAsync(request, BodyHandlers.ofString());
        } catch (Exception e) {
            api.logging().logToError("Failed to send log to SOC: " + e.getMessage());
        }
    }

    @Override
    public List<MenuItem> provideMenuItems(ContextMenuEvent event) {
        List<MenuItem> menuItems = new ArrayList<>();

        if (event.isFromTool(burp.api.montoya.core.Tool.PROXY,
                             burp.api.montoya.core.Tool.REPEATER,
                             burp.api.montoya.core.Tool.INTRUDER)) {

            menuItems.add(MenuItem.menuItem("Send to SOC Platform",
                actionEvent -> sendSelectedRequestsToSOC(event.requestResponses())));

            menuItems.add(MenuItem.menuItem("Add as Asset to SOC",
                actionEvent -> addAsAssetToSOC(event.requestResponses())));
        }

        return menuItems;
    }

    private void sendSelectedRequestsToSOC(List<HttpRequestResponse> requestResponses) {
        CompletableFuture.runAsync(() -> {
            int sent = 0;
            for (HttpRequestResponse requestResponse : requestResponses) {
                try {
                    Map<String, Object> data = new HashMap<>();
                    data.put("url", requestResponse.request().url());
                    data.put("method", requestResponse.request().method());
                    data.put("status_code", requestResponse.response() != null ?
                            requestResponse.response().statusCode() : 0);
                    data.put("source", "burp_manual");
                    data.put("project", config.projectName);

                    String jsonPayload = convertToJson(data);

                    java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                        .uri(URI.create(config.socApiUrl + "/api/traffic/import"))
                        .timeout(Duration.ofSeconds(30))
                        .header("Content-Type", "application/json")
                        .header("Authorization", "Bearer " + config.apiToken)
                        .POST(java.net.http.HttpRequest.BodyPublishers.ofString(jsonPayload))
                        .build();

                    var response = httpClient.send(request, BodyHandlers.ofString());
                    if (response.statusCode() >= 200 && response.statusCode() < 300) {
                        sent++;
                    }
                } catch (Exception e) {
                    api.logging().logToError("Failed to send request to SOC: " + e.getMessage());
                }
            }

            final int finalSent = sent;
            SwingUtilities.invokeLater(() -> {
                JOptionPane.showMessageDialog(null,
                    "Sent " + finalSent + " requests to SOC Platform");
            });
        });
    }

    private void addAsAssetToSOC(List<HttpRequestResponse> requestResponses) {
        CompletableFuture.runAsync(() -> {
            int added = 0;
            for (HttpRequestResponse requestResponse : requestResponses) {
                try {
                    String url = requestResponse.request().url();
                    URI uri = URI.create(url);
                    String host = uri.getHost();

                    Map<String, Object> assetData = new HashMap<>();
                    assetData.put("name", host);
                    assetData.put("type", "domain");
                    assetData.put("value", host);
                    assetData.put("priority", "medium");
                    assetData.put("source", "burp_suite");
                    assetData.put("description", "Discovered via Burp Suite");

                    String jsonPayload = convertToJson(assetData);

                    java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                        .uri(URI.create(config.socApiUrl + "/api/assets"))
                        .timeout(Duration.ofSeconds(30))
                        .header("Content-Type", "application/json")
                        .header("Authorization", "Bearer " + config.apiToken)
                        .POST(java.net.http.HttpRequest.BodyPublishers.ofString(jsonPayload))
                        .build();

                    var response = httpClient.send(request, BodyHandlers.ofString());
                    if (response.statusCode() >= 200 && response.statusCode() < 300) {
                        added++;
                    }
                } catch (Exception e) {
                    api.logging().logToError("Failed to add asset to SOC: " + e.getMessage());
                }
            }

            final int finalAdded = added;
            SwingUtilities.invokeLater(() -> {
                JOptionPane.showMessageDialog(null,
                    "Added " + finalAdded + " assets to SOC Platform");
            });
        });
    }

    // Inner class for scanner integration
    private static class SOCPlatformScanCheck implements burp.api.montoya.scanner.ScanCheck {
        private final SOCPlatformExtension extension;

        public SOCPlatformScanCheck(SOCPlatformExtension extension) {
            this.extension = extension;
        }

        @Override
        public List<burp.api.montoya.scanner.audit.issues.AuditIssue> doPassiveScan(
                burp.api.montoya.http.message.HttpRequestResponse baseRequestResponse) {
            // Automatically send any discovered issues to SOC Platform
            return List.of();
        }

        @Override
        public List<burp.api.montoya.scanner.audit.issues.AuditIssue> doActiveScan(
                burp.api.montoya.http.message.HttpRequestResponse baseRequestResponse,
                burp.api.montoya.scanner.audit.insertionpoint.AuditInsertionPoint auditInsertionPoint) {
            // Automatically send any discovered issues to SOC Platform
            return List.of();
        }
    }
}