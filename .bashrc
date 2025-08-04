# Project-specific conda configuration for Vibe Dating Backend
# This file is sourced when entering the project directory

if command -v conda &> /dev/null; then
    # Initialize conda if not already done
    if [ -z "$CONDA_DEFAULT_ENV" ]; then
        eval "$(conda shell.bash hook)"
    fi
    
    # Activate base environment if not already active
    if [ "$CONDA_DEFAULT_ENV" != "base" ]; then
        conda activate base
        echo "Conda base environment activated for Vibe Dating Backend"
    fi
fi

# Set project-specific environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
export AWS_PROFILE="${AWS_PROFILE:-default}"

# Show helpful project info
echo "Vibe Dating Backend - Conda base environment ready" 