#!/bin/bash

# Script to install the Speech Transcriber as a macOS LaunchAgent

# Define paths
PLIST_SOURCE="$(pwd)/com.user.speech_transcriber.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/com.user.speech_transcriber.plist"

# Ensure LaunchAgents directory exists
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist file
echo "Installing LaunchAgent plist file..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Set permissions
chmod 644 "$PLIST_DEST"

# Unload the service if it's already loaded
echo "Unloading any existing service..."
launchctl unload "$PLIST_DEST" 2>/dev/null

# Load the service
echo "Loading the service..."
launchctl load "$PLIST_DEST"

# Check status
echo "Checking service status..."
launchctl list | grep com.user.speech_transcriber

echo ""
echo "Installation complete!"
echo "IMPORTANT: To grant necessary permissions, the service will run the next time you restart"
echo "or you can manually start it now. You will be prompted to grant microphone and"
echo "accessibility permissions the first time it runs."
echo ""
echo "To uninstall, run: launchctl unload $PLIST_DEST"
echo "and then delete the plist file: rm $PLIST_DEST"