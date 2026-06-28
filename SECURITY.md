# Security Policy

## Supported Status

`MT5 Robot Lab` is in bootstrap status. It is not approved for real trading or
live account automation.

## Sensitive Data Boundary

Do not commit:

- broker login;
- broker password;
- account number;
- broker server;
- `.env`;
- `.set`;
- `.ex5`;
- raw MT5 reports;
- private logs;
- MT5 history files;
- local private configuration.

## Reporting

Open a private security report or contact the maintainer before publishing any
finding involving credential exposure, account leakage or unsafe live-trading
behavior.
