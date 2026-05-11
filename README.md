# df-pms-opera-adapter [CRUX-MK]

**15. Foundation-DF (Welle-36 HeyLou-Mosaic-Layer): Oracle Opera PMS-Adapter (Premium).**

Mosaic-Adapter fuer Oracle Opera PMS (Premium-Segment, Chain-Hotels).
ENV-Var-gated Sandbox-Default-Mode, Mock-Fallback Pflicht, K17-PAV, HMAC-SHA256.

## Architektur

- `OperaConnector` (OXI-API Wrapper - Opera Xchange Interface)
- `OperaAuth` (Token-Service-Pattern: OAuth2 Client-Credentials)
- `OperaAdapterOrchestrator` (LaunchAgent-Entry-Point)
- `AuditLogger` (HMAC-SHA256 JSONL)

## Opera-Spezifika

Opera verwendet **Token-Service-Pattern**:
- OAuth2 Client-Credentials Flow gegen Token-Service-URL
- Bearer-Token fuer OXI-API-Calls
- Hotel-ID per X-HotelId-Header
- Token-Refresh ~1h Lifetime

## ENV-Vars

| Var | Default | Pflicht | Beschreibung |
|-----|---------|---------|--------------|
| `DF_PMS_OPERA_REAL_ENABLED` | `false` | nein | Aktiviert Real-API |
| `OPERA_CLIENT_ID` | `""` | bei Real | OAuth2 Client-ID |
| `OPERA_CLIENT_SECRET` | `""` | bei Real | OAuth2 Client-Secret |
| `OPERA_TOKEN_URL` | `""` | bei Real | Token-Service-Endpoint |
| `OPERA_HOTEL_ID` | `""` | bei Real | Property-ID (OXI) |
| `DF_PMS_OPERA_PHRONESIS_TICKET` | `""` | bei Real-Booking | K17-PAV |
| `DF_PMS_OPERA_HMAC_SECRET` | `""` | nein | Audit-Secret |

## Welle-36 Status

- Tier: SKELETON-CONDITIONAL
- LaunchAgent-Cadence: 7200s

## Install

```bash
cp scripts/com.kemmer.df-pms-opera-adapter.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.kemmer.df-pms-opera-adapter.plist
```

## Tests

```bash
python3 -m pytest tests/ -v
```

[CRUX-MK]
