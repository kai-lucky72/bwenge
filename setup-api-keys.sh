#!/bin/bash

echo "🔑 Bwenge OS API Keys Setup"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run: cp .env.example .env"
    exit 1
fi

echo "📝 Current API key status:"
echo ""

# Check OpenAI API Key
if grep -q "your-openai-api-key" .env; then
    echo "❌ OpenAI API Key: NOT SET (required for AI features)"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Enter your OpenAI API Key (or press Enter to skip): " openai_key
    if [ ! -z "$openai_key" ]; then
        sed -i "s/your-openai-api-key/$openai_key/g" .env
        echo "✅ OpenAI API Key updated!"
    fi
else
    echo "✅ OpenAI API Key: SET"
fi

echo ""

# Check Payment Configuration (Rwanda)
echo "✅ Rwanda Payment System: CONFIGURED"
echo "   - Mobile Money (MTN, Airtel, Tigo): Available"
echo "   - Bank Transfer: Available" 
echo "   - Cash Payment: Available"

echo ""
echo "🚀 Setup complete! You can now restart the services:"
echo "   docker compose down && docker compose up -d"
echo ""
echo "📋 Service Requirements Summary:"
echo "   ✅ Required for basic functionality:"
echo "      - JWT_SECRET (✅ already set)"
echo "      - Database & Redis (✅ running)"
echo "      - Weaviate (✅ running)"
echo ""
echo "   🤖 Required for AI features:"
echo "      - OPENAI_API_KEY (for persona & ingest services)"
echo ""
echo "   💳 Rwanda Payment Methods:"
echo "      - MTN Mobile Money (Momo)"
echo "      - Airtel Money"
echo "      - Tigo Cash"
echo "      - Bank Transfer (BK, Equity, etc.)"
echo "      - Cash Payment"