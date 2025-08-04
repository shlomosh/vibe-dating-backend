#!/bin/bash

# Script to configure automatic conda base activation for terminals

echo "Setting up automatic conda base activation for terminals..."

# Get the user's shell profile file
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
else
    echo "No shell profile found. Creating .bashrc..."
    SHELL_PROFILE="$HOME/.bashrc"
fi

# Check if conda activation is already configured
if grep -q "conda activate base" "$SHELL_PROFILE"; then
    echo "Conda base activation is already configured in $SHELL_PROFILE"
else
    # Add conda initialization and base activation
    echo "" >> "$SHELL_PROFILE"
    echo "# Conda base environment auto-activation" >> "$SHELL_PROFILE"
    echo "if command -v conda &> /dev/null; then" >> "$SHELL_PROFILE"
    echo "    # Initialize conda" >> "$SHELL_PROFILE"
    echo "    eval \"\$(conda shell.bash hook)\"" >> "$SHELL_PROFILE"
    echo "    # Activate base environment" >> "$SHELL_PROFILE"
    echo "    conda activate base" >> "$SHELL_PROFILE"
    echo "fi" >> "$SHELL_PROFILE"
    
    echo "Added conda base activation to $SHELL_PROFILE"
fi

# Create a project-specific profile for this workspace
PROJECT_PROFILE=".bashrc"
if [ ! -f "$PROJECT_PROFILE" ]; then
    echo "# Project-specific conda configuration" > "$PROJECT_PROFILE"
    echo "if command -v conda &> /dev/null; then" >> "$PROJECT_PROFILE"
    echo "    conda activate base" >> "$PROJECT_PROFILE"
    echo "    echo 'Conda base environment activated for Vibe Dating Backend'" >> "$PROJECT_PROFILE"
    echo "fi" >> "$PROJECT_PROFILE"
    
    echo "Created project-specific profile: $PROJECT_PROFILE"
fi

echo "Terminal setup complete!"
echo "To apply changes immediately, run: source $SHELL_PROFILE"
echo "Or restart your terminal." 