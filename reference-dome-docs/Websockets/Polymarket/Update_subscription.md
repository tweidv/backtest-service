# Update Subscription

> Update an existing subscription's filters without creating a new subscription

## Overview

The `update` action allows you to modify the filters of an existing subscription without creating a new one. This is more efficient than unsubscribing and re-subscribing, as it maintains the same subscription ID.

## Update Message Format

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
```

**Required Parameters:**

* `action`: Must be `"update"`
* `subscription_id`: The ID of the subscription you want to update
* `platform`: Must be `"polymarket"`
* `version`: Currently `1`
* `type`: Must be `"orders"`
* `filters`: New filter configuration (same format as subscribe)

## Example

Update a subscription to change its filters:

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
```

After updating, the subscription will immediately start using the new filters. You'll continue to receive events, but they'll match the updated criteria.

## Use Cases

* Change which users you're tracking without losing your subscription
* Switch from tracking users to tracking condition IDs
* Update market slugs or condition IDs as markets change
* Adjust filters based on runtime conditions

## Filter Types

You can update a subscription to use any of the supported filter types:

### Update to User Filters

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
```

### Update to Condition ID Filters

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "condition_ids": ["0x17815081230e3b9c78b098162c33b1ffa68c4ec29c123d3d14989599e0c2e113"]
    }
}
```

### Update to Market Slug Filters

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "market_slugs": ["btc-updown-15m-1762755300"]
    }
}
```

## Complete Example

Here's a complete example showing the full flow of subscribing, receiving events, and then updating the subscription:

### Step 1: Initial Subscription

```json  theme={null}
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b"]
    }
}
```

**Server Response:**

```json  theme={null}
{
    "type": "ack",
    "subscription_id": "sub_k7f5hgr7wy"
}
```

### Step 2: Receiving Events (Before Update)

You'll receive order events for the subscribed user:

```json  theme={null}
{
    "type": "event",
    "subscription_id": "sub_k7f5hgr7wy",
    "data": {
        "token_id": "80311845198420617303393545005967792170450763818026370381995461841892638500659",
        "side": "BUY",
        "market_slug": "btc-updown-15m-1762479900",
        "condition_id": "0x5853a47d2d7d97571684c458e2ac28f7f232e12d5490a96cc5b302bd8b4c61bd",
        "shares": 9000000,
        "shares_normalized": 9,
        "price": 0.56,
        "user": "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b",
        "timestamp": 1762480391
    }
}
```

### Step 3: Update Subscription

Now update the subscription to track a different user:

```json  theme={null}
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
```

**Note:** The subscription ID remains the same: `sub_k7f5hgr7wy`

### Step 4: Receiving Events (After Update)

After the update, you'll now receive events for the new user:

```json  theme={null}
{
    "type": "event",
    "subscription_id": "sub_k7f5hgr7wy",
    "data": {
        "token_id": "57564352641769637293436658960633624379577489846300950628596680893489126052038",
        "side": "BUY",
        "market_slug": "btc-updown-15m-1762755300",
        "condition_id": "0x592b8a416cbe36aa7bb40df85a61685ebd54ebbd2d55842f1bb398cae4f40dfc",
        "shares": 5000000,
        "shares_normalized": 5,
        "price": 0.54,
        "user": "0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d",
        "timestamp": 1762755335
    }
}
```

Notice that:

* The `subscription_id` is still `sub_k7f5hgr7wy` (same as before)
* The `user` field in the event data now matches the updated filter
* You'll no longer receive events for the previous user (`0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b`)

### Example: Changing Filter Types

You can also change the filter type entirely. For example, switch from user filters to condition ID filters:

```json  theme={null}
// Update from user filter to condition ID filter
{
    "action": "update",
    "subscription_id": "sub_k7f5hgr7wy",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "condition_ids": ["0x17815081230e3b9c78b098162c33b1ffa68c4ec29c123d3d14989599e0c2e113"]
    }
}
```

After this update, you'll receive events for orders matching the specified condition ID, regardless of which user made the trade.

## Benefits

* **Efficiency**: No need to unsubscribe and re-subscribe
* **Consistency**: Maintains the same subscription ID
* **Seamless**: No interruption in receiving events (after the update takes effect)
* **Flexibility**: Change filter types or criteria on the fly

## Related

* [Subscribe to Channels](/websockets/subscribe)
* [Unsubscribe from Channels](/websockets/unsubscribe)
* [Filter by Users](/websockets/subscribe-users)
* [Filter by Condition IDs](/websockets/subscribe-condition-ids)
* [Filter by Market Slugs](/websockets/subscribe-market-slugs)


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt