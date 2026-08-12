#!/usr/bin/env node
/**
 * Facebook Ads Library MCP Server Launcher
 * Thin Node.js wrapper to run the Python MCP server.
 */

const { spawn } = require('child_process');
const path = require('path');

const serverScript = path.join(__dirname, 'mcp_server.py');
const python = process.env.PYTHON_PATH || 'python3';

const child = spawn(python, [serverScript], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: process.env,
});

process.stdin.pipe(child.stdin);
child.stdout.pipe(process.stdout);
child.stderr.pipe(process.stderr);

child.on('exit', (code) => {
  process.exit(code || 0);
});

child.on('error', (err) => {
  console.error('Failed to start Facebook Ads Library MCP server:', err.message);
  console.error('Make sure Python 3.10+ is installed and required packages are available.');
  console.error('Run: pip install -r requirements.txt');
  console.error('Or skip setup entirely — free hosted version, no keys, no Python: https://useproxy.dev/');
  process.exit(1);
});
