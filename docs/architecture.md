# Architecture

## Core

The core layer is independent from React Native:

- `IncomingLinkResolver` resolves direct HTTP/HTTPS links and `msbrowser://` links.
- `ValueValidator` enforces the mandatory value rule.
- `CryptoWorkflow` exposes `encryptValue` and `decryptValue`.
- `PlaceholderTransformEngine` is the replaceable alpha implementation.
- `LogHandler` writes structured logs with serialized stack traces.

## Presentation

The presentation layer keeps the UI minimal:

- `useAlphaBrowserController` owns screen state, input state, notifications, and button handlers.
- `AlphaBrowserScreen` renders the value input, action buttons, and result view.
- `ActionButton` and `NotificationBanner` keep repeated UI behavior isolated.

## Replacing the Placeholder Engine

Create a class with this shape:

```js
export class RealTransformEngine {
  async encrypt(value) {
    return "real encrypted value";
  }

  async decrypt(value) {
    return "real decrypted value";
  }
}
```

Inject it into `CryptoWorkflow`:

```js
new CryptoWorkflow({ transformEngine: new RealTransformEngine() });
```
