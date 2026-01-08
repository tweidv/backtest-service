# Unsubscribe

> Unsubscribe from WebSocket channels to stop receiving updates

## Overview

The `unsubscribe` action allows you to stop receiving updates for a specific subscription without disconnecting from the WebSocket entirely. This is useful when you want to manage multiple subscriptions independently.

## Unsubscribe Message Format

```json  theme={null}
{
    "action": "unsubscribe",
    "version": 1,
    "subscription_id": "sub_wjhhq8dny2"
}
```

**Required Parameters:**

* `action`: Must be `"unsubscribe"`
* `version`: Currently `1`
* `subscription_id`: The subscription ID you received when you subscribed (e.g., `"sub_wjhhq8dny2"`)

## Example

To unsubscribe from a subscription:

```json  theme={null}
{
    "action": "unsubscribe",
    "version": 1,
    "subscription_id": "sub_wjhhq8dny2"
}
```

After sending this message, you will stop receiving order events for that subscription. Other active subscriptions will continue to work normally.

## Getting the Subscription ID

When you [subscribe](/websockets/subscribe), you receive an acknowledgment with a `subscription_id`:

```json  theme={null}
{
    "type": "ack",
    "subscription_id": "sub_gq5c3resmrq"
}
```

Save this ID to unsubscribe later.

## Alternative: Disconnect

If you want to stop all subscriptions at once, you can simply disconnect from the WebSocket. All active subscriptions will be automatically cancelled when you disconnect.

## Managing Multiple Subscriptions

You can maintain multiple active subscriptions simultaneously. Unsubscribing from one does not affect others:

```json  theme={null}
// Subscribe to users
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
// Response: { "type": "ack", "subscription_id": "sub_abc123" }

// Subscribe to condition IDs
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "condition_ids": ["0x17815081230e3b9c78b098162c33b1ffa68c4ec29c123d3d14989599e0c2e113"]
    }
}
// Response: { "type": "ack", "subscription_id": "sub_xyz789" }

// Later, unsubscribe from just the first one
{
    "action": "unsubscribe",
    "version": 1,
    "subscription_id": "sub_abc123"
}
// sub_xyz789 will continue to receive events
```

## Related

* [Subscribe to Channels](/websockets/subscribe)
* [Update Subscription](/websockets/update)


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt