# 🚀 VeriCode - Easy Setup Guide for Non-Coders

Welcome to VeriCode! This guide will help you set up and run the application easily, even if you have no coding experience.

## 📋 What You'll Need

Before starting, make sure you have:

1. **Node.js** (We'll help you install this if needed)
2. **Internet Connection** (For downloading dependencies)
3. **About 10-15 minutes** of your time
4. **Basic computer skills** (opening terminal/command prompt)

## 🖥️ Choose Your Operating System

### Windows Users

#### Method 1: Using the Automated Script (Recommended)

1. **Double-click** the file named `run-vericode.bat`
2. **Follow the on-screen instructions**
3. **Wait** for the setup to complete
4. **Open your web browser** and go to `http://localhost:3000`

#### Method 2: Manual Setup

1. **Open Command Prompt**:
   - Press `Windows Key + R`
   - Type `cmd` and press Enter

2. **Navigate to the project folder**:
   ```cmd
   cd path\to\vericode
   ```
   (Replace `path\to\vericode` with the actual folder path)

3. **Run the setup**:
   ```cmd
   npm install
   npm run db:push
   npm run dev
   ```

### Mac Users

#### Method 1: Using the Automated Script (Recommended)

1. **Open Terminal**:
   - Press `Command + Space` to open Spotlight
   - Type `Terminal` and press Enter

2. **Navigate to the project folder**:
   ```bash
   cd /path/to/vericode
   ```
   (Replace `/path/to/vericode` with the actual folder path)

3. **Make the script executable**:
   ```bash
   chmod +x run-vericode.sh
   ```

4. **Run the setup script**:
   ```bash
   ./run-vericode.sh
   ```

#### Method 2: Manual Setup

1. **Open Terminal** (same as above)
2. **Navigate to the project folder** (same as above)
3. **Run the setup**:
   ```bash
   npm install
   npm run db:push
   npm run dev
   ```

### Linux Users

#### Method 1: Using the Automated Script (Recommended)

1. **Open Terminal**:
   - Press `Ctrl + Alt + T`

2. **Navigate to the project folder**:
   ```bash
   cd /path/to/vericode
   ```
   (Replace `/path/to/vericode` with the actual folder path)

3. **Make the script executable**:
   ```bash
   chmod +x run-vericode.sh
   ```

4. **Run the setup script**:
   ```bash
   ./run-vericode.sh
   ```

#### Method 2: Manual Setup

1. **Open Terminal** (same as above)
2. **Navigate to the project folder** (same as above)
3. **Run the setup**:
   ```bash
   npm install
   npm run db:push
   npm run dev
   ```

## 🎯 What Happens During Setup

The setup script will automatically:

1. **Check if Node.js is installed** - If not, it will help you install it
2. **Install all required dependencies** - This might take a few minutes
3. **Set up the database** - Creates the necessary data storage
4. **Start the application** - Launches the VeriCode web server

## 🌐 Using VeriCode

Once the setup is complete:

1. **Open your web browser** (Chrome, Firefox, Safari, Edge, etc.)
2. **Go to** `http://localhost:3000`
3. **You should see the VeriCode homepage**
4. **Try it out!** Paste any tutorial URL and click "Verify"

## 🔧 Common Issues and Solutions

### Issue: "Node.js is not installed"

**Solution:**
1. Go to https://nodejs.org/
2. Click the "LTS" (Long Term Support) download button
3. Run the installer
4. Restart the setup script

### Issue: "Port 3000 is already in use"

**Solution:**
1. Close any other applications that might be using port 3000
2. Or, modify the port in the setup (advanced users only)

### Issue: "Permission denied" (Mac/Linux)

**Solution:**
1. Make sure you're in the correct directory
2. Run: `chmod +x run-vericode.sh`
3. Try again

### Issue: "Command not found: npm"

**Solution:**
1. This means Node.js isn't installed properly
2. Reinstall Node.js from https://nodejs.org/
3. Restart your computer
4. Try again

### Issue: "Database setup failed"

**Solution:**
1. Make sure you have enough disk space
2. Try running the setup again
3. If it still fails, contact support

## 📱 What VeriCode Does

VeriCode helps you check if code snippets from tutorials are still valid:

1. **Paste a URL** from any programming tutorial
2. **Click "Verify"** to start the analysis
3. **Get a report** showing which code snippets work and which don't
4. **See specific errors** for outdated code
5. **Share results** with others

## 🛑 How to Stop VeriCode

When you're done using VeriCode:

1. **Go back to the terminal/command prompt** where it's running
2. **Press `Ctrl + C`** (hold Control and press C)
3. **The application will stop**

## 🔄 How to Start VeriCode Again

After the initial setup, you only need to:

1. **Open terminal/command prompt**
2. **Navigate to the project folder**
3. **Run**: `npm run dev`

## 🆘 Need Help?

If you run into any issues:

1. **Check this guide** for common solutions
2. **Look at the error messages** - they often tell you what's wrong
3. **Try searching online** for the specific error message
4. **Contact support** if you're still stuck

## 🎉 Congratulations!

You've successfully set up VeriCode! Now you can easily check if tutorial code snippets are still valid with the latest dependencies.

Happy coding! 🚀