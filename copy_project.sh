#!/bin/bash
# Copy Project Script
# Usage: ./copy_project.sh /path/to/destination

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$1"

if [ -z "$DEST" ]; then
    echo "❌ Error: Destination path required"
    echo ""
    echo "Usage: ./copy_project.sh /path/to/destination"
    echo ""
    echo "Examples:"
    echo "  ./copy_project.sh /Volumes/USB/mosab-sport"
    echo "  ./copy_project.sh ~/Desktop/mosab-sport"
    echo "  ./copy_project.sh /Users/Shared/mosab-sport"
    exit 1
fi

echo "📦 Copying Mosab Sport project..."
echo "   From: $SOURCE"
echo "   To:   $DEST/mosab-sport"
echo ""

# Create destination directory
mkdir -p "$DEST"

# Copy with exclusions
rsync -av --progress \
    --exclude 'node_modules' \
    --exclude 'backend/uploads/reports' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude 'venv' \
    "$SOURCE/" "$DEST/mosab-sport/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Copy complete!"
    echo ""
    echo "📋 On the other computer, run:"
    echo "   cd $DEST/mosab-sport"
    echo "   docker-compose up -d --build"
    echo "   docker-compose exec api alembic upgrade head"
    echo ""
else
    echo ""
    echo "❌ Copy failed!"
    exit 1
fi

