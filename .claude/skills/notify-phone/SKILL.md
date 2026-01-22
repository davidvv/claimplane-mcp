---
name: notify-phone
description: Send direct messages to David via RocketChat for important events
license: MIT
compatibility: opencode
metadata:
  author: David
  category: notifications
---

# Phone Notification Skill

Send direct messages to David via RocketChat when important events occur, tasks complete, or errors happen.

## What I do

- Send direct messages to David through RocketChat
- Notify about task completions, errors, and important events
- Use the existing RocketChat infrastructure at `/home/david/rocket-connection`
- Deliver notifications that David sees on all his devices (desktop, mobile, etc.)

## When to use me

Send notifications when:

- ✅ Long-running tasks complete (analysis, builds, deployments)
- 🔴 Critical errors or failures occur
- 📋 Important tickets are created or updated  
- ⚠️ Issues require immediate attention
- 📞 User explicitly requests to be notified

## How to send notifications

Use the RocketChatClient located at `/home/david/rocket-connection/rocketChatClient.js`.

### Step 1: Require the client

```javascript
const RocketChatClient = require('/home/david/rocket-connection/rocketChatClient');
```

### Step 2: Initialize and login

```javascript
const client = new RocketChatClient();
await client.login();
```

The client automatically reads credentials from `/home/david/rocket-connection/.env`.

### Step 3: Send a direct message

To send a direct message to David, use his username `@david`:

```javascript
await client.sendMessage('@david', 'Your message here');
```

### Complete example

```javascript
const RocketChatClient = require('/home/david/rocket-connection/rocketChatClient');

(async () => {
  const client = new RocketChatClient();
  await client.login();
  
  await client.sendMessage(
    '@david',
    '✅ Bug analysis complete! Created OpenProject ticket #237 for flight API data source issue.'
  );
})();
```

## Using with Bash tool

You can use Node.js one-liner with the Bash tool:

```bash
cd /home/david/rocket-connection && node -e "
const RocketChatClient = require('./rocketChatClient');
(async () => {
  const client = new RocketChatClient();
  await client.login();
  await client.sendMessage('@david', 'Your notification message here');
})();
"
```

## Example notifications

### Task completion
```javascript
await client.sendMessage(
  '@david',
  '✅ Analysis Complete\n\nCreated OpenProject ticket #237: Flight API data source issue\n\nThe agent searched the codebase and identified 3 API integration points that need updating.'
);
```

### Error notification
```javascript
await client.sendMessage(
  '@david',
  '❌ Analysis Failed\n\nFailed to create ticket: OpenProject API timeout after 30s\n\nRetrying in 60 seconds...'
);
```

### Progress update
```javascript
await client.sendMessage(
  '@david',
  '⏳ Analysis in Progress\n\nProcessing bug report about flight data API\nSearching codebase... (2/5 steps complete)'
);
```

### User-requested notification
```javascript
await client.sendMessage(
  '@david',
  '🔔 Requested Task Complete\n\nYour analysis task has finished successfully.\n\nTicket #238 created with full root cause analysis.'
);
```

## Best practices

1. **Keep messages clear**: Include key details (ticket numbers, error messages)
2. **Use emojis**: ✅ ❌ ⚠️ 🔔 ⏳ help scan messages quickly
3. **Be concise**: Get to the point in the first line
4. **Add context**: Include enough info so David knows what happened
5. **Don't spam**: Only for genuinely important events

## Message format tips

Structure notifications like this:

```
[Emoji] [Short Status Title]

[Main message body with details]

[Optional: Next steps or additional info]
```

Example:
```
✅ Bug Analysis Complete

Created ticket #237: Flight API requires backup data source

Analyzed 15 files, found 3 API integration points in:
- app/services/flightData.js:45
- app/api/flights.js:120
- app/models/Flight.js:78

Next: Review and prioritize the ticket.
```

## Technical details

- **Client location**: `/home/david/rocket-connection/rocketChatClient.js`
- **Environment file**: `/home/david/rocket-connection/.env` (contains credentials)
- **RocketChat URL**: `https://rocket.dvvcloud.work`
- **David's username**: `david`
- **Direct message format**: Use `@david` as the channel/recipient

## Important notes

- The RocketChatClient handles authentication automatically
- Messages go through RocketChat's notification system
- David receives notifications on all connected devices
- No external services required - everything is self-hosted
- Dependencies (axios, dotenv) are already installed in `/home/david/rocket-connection`

## Quick test

Test the notification system:

```bash
cd /home/david/rocket-connection && node -e "
const RocketChatClient = require('./rocketChatClient');
(async () => {
  const client = new RocketChatClient();
  await client.login();
  await client.sendMessage('@david', '🤖 Test notification from OpenCode notify-phone skill!');
})();
"
```
