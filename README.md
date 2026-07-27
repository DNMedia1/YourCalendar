# MSBrowser Alpha

MSBrowser Alpha is a minimal Expo React Native app for iOS and Android. It can receive a link, prefill the mandatory value field, and run separate Encrypt and Decrypt button workflows.

The encryption and decryption mechanisms are intentionally not implemented. The framework exposes the workflow methods and a replaceable transform engine so a real mechanism can be added later without changing the UI.

## Requirements

- Node.js 22.13 or newer
- npm
- Expo-compatible iOS or Android build environment

## Install

```powershell
npm install
```

## Run

```powershell
npm start
npm run start:lan
npm run android
npm run ios
```

`npm run ios` requires macOS and Xcode. On Windows, use Android or an Expo development build.
`npm run start:lan` starts the Metro server on port 8083 for devices on the same network.

## Test

```powershell
npm test
```

The integration test verifies startup link resolution and both alpha workflows.

## Link Handling

Android standalone builds register HTTP and HTTPS intent filters, so Android can offer MSBrowser Alpha as a link target.

iOS supports the `msbrowser://` custom scheme in this alpha. Opening arbitrary HTTP/HTTPS links from every iOS app requires Apple platform capabilities such as Universal Links for owned domains or browser-specific entitlements. Those cannot be completed by code alone without the required Apple account, domain, and entitlement setup.

Custom scheme example:

```text
msbrowser://open?url=https%3A%2F%2Fexample.com
```

## Project Structure

- `src/core` contains link resolution, validation, logging, and workflow classes.
- `src/presentation` contains mobile UI components, hooks, and screens.
- `tests/unit` contains focused unit tests.
- `tests/integration` verifies the alpha workflow end to end at the core layer.

## API Keys

No API keys are required for this alpha because the current scope has no external API calls.
