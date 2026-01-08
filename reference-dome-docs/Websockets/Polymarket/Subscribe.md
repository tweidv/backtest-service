# Subscribe

> Subscribe to real-time order data via WebSocket

## Overview

The `subscribe` action allows you to receive real-time order updates from Polymarket. You can filter orders by different criteria to receive only the data you need.

## Subscription Message Format

All subscription messages follow this base format:

```json  theme={null}
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        // Filter options (see below)
    }
}
```

**Required Parameters:**

* `action`: Must be `"subscribe"`
* `platform`: Must be `"polymarket"`
* `version`: Currently `1`
* `type`: Must be `"orders"`
* `filters`: Object containing filter criteria (see filter types below)

## Tier Limits

Subscription limits vary by tier:

| Tier           | Subscriptions | Wallets per Subscription |
| -------------- | ------------- | ------------------------ |
| **Free**       | 2             | 5                        |
| **Dev**        | 500           | 500                      |
| **Enterprise** | Custom        | Custom                   |

## Filter Types

You can subscribe to orders using one of three filter criteria:

<Tabs>
  <Tab title="Users">
    ### Filter by Wallet Addresses

    Track orders from specific wallet addresses or use a wildcard to receive all trades.

    **Specific Wallet Addresses:**

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

    You'll receive order events when any of the specified wallet addresses execute trades.

    **Wildcard - All Trades:**

    <Warning>
      The wildcard option (`"*"`) is only available on **Dev tier** and above due to high egress costs. Free tier users cannot use this feature.
    </Warning>

    To receive all trades across Polymarket, use a wildcard:

    ```json  theme={null}
    {
        "action": "subscribe",
        "platform": "polymarket",
        "version": 1,
        "type": "orders",
        "filters": {
            "users": ["*"]
        }
    }
    ```
  </Tab>

  <Tab title="Condition IDs">
    ### Filter by Condition IDs

    Track orders for specific market conditions. This is useful when you want to monitor specific outcomes or tokens within markets.

    **Single Condition ID:**

    ```json  theme={null}
    {
        "action": "subscribe",
        "platform": "polymarket",
        "version": 1,
        "type": "orders",
        "filters": {
            "condition_ids": [
                "0x17815081230e3b9c78b098162c33b1ffa68c4ec29c123d3d14989599e0c2e113"
            ]
        }
    }
    ```

    **Multiple Condition IDs:**

    You can track multiple conditions in a single subscription:

    ```json  theme={null}
    {
        "action": "subscribe",
        "platform": "polymarket",
        "version": 1,
        "type": "orders",
        "filters": {
            "condition_ids": [
                "0x17815081230e3b9c78b098162c33b1ffa68c4ec29c123d3d14989599e0c2e113",
                "0x592b8a416cbe36aa7bb40df85a61685ebd54ebbd2d55842f1bb398cae4f40dfc"
            ]
        }
    }
    ```

    You'll receive order events when trades occur for any of the specified condition IDs.

    **Use Cases:**

    * Monitor specific tokens or outcomes within a market
    * Track trading activity for particular conditions
    * Build analytics dashboards for specific market conditions
    * Create alerts for trades on specific conditions
  </Tab>

  <Tab title="Market Slugs">
    ### Filter by Market Slugs

    Track all trades within specific markets. Market slugs are unique identifiers for each market on Polymarket.

    **Single Market:**

    ```json  theme={null}
    {
        "action": "subscribe",
        "platform": "polymarket",
        "version": 1,
        "type": "orders",
        "filters": {
            "market_slugs": [
                "btc-updown-15m-1762755300"
            ]
        }
    }
    ```

    **Multiple Markets:**

    You can track multiple markets in a single subscription:

    ```json  theme={null}
    {
        "action": "subscribe",
        "platform": "polymarket",
        "version": 1,
        "type": "orders",
        "filters": {
            "market_slugs": [
                "btc-updown-15m-1762755300",
                "eth-price-2024-12-31"
            ]
        }
    }
    ```

    You'll receive order events when trades occur in any of the specified markets.

    **Finding Market Slugs:**

    * In the URL of Polymarket market pages
    * From the [Markets API endpoint](/api-reference/endpoint/get-markets) response
    * In order event data from other subscriptions

    **Use Cases:**

    * Monitor all trading activity within specific markets
    * Track market-wide order flow
    * Build market-specific analytics
    * Create alerts for trades in particular markets
  </Tab>
</Tabs>

## Subscription Acknowledgment

After sending a subscription message, you'll receive an acknowledgment from the server:

```json  theme={null}
{
    "type": "ack",
    "subscription_id": "sub_gq5c3resmrq"
}
```

**Important:** Save the `subscription_id` - you'll need it to [unsubscribe](/websockets/unsubscribe) or [update](/websockets/update) your subscription later.

## Receiving Order Events

When orders matching your subscription filters are executed, you'll receive event messages in real-time:

```json  theme={null}
{
    "type": "event",
    "subscription_id": "sub_gq5c3resmrq",
    "data": {
        "token_id": "80311845198420617303393545005967792170450763818026370381995461841892638500659",
        "token_label": "No",
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

## Next Steps

* [Unsubscribe from a subscription](/websockets/unsubscribe)
* [Update an existing subscription](/websockets/update)
* Learn about [SDKs](/websockets/polymarket-websockets-sdk) for easier integration


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt