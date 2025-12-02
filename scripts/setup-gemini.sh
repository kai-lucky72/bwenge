#!/bin/bash

# Setup Gemini Embeddings for Bwenge OS

echo "🚀 Setting up Gemini Embeddings..."
echo ""

# Your API key
GEMINI_KEY="AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc"

# Install package
echo "📦 Installing google-genai package..."
pip install google-genai==0.2.0

# Add to .env if not already there
if grep -q "GEMINI_API_KEY" .env 2>/dev/null; then
    echo "✅ GEMINI_API_KEY already in .env"
else
    echo "📝 Adding GEMINI_API_KEY to .env..."
    echo "" >> .env
    echo "# Google Gemini API" >> .env
    echo "GEMINI_API_KEY=$GEMINI_KEY" >> .env
    echo "✅ Added GEMINI_API_KEY to .env"
fi

# Test the embeddings
echo ""
echo "🧪 Testing Gemini embeddings..."
export GEMINI_API_KEY=$GEMINI_KEY
python libs/common/gemini_embeddings.py

echo ""
echo "✅ Gemini embeddings setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Start services: ./scripts/local-dev-start.sh"
echo "  2. Upload a document to test embeddings"
echo "  3. Query with RAG to see it in action"
echo ""
echo "📖 Read GEMINI_INTEGRATION_GUIDE.md for more details"
