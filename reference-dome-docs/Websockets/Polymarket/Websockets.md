# Websockets

> Real-time Polymarket order data via WebSocket

## Overview

Dome API's WebSocket server provides real-time order information from Polymarket. The server is designed to be the fastest WebSocket server available, making it perfect for copy-trading applications where speed is critical.

## Connection

### Server Endpoint

Connect to the WebSocket server at:

```
wss://ws.domeapi.io/<YOUR_API_KEY>
```

### Authentication

Authenticate by including your API key in the connection URL. The API key acts as your authentication token.

**Example using wscat:**

```bash  theme={null}
wscat -c wss://ws.domeapi.io/<YOUR_API_KEY>
```

## Subscribing to Channels

To receive real-time order updates, send a subscription message after connecting.

### Subscription Message Format

```json  theme={null}
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": [
            "0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d",
            "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b"
        ]
    }
}
```

**Parameters:**

* `action`: Must be `"subscribe"`
* `platform`: Must be `"polymarket"`
* `version`: Currently `1`
* `type`: Must be `"orders"`
* `filters.users`: Array of wallet addresses to track

### Subscription Acknowledgment

After sending a subscription message, you'll receive an acknowledgment from the server:

```json  theme={null}
{
    "type": "ack",
    "subscription_id": "sub_gq5c3resmrq"
}
```

Save the `subscription_id` - you'll need it to unsubscribe later.

## Receiving Order Events

When orders matching your subscription filters are executed, you'll receive event messages in real-time.

### Event Message Format

```json  theme={null}
{
    "type": "event",
    "subscription_id": "sub_gq5c3resmrq",
    "data": {
        "token_id": "80311845198420617303393545005967792170450763818026370381995461841892638500659",
        "token_label": "No"
        "side": "BUY",
        "market_slug": "btc-updown-15m-1762479900",
        "condition_id": "0x5853a47d2d7d97571684c458e2ac28f7f232e12d5490a96cc5b302bd8b4c61bd",
        "shares": 9000000,
        "shares_normalized": 9,
        "price": 0.56,
        "tx_hash": "0xaccc1246d7bc1c95ad44789a6e7ecbc7819dd308632aa0190fedf9673c034077",
        "title": "Bitcoin Up or Down - November 6, 8:45PM-9:00PM ET",
        "timestamp": 1762480391,
        "order_hash": "0xc2b8ee7c9dced1374ac8e2307c65e5204283781c98e1640e28d25d6cc14a0e13",
        "user": "0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d",
        "taker": "0x8d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e"
    }
}
```

**Event Fields:**

* `type`: Always `"event"` for order events
* `subscription_id`: The ID of the subscription that triggered this event
* `data`: Order information matching the format of our orders API

Orders are sent when they match any wallet address in your subscription's `filters.users` array.

## Unsubscribing

To stop receiving updates for a subscription, send an unsubscribe message:

```json  theme={null}
{
    "action": "unsubscribe",
    "version": 1,
    "subscription_id": "sub_gq5c3resmrq"
}
```

Use the `subscription_id` from the acknowledgment you received when subscribing.

Alternatively, you can simply disconnect from the WebSocket to stop all subscriptions.

## Important Notes

### Reconnection Behavior

If you get disconnected from the server (e.g., due to a server restart), you'll need to re-subscribe using the exact same subscription payload you initially sent. The server does not automatically restore subscriptions after reconnection.

### Data Format

Order event data follows the same format as Dome's [orders API endpoint](https://docs.domeapi.io/api-reference/endpoint/get-trade-history), ensuring consistency across both interfaces.


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt