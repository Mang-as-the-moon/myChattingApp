# Partner App — Backend (FastAPI)

## What's implemented and working (tested end-to-end)
- Email/password auth + Google Sign-In verification (JWT issued either way)
- Secret-token pairing: one user generates a token, shares it out-of-band, the
  other enters it to link — enforced 1-to-1
- Realtime WebSocket (`/ws`) for: presence, chat messages, HP updates, and
  pure signaling relay for calls / walkie-talkie / private-media (server never
  inspects that signaling payload's content)
- REST endpoints for profile, partner view, message history, media upload
- HP ("responsiveness") tracking: resets to 10 when you message your partner,
  decays by 1 every N hours of silence (configurable per user), background job
  via APScheduler, pushed live over the socket

## Setup
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SECRET_KEY and GOOGLE_CLIENT_ID
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API docs: http://localhost:8000/docs

## Google Sign-In setup
1. Create an OAuth 2.0 Client ID (Web application type, even for mobile — you
   need this for backend `id_token` verification) in Google Cloud Console.
2. Put that client ID in `.env` as `GOOGLE_CLIENT_ID`.
3. Also create Android/iOS OAuth client IDs for the `google_sign_in` Flutter
   package itself (see Flutter setup below).

## What you still need to do before production
- Swap SQLite for Postgres (`DATABASE_URL`) and add Alembic migrations
- Swap local `/media` disk storage for S3/GCS with signed URLs
- Add a TURN server (e.g. coturn) — STUN alone won't work on many mobile networks
- Serve over HTTPS/WSS (required for microphone/camera access on real devices
  and for Google Sign-In in production)
- Rate-limit `/auth/*` and `/pairing/generate-token`
- The chat message websocket path currently has no message-content encryption
  at rest in the DB — for real end-to-end encrypted text, you'd add a
  Signal-protocol-style key exchange per partnership (out of scope for this
  scaffold, flagging so it's a conscious decision, not an oversight)
