# Privacy Policy for TikTok Bulk Downloader Extension

**Last Updated:** January 12, 2026

## Overview
TikTok Bulk Downloader is a browser extension that helps users collect and download TikTok videos. We are committed to protecting your privacy.

## Data Collection
This extension **does not collect, store, or transmit any personal information** to external servers.

### What Data is Stored Locally
The extension stores the following data **locally on your device only** using Chrome's storage API:
- **Video URLs**: URLs of TikTok videos you collect while scrolling
- **Extension Settings**: Your preferences for scroll interval and backend API URL
- **Badge Count**: The number of URLs collected (displayed on the extension icon)

All data is stored **locally in your browser** and is never sent to us or any third-party services.

## Data Transmission
The extension communicates **only** with:
1. **TikTok.com**: To collect video URLs from pages you visit
2. **Your Local Backend Server** (default: http://localhost:3000): To send video URLs for download

The extension **does not** communicate with:
- Our servers (we don't have any)
- Third-party analytics services
- Advertising networks
- Any external data collection services

## Permissions Explained
The extension requests the following permissions:

- **activeTab**: To interact with the current TikTok page you're viewing
- **storage**: To save your settings and collected URLs locally in your browser
- **scripting**: To inject auto-scroll functionality into TikTok pages
- **host_permissions (tiktok.com)**: To collect video URLs from TikTok pages you visit
- **host_permissions (localhost)**: To communicate with your local download backend

## Data Deletion
You can delete all data stored by the extension at any time:
1. Click the extension icon
2. Click "Clear URLs" to remove collected URLs
3. Or uninstall the extension to remove all stored data

## Changes to This Policy
We may update this privacy policy from time to time. Changes will be reflected in the extension's GitHub repository.

## Contact
If you have questions about this privacy policy, please open an issue on our GitHub repository:
https://github.com/Joombah/Tiktok-Bulk-Downloader

## Open Source
This extension is open source. You can review the complete source code at:
https://github.com/Joombah/Tiktok-Bulk-Downloader
