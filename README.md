# XIV Auto OTP
Simple program to store your XIV OTP key in Windows Credentials, automatically sending it to [XIVLauncher](https://github.com/goatcorp/FFXIVQuickLauncher/).

## Is this secure?
* This program stores your OTP secret in the Windows Credentials. While this is slightly more secure than [storing it in plain text][kensykora], it is not secure as using [proper encrypted storage][1pass], or [another device][mobile]; any user program could still access the secret from Windows Credentials if they knew to look.
* This programs the entire "two factor" from 2FA. If a user had access to your computer, they could login as you.

## Why use it?
* This program offers more protection then no OTP at all, giving many of the bonuses of securing your account with OTP.
* This program, unlike many others, automatically detect's XIVLauncher's OTP dialog, generating and sending a code on your behalf.

## Getting Started
### Program installatation
1. Download a copy of this program and save it somewhere you won't lose it.
2. Add the program to start with windows, if you prefer.
3. Launch the program, right click the tray icon, and select "Configure OTP Secret".

### Adding Software Authenticators
1. Start the web process of adding a Software Authenticator to your account.
2. Add the provided QR code to your preferred mobile authenticator, such as Authy or Google Authenticator, just in case.
3. Decode the QR code using a QR scanner, such as [this one](https://nimiq.github.io/qr-scanner/demo/) or the one built into [ShareX](https://getsharex.com/).
4. Copy the entire `otpauth://...` URL from the QR code into the "Configure OTP Secret" dialog and click OK.
5. Confirm both authenticators match by selecting "Generate OTP Code" from the program's tray icon menu.

### Configure XIVLauncher
1. In the XIVLauncher settings dialog, ensure  "Enable XL Authenticator app/OTP macro support" is enabled.
2. Enter your username/pass, and tick "Log in Automatically" and "Use One-Time-Passwords"
3. As long as the program is running, the OTP dialog should be automatically detected, logging you in.

## See Also
* [XIVLauncher's XL Authenticator][mobile]
* [XIVLauncher's 1Password CLI Script][1pass]
* [Kensykoras' Automatic OTP Entry][kensykora]

[mobile]: https://goatcorp.github.io/faq/mobile_otp
[1pass]: https://github.com/goatcorp/FFXIVQuickLauncher/tree/master/misc/1password-cli-otp
[kensykora]: https://gist.github.com/kensykora/b220573b4230d7622c5a23a497c75fd3
