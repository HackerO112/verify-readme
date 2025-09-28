#!/bin/bash

# VeriCode - Live Documentation Verifier
# Easy Setup Script for Non-Coders
# This script will set up and run the VeriCode application automatically

set -e  # Exit on any error

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Node.js if not present
install_nodejs() {
    print_status "Checking Node.js installation..."

    if command_exists node; then
        NODE_VERSION=$(node -v | cut -d'v' -f2)
        print_success "Node.js v$NODE_VERSION is already installed"
        return 0
    fi

    print_warning "Node.js is not installed. Installing Node.js..."

    # Detect OS and install Node.js accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            # Ubuntu/Debian
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command_exists yum; then
            # CentOS/RHEL
            curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
            sudo yum install -y nodejs
        elif command_exists dnf; then
            # Fedora
            sudo dnf install -y nodejs
        else
            print_error "Could not detect package manager. Please install Node.js manually from https://nodejs.org/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install node
        else
            print_error "Homebrew is not installed. Please install Homebrew first or install Node.js manually from https://nodejs.org/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows (Git Bash)
        print_error "Please install Node.js manually from https://nodejs.org/ and run this script again"
        exit 1
    else
        print_error "Unsupported operating system. Please install Node.js manually from https://nodejs.org/"
        exit 1
    fi

    print_success "Node.js installed successfully"
}

# Function to check and install npm packages
install_dependencies() {
    print_status "Installing project dependencies..."

    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Please make sure you're in the correct directory."
        exit 1
    fi

    npm install

    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."

    if [ ! -f "prisma/schema.prisma" ]; then
        print_error "Prisma schema not found. Please make sure you're in the correct directory."
        exit 1
    fi

    # FIX: Create the .env file with the DATABASE_URL if it doesn't exist
    print_status "Checking for database configuration..."
    if [ ! -f ".env" ]; then
        print_status "Creating database configuration file (.env)..."
        echo 'DATABASE_URL="file:./dev.db"' > .env
        print_success ".env file created successfully"
    else
        print_status ".env file already exists."
    fi

    # Generate Prisma client
    npx prisma generate

    # Push database schema
    npm run db:push

    if [ $? -eq 0 ]; then
        print_success "Database setup completed successfully"
    else
        print_error "Failed to setup database"
        exit 1
    fi
}

# Function to start the application
start_application() {
    print_status "Starting VeriCode application..."

    print_success "VeriCode is starting up..."
    print_status "Please wait a moment for the development server to initialize..."
    print_status "Once ready, you can access VeriCode at: http://localhost:3000"
    print_status ""
    print_status "To stop the application, press Ctrl+C"
    print_status ""

    # Start the development server
    npm run dev
}

# Function to display system information
display_system_info() {
    print_status "System Information:"
    echo "  Operating System: $OSTYPE"

    if command_exists node; then
        NODE_VERSION=$(node -v)
        echo "  Node.js Version: $NODE_VERSION"
    fi

    if command_exists npm; then
        NPM_VERSION=$(npm -v)
        echo "  NPM Version: $NPM_VERSION"
    fi

    echo ""
}

# Function to check for common issues
check_common_issues() {
    print_status "Checking for common issues..."

    # Check if port 3000 is available
    if command_exists lsof; then
        if lsof -i :3000 >/dev/null 2>&1; then
            print_warning "Port 3000 is already in use. VeriCode might not start properly."
            print_status "You can try to stop the process using port 3000 or change the port in the configuration."
        fi
    fi

    # Check disk space
    if command_exists df; then
        FREE_SPACE=$(df . | tail -1 | awk '{print $4}')
        if [ "$FREE_SPACE" -lt 1048576 ]; then  # Less than 1GB
            print_warning "Low disk space detected. You might need to free up some space."
        fi
    fi

    # Check internet connection
    if command_exists curl; then
        if curl -s --head https://www.google.com > /dev/null; then
            print_success "Internet connection is available"
        else
            print_warning "No internet connection detected. Some features might not work properly."
        fi
    fi
}

# Main script execution
main() {
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                    🚀 VeriCode Setup 🚀                      ║"
    echo "║                Live Documentation Verifier                   ║"
    echo "║                                                              ║"
    echo "║          Easy Setup Script for Non-Coders                   ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    display_system_info
    check_common_issues

    echo ""
    print_status "Starting VeriCode setup process..."
    echo ""

    # Step 1: Check and install Node.js
    install_nodejs
    echo ""

    # Step 2: Install dependencies
    install_dependencies
    echo ""

    # Step 3: Setup database
    setup_database
    echo ""

    # Step 4: Start application
    start_application
}

# Function to show help
show_help() {
    echo "VeriCode - Live Documentation Verifier"
    echo ""
    echo "Usage: ./run-vericode.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -i, --info     Show system information only"
    echo "  -c, --check    Check for common issues only"
    echo "  -s, --setup    Run setup only (don't start app)"
    echo ""
    echo "Examples:"
    echo "  ./run-vericode.sh          # Full setup and start"
    echo "  ./run-vericode.sh -h       # Show help"
    echo "  ./run-vericode.sh -i       # Show system info"
    echo "  ./run-vericode.sh -c       # Check issues"
    echo "  ./run-vericode.sh -s       # Setup only"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -i|--info)
        display_system_info
        exit 0
        ;;
    -c|--check)
        check_common_issues
        exit 0
        ;;
    -s|--setup)
        print_status "Running setup only..."
        install_nodejs
        install_dependencies
        setup_database
        print_success "Setup completed successfully!"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
