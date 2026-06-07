// SwarmDesk AI — Azure Infrastructure
// Deploys: Container Apps + Azure AI Search + Cosmos DB + Redis Cache
// Deploy: az deployment group create --resource-group swarmdesk-rg --template-file main.bicep

param location string = resourceGroup().location
param appName  string = 'swarmdesk'
param env      string = 'prod'

// ── Azure Container Apps Environment ─────────────────────────────────────────
resource containerEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${appName}-env-${env}'
  location: location
  properties: {
    appLogsConfiguration: { destination: 'azure-monitor' }
  }
}

// ── Container App: API ────────────────────────────────────────────────────────
resource apiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-api-${env}'
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
      }
    }
    template: {
      containers: [{
        name: 'swarmdesk-api'
        image: 'ghcr.io/anishagarg/swarmdesk-ai:latest'
        resources: { cpu: '1.0', memory: '2Gi' }
        env: [
          { name: 'AZURE_OPENAI_ENDPOINT', secretRef: 'openai-endpoint' }
          { name: 'AZURE_OPENAI_KEY',      secretRef: 'openai-key' }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 10 }
    }
  }
}

// ── Azure AI Search ───────────────────────────────────────────────────────────
resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${appName}-search-${env}'
  location: location
  sku: { name: 'standard' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

// ── Azure Cosmos DB ───────────────────────────────────────────────────────────
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: '${appName}-cosmos-${env}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
  }
}

// ── Azure Cache for Redis ─────────────────────────────────────────────────────
resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: '${appName}-redis-${env}'
  location: location
  properties: {
    sku: { name: 'Basic', family: 'C', capacity: 0 }
    enableNonSslPort: false
  }
}

output apiUrl   string = 'https://${apiApp.properties.configuration.ingress.fqdn}'
output searchEp string = 'https://${search.name}.search.windows.net'
output cosmosEp string = cosmos.properties.documentEndpoint
