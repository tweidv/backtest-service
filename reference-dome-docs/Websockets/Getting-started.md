# Websockets

> Get started with Dome Websockets

## What is Dome API?

Dome API provides comprehensive access to prediction market data across multiple platforms including Polymarket and Kalshi. Get real-time market prices, historical candlestick data, wallet analytics, order tracking, and cross-platform market matching. Get started with a free API key [here](https://dashboard.domeapi.io/).

## What are Websockets?

Dome API provides real-time data streaming through WebSocket connections, allowing you to receive live updates for market prices, trades, orderbook changes, and more without constantly polling the REST API.

## Tier Limits

Subscription and wallet tracking limits vary by tier:

| Tier           | Subscriptions | Wallets per Subscription |
| -------------- | ------------- | ------------------------ |
| **Free**       | 2             | 5                        |
| **Dev**        | 500           | 500                      |
| **Enterprise** | Custom        | Custom                   |

## Quick Start

### 1. Get Your API Key

[Sign up](https://dashboard.domeapi.io/) for an account and get your API Key from the dashboard.
<img src="https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=fa7ef3bac84721e7d4366ad8207f8068" alt="Hero Light Pn" data-og-width="2064" width="2064" data-og-height="1104" height="1104" data-path="images/hero-light.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=280&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=6916e9095018482f82cc49f0d97a6678 280w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=560&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=d7d6008b151a1bb7bb840ba37adb4758 560w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=840&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=831ff585efef02cc968263af252ced44 840w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=1100&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=48487615fcbcb8744494547ccbdd6e27 1100w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=1650&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=3ed53781014805fa0125c20e9684de3e 1650w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=2500&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=52761c1fee79e3a6020f443be795512a 2500w" />

### 2. Connect to the WebSocket

Connect to the Dome API WebSocket endpoint to start receiving real-time data. Below is an example using `wscat`

`wscat -c wss://ws.domeapi.io/<API_KEY_GOES_HERE>`

### 3. WebSocket Actions

Dome API WebSockets support three main actions to manage your real-time data streams:

#### Subscribe

Subscribe to channels to start receiving real-time updates. You can filter orders by:

* **[User addresses](/websockets/subscribe-users)** - Track trades from specific wallets or use a wildcard for all trades (Dev tier only)
* **[Condition IDs](/websockets/subscribe-condition-ids)** - Track trades for specific market conditions
* **[Market slugs](/websockets/subscribe-market-slugs)** - Track all trades within specific markets

```json  theme={null}
{
    "action": "subscribe",
    "platform": "polymarket",
    "version": 1,
    "type": "orders",
    "filters": {
        "users": ["0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"]
    }
}
```

[Learn more about subscribing →](/websockets/subscribe)

#### Update

Update an existing subscription's filters without creating a new subscription:

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

[Learn more about updating subscriptions →](/websockets/update)

#### Unsubscribe

Stop receiving updates from a subscription:

```json  theme={null}
{
    "action": "unsubscribe",
    "version": 1,
    "subscription_id": "sub_wjhhq8dny2"
}
```

[Learn more about unsubscribing →](/websockets/unsubscribe)

## Need Help?

* Email: [Support Email](mailto:support@domeapi.com)
* Join our [Discord](https://discord.gg/fKAbjNAbkt) community
* Check out our SDKs: [TypeScript](https://github.com/kurushdubash/dome-sdk-ts) | [Python](https://github.com/kurushdubash/dome-sdk-py)


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt