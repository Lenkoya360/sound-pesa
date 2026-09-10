#!/bin/bash
set -e

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until curl -s http://vault:8200/v1/sys/health > /dev/null 2>&1; do
    echo "Vault is not ready yet, waiting..."
    sleep 5
done

echo "Vault is ready!"

# Check if Vault is already initialized
VAULT_STATUS=$(curl -s http://vault:8200/v1/sys/init)
IS_INITIALIZED=$(echo $VAULT_STATUS | grep -o '"initialized":[^,]*' | cut -d':' -f2)

if [ "$IS_INITIALIZED" = "false" ]; then
    echo "Initializing Vault..."
    
    # Initialize Vault
    INIT_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"secret_shares": 5, "secret_threshold": 3}' \
        http://vault:8200/v1/sys/init)
    
    # Extract keys and root token
    UNSEAL_KEY_1=$(echo $INIT_RESPONSE | jq -r '.keys[0]')
    UNSEAL_KEY_2=$(echo $INIT_RESPONSE | jq -r '.keys[1]')
    UNSEAL_KEY_3=$(echo $INIT_RESPONSE | jq -r '.keys[2]')
    ROOT_TOKEN=$(echo $INIT_RESPONSE | jq -r '.root_token')
    
    echo "Vault initialized successfully!"
    echo "Root Token: $ROOT_TOKEN"
    echo "Unseal Key 1: $UNSEAL_KEY_1"
    echo "Unseal Key 2: $UNSEAL_KEY_2"
    echo "Unseal Key 3: $UNSEAL_KEY_3"
    
    # Save keys to files (in production, these should be stored securely)
    echo $ROOT_TOKEN > /vault/data/root-token
    echo $UNSEAL_KEY_1 > /vault/data/unseal-key-1
    echo $UNSEAL_KEY_2 > /vault/data/unseal-key-2
    echo $UNSEAL_KEY_3 > /vault/data/unseal-key-3
    
    # Unseal Vault
    echo "Unsealing Vault..."
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"key\": \"$UNSEAL_KEY_1\"}" \
        http://vault:8200/v1/sys/unseal
    
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"key\": \"$UNSEAL_KEY_2\"}" \
        http://vault:8200/v1/sys/unseal
    
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"key\": \"$UNSEAL_KEY_3\"}" \
        http://vault:8200/v1/sys/unseal
    
    echo "Vault unsealed successfully!"
    
    # Set root token as environment variable for further operations
    export VAULT_TOKEN=$ROOT_TOKEN
    
else
    echo "Vault is already initialized"
    
    # Check if Vault is sealed
    SEAL_STATUS=$(curl -s http://vault:8200/v1/sys/seal-status)
    IS_SEALED=$(echo $SEAL_STATUS | jq -r '.sealed')
    
    if [ "$IS_SEALED" = "true" ]; then
        echo "Vault is sealed, attempting to unseal..."
        
        # Try to read unseal keys from files
        if [ -f /vault/data/unseal-key-1 ] && [ -f /vault/data/unseal-key-2 ] && [ -f /vault/data/unseal-key-3 ]; then
            UNSEAL_KEY_1=$(cat /vault/data/unseal-key-1)
            UNSEAL_KEY_2=$(cat /vault/data/unseal-key-2)
            UNSEAL_KEY_3=$(cat /vault/data/unseal-key-3)
            
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -d "{\"key\": \"$UNSEAL_KEY_1\"}" \
                http://vault:8200/v1/sys/unseal
            
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -d "{\"key\": \"$UNSEAL_KEY_2\"}" \
                http://vault:8200/v1/sys/unseal
            
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -d "{\"key\": \"$UNSEAL_KEY_3\"}" \
                http://vault:8200/v1/sys/unseal
            
            echo "Vault unsealed successfully!"
        else
            echo "Unseal keys not found. Manual unsealing required."
            exit 1
        fi
    else
        echo "Vault is already unsealed"
    fi
    
    # Read root token
    if [ -f /vault/data/root-token ]; then
        export VAULT_TOKEN=$(cat /vault/data/root-token)
    else
        echo "Root token not found. Using environment variable."
        export VAULT_TOKEN=${VAULT_DEV_ROOT_TOKEN_ID}
    fi
fi

# Configure Vault policies and auth methods
echo "Configuring Vault policies..."

# Create policy for Sound Pesa application
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "policy": "path \"sound-pesa/*\" {\n  capabilities = [\"create\", \"read\", \"update\", \"delete\", \"list\"]\n}\npath \"transit/encrypt/private-keys\" {\n  capabilities = [\"update\"]\n}\npath \"transit/decrypt/private-keys\" {\n  capabilities = [\"update\"]\n}\npath \"transit/encrypt/api-keys\" {\n  capabilities = [\"update\"]\n}\npath \"transit/decrypt/api-keys\" {\n  capabilities = [\"update\"]\n}\npath \"database/creds/soundpesa-app\" {\n  capabilities = [\"read\"]\n}"
    }' \
    http://vault:8200/v1/sys/policies/acl/soundpesa-app

echo "Vault configuration completed!"

# Health check
echo "Performing health check..."
HEALTH_STATUS=$(curl -s http://vault:8200/v1/sys/health)
echo "Vault health status: $HEALTH_STATUS"

echo "Vault initialization script completed successfully!"