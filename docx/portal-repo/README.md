# Portal repo setup (Android-MCP-Portal)

`android_mcp/bootstrap.py` downloads a **pinned** APK from
`https://github.com/HadyAhmed00/Android-MCP-Portal/releases/download/<TAG>/portal.apk`.
That release does not exist yet — these are the files to add to the Portal repo to produce it.

## 1. Add the release workflow

Copy `release.yml` here to `.github/workflows/release.yml` in the Portal repo.

Notes:
- `app/build.gradle.kts` reads `versionName`/`versionCode` via
  `project.findProperty(...) as String`, which throws when the property is missing — the
  workflow always passes both `-PversionName` and `-PversionCode`.
- `versionCode` uses `github.run_number` so it is monotonic across releases.
- Asset names `portal.apk` and `portal.apk.sha256` are the contract with bootstrap.py.
  Renaming them breaks auto-install.

## 2. Add release signing

`assembleRelease` without a signing config produces `app-release-unsigned.apk`, which
`adb install` rejects. Add to `app/build.gradle.kts`:

```kotlin
android {
    signingConfigs {
        create("release") {
            val keystore = System.getenv("KEYSTORE_PATH")
            if (keystore != null) {
                storeFile = file(keystore)
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
            }
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

Generate the keystore once:

```bash
keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias portal
base64 -w0 release.jks          # paste into the KEYSTORE_B64 secret
```

**Back the keystore up somewhere off GitHub.** Losing it means a different signature, and
every existing user's in-place upgrade fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`
(bootstrap recovers by uninstalling first, but that wipes the app's state).

Repo secrets needed: `KEYSTORE_B64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`.
Add `*.jks` to `.gitignore`.

## 3. Cut the first release

```bash
git tag v0.5.5 && git push origin v0.5.5
```

## 4. Pin it here

Copy the digest from the release's `portal.apk.sha256` into `android_mcp/bootstrap.py`:

```python
PORTAL_APK_TAG = "v0.5.5"
PORTAL_APK_SHA256 = "<digest>"
```

Until that is done, `PORTAL_APK_SHA256` is `None`: bootstrap skips checksum verification and
auto-install 404s, falling back to manual instructions and the UIAutomator2 backend.
